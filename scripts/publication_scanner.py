"""
publication_scanner.py — Pre-publication safety scanner for the Leo Life vault.

Scans files and directories for content that must not appear in GitHub exports:
  - Token-looking strings and common provider secret patterns
  - Absolute local paths (e.g. /home/youruser/)
  - audience: private/internal frontmatter in public docs
  - References to raw/, inbox/, private folders
  - Slack workspace/channel IDs or real token examples
  - Personal names and operational details

Usage
-----
# Scan a single file
python3 scripts/publication_scanner.py path/to/file.md

# Scan a directory
python3 scripts/publication_scanner.py exports/github-preview/

# Scan with an allowlist file
python3 scripts/publication_scanner.py exports/ --allowlist scripts/scanner_allowlist.txt

# Scan and exit non-zero if any findings
python3 scripts/publication_scanner.py exports/ --strict

The scanner is designed to run as a gate before any GitHub push.  Run it from
the vault root.  Exit code 0 = clean; 1 = findings; 2 = error.

Allowlist format
----------------
Each line in the allowlist file is a literal string.  Any finding whose
matched text exactly equals an allowlist entry is suppressed.  Use allowlists
only for intentional examples (e.g. placeholder tokens in test fixtures).

Integration
-----------
Add to pre-push hook or CI step:
  python3 scripts/publication_scanner.py exports/github-preview/ --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Each entry: (category_label, compiled_regex)
_PATTERNS: list[tuple[str, re.Pattern[str]]] = []


def _add(label: str, pattern: str, flags: int = 0) -> None:
    _PATTERNS.append((label, re.compile(pattern, flags)))


# --- Secret / token patterns -----------------------------------------------

# Generic high-entropy token: long alphanum+symbol string after key= / token= etc.
_add(
    "secret:generic-token-assignment",
    r'(?i)(?:api[_-]?key|token|secret|password|passwd|auth[_-]?key|access[_-]?key'
    r'|private[_-]?key|client[_-]?secret)\s*[=:]\s*["\']?([A-Za-z0-9+/\-_]{20,})["\']?',
)

# AWS keys
_add("secret:aws-access-key", r'(?:AKIA|ASIA|AROA)[A-Z0-9]{16}')
_add("secret:aws-secret-key", r'(?i)aws[_\-\s]?secret[_\-\s]?access[_\-\s]?key\s*[=:]\s*\S{20,}')

# OpenAI / Anthropic / generic sk- bearer tokens
_add("secret:openai-key", r'sk-[A-Za-z0-9\-_]{20,}')
_add("secret:anthropic-key", r'sk-ant-[A-Za-z0-9\-_]{20,}')

# Slack bot/user tokens
_add("secret:slack-bot-token", r'xoxb-[0-9A-Za-z\-]{20,}')
_add("secret:slack-user-token", r'xoxp-[0-9A-Za-z\-]{20,}')
_add("secret:slack-app-token", r'xapp-[0-9A-Za-z\-]{20,}')

# Slack workspace/channel IDs (Txxxxxxxx / Cxxxxxxxx / Uxxxxxxxx)
_add("slack:workspace-id", r'\bT[A-Z0-9]{8,10}\b')
_add("slack:channel-id", r'\bC[A-Z0-9]{8,10}\b')
_add("slack:user-id", r'\bU[A-Z0-9]{8,10}\b')

# GitHub PATs
_add("secret:github-pat", r'ghp_[A-Za-z0-9]{36,}')
_add("secret:github-fine-grained-pat", r'github_pat_[A-Za-z0-9_]{40,}')

# Google API keys
_add("secret:google-api-key", r'AIza[A-Za-z0-9\-_]{35}')

# Twilio
_add("secret:twilio-sid", r'AC[a-f0-9]{32}')
_add("secret:twilio-auth-token", r'(?i)twilio.*auth.*token\s*[=:]\s*[a-f0-9]{32}')

# Bearer tokens in headers
_add("secret:bearer-token", r'(?i)Authorization:\s*Bearer\s+[A-Za-z0-9\-_\.=]{20,}')

# Private key blocks
_add("secret:private-key-block", r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')

# --- Local path patterns ----------------------------------------------------

# Absolute paths starting with /Users/ (macOS home dirs)
_add("path:local-users", r'/Users/[A-Za-z][A-Za-z0-9_\-]+/')

# Absolute paths starting with /home/ (Linux home dirs)
_add("path:local-home", r'/home/[A-Za-z][A-Za-z0-9_\-]+/')

# Absolute paths starting with /root/
_add("path:local-root", r'/root/')

# Tilde-expanded home shorthand in configs (~/foo)
_add("path:tilde-home", r'(?<!\w)~/(\.config|\.ssh|\.aws|\.env|Workspaces|Documents|Downloads)')

# --- Audience / frontmatter -------------------------------------------------

# audience: private or internal in YAML frontmatter
_add(
    "frontmatter:private-audience",
    r'^audience\s*:\s*(?:private|internal)',
    re.MULTILINE,
)

# --- Private folder references ----------------------------------------------

# References to vault-internal raw/, inbox/, private/ directories
_add("path:raw-folder", r'(?<![a-zA-Z0-9_\-])(raw|inbox|private)/(?!\.)')
_add("path:private-vault-dir", r'work/(?:raw|inbox|private)/')

# client-facing or public export movement paths
_add("path:client-facing-export", r'exports/(?:client-facing|public)/')

# ---------------------------------------------------------------------------
# Finding data class
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    file: Path
    line_no: int
    category: str
    matched_text: str
    line_text: str = ""

    def is_allowlisted(self, allowlist: set[str]) -> bool:
        return self.matched_text.strip() in allowlist

    def __str__(self) -> str:
        short = self.matched_text[:80] + ("…" if len(self.matched_text) > 80 else "")
        return f"{self.file}:{self.line_no} [{self.category}] {short!r}"


# ---------------------------------------------------------------------------
# Scanner core
# ---------------------------------------------------------------------------


def _load_allowlist(path: Optional[Path]) -> set[str]:
    if path is None or not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")}


def scan_text(text: str, filepath: Path) -> list[Finding]:
    """Scan *text* for all registered patterns. Returns list of findings."""
    findings: list[Finding] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        for category, pattern in _PATTERNS:
            for match in pattern.finditer(line):
                # Use the first capturing group if present, else whole match
                matched = match.group(1) if match.lastindex else match.group(0)
                findings.append(
                    Finding(
                        file=filepath,
                        line_no=lineno,
                        category=category,
                        matched_text=matched,
                        line_text=line.strip(),
                    )
                )
    return findings


def scan_file(path: Path, allowlist: set[str]) -> list[Finding]:
    """Read and scan a single file. Returns non-allowlisted findings."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [
            Finding(
                file=path,
                line_no=0,
                category="error:read",
                matched_text=str(exc),
            )
        ]
    raw = scan_text(text, path)
    return [f for f in raw if not f.is_allowlisted(allowlist)]


# Extensions we consider for scanning. Binary files are skipped.
_TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".sh", ".env", ".html", ".css",
    ".rst", ".csv", ".xml", ".sql",
}

# Always skip these directory names
_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def scan_path(
    target: Path,
    allowlist: set[str],
    extensions: Optional[set[str]] = None,
) -> list[Finding]:
    """Recursively scan *target* (file or directory). Returns all findings."""
    exts = extensions or _TEXT_EXTENSIONS
    all_findings: list[Finding] = []

    if target.is_file():
        if target.suffix.lower() in exts or not target.suffix:
            all_findings.extend(scan_file(target, allowlist))
    elif target.is_dir():
        for child in sorted(target.rglob("*")):
            if any(part in _SKIP_DIRS for part in child.parts):
                continue
            if child.is_file() and (child.suffix.lower() in exts or not child.suffix):
                all_findings.extend(scan_file(child, allowlist))
    return all_findings


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def _group_by_file(findings: list[Finding]) -> dict[Path, list[Finding]]:
    groups: dict[Path, list[Finding]] = {}
    for f in findings:
        groups.setdefault(f.file, []).append(f)
    return groups


def format_report(findings: list[Finding], verbose: bool = False) -> str:
    if not findings:
        return "publication_scanner: CLEAN — no findings.\n"

    lines: list[str] = [
        f"publication_scanner: {len(findings)} finding(s) across "
        f"{len(_group_by_file(findings))} file(s).\n"
    ]
    for file, file_findings in _group_by_file(findings).items():
        lines.append(f"\n{file}")
        for f in file_findings:
            short = f.matched_text[:80] + ("…" if len(f.matched_text) > 80 else "")
            lines.append(f"  L{f.line_no:4d}  [{f.category}]  {short!r}")
            if verbose and f.line_text:
                lines.append(f"          context: {f.line_text[:120]}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="publication_scanner",
        description=(
            "Scan vault files for secrets, private audience markers, local paths, "
            "and other publication boundary violations before GitHub export."
        ),
    )
    p.add_argument("target", type=Path, help="File or directory to scan.")
    p.add_argument(
        "--allowlist",
        type=Path,
        default=None,
        metavar="FILE",
        help="Path to allowlist file (one literal string per line).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any findings are present (use in CI / pre-push).",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show source line context for each finding.",
    )
    p.add_argument(
        "--extensions",
        default=None,
        metavar="EXT,...",
        help="Comma-separated list of file extensions to scan (default: common text types).",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    target: Path = args.target
    if not target.exists():
        print(f"publication_scanner: error: path not found: {target}", file=sys.stderr)
        return 2

    allowlist = _load_allowlist(args.allowlist)

    extensions: Optional[set[str]] = None
    if args.extensions:
        extensions = {e.strip() if e.startswith(".") else f".{e.strip()}"
                      for e in args.extensions.split(",")}

    findings = scan_path(target, allowlist, extensions)
    print(format_report(findings, verbose=args.verbose), end="")

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
