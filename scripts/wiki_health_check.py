#!/usr/bin/env python3
"""Generate a compact report-only health check for the Leo Life Wiki vault.

Policy — read before modifying this file:
  wiki/07-systems/wiki-operating-rules.md  provenance, tags, status values, audience boundaries
  wiki/07-systems/wiki-health-check.md     check definitions, thresholds, and report format
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", ".obsidian", ".tmp", "__pycache__", "runs"}
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
VALID_TAG_RE = re.compile(r"^[a-z0-9]+(?:[/-][a-z0-9]+)*$")
PROVENANCE_RE = re.compile(r"(?m)^-\s+(?:source|derived_from|implements):\s+\[\[")
CURRENT_RE = re.compile(r"\bcurrent\b", re.IGNORECASE)


@dataclass
class Page:
    path: Path
    relative: Path
    text: str
    metadata: dict
    frontmatter_error: str | None = None


def parse_frontmatter(text: str) -> tuple[dict, str | None]:
    if not text.startswith("---\n"):
        return {}, None
    try:
        frontmatter, _body = text[4:].split("\n---\n", 1)
        metadata = yaml.safe_load(frontmatter) or {}
        if not isinstance(metadata, dict):
            return {}, "frontmatter must be a YAML mapping"
        return metadata, None
    except (ValueError, yaml.YAMLError) as exc:
        return {}, str(exc).splitlines()[0]


def markdown_pages(root: Path) -> list[Page]:
    pages = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_PARTS for part in path.relative_to(root).parts):
            continue
        text = path.read_text(errors="replace")
        metadata, error = parse_frontmatter(text)
        pages.append(Page(path, path.relative_to(root), text, metadata, error))
    return pages


def page_aliases(page: Page) -> set[str]:
    without_suffix = page.relative.with_suffix("").as_posix()
    return {without_suffix, page.relative.as_posix(), page.relative.stem}


def link_target(raw_link: str) -> str:
    target = raw_link.split("|", 1)[0].split("#", 1)[0].strip().rstrip("\\")
    return target.removesuffix(".md")


def resolve_link(page: Page, target: str, aliases: dict[str, list[Page]], root: Path) -> bool:
    if not target or "://" in target:
        return True
    direct_candidates = (
        root / f"{target}.md",
        page.path.parent / f"{target}.md",
        root / target,
        page.path.parent / target,
    )
    if any(candidate.resolve().is_file() for candidate in direct_candidates):
        return True
    return len(aliases.get(target, [])) == 1


def markdown_link_issues(pages: list[Page], root: Path) -> tuple[list[str], dict[Path, int]]:
    aliases: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        for alias in page_aliases(page):
            aliases[alias].append(page)

    broken = []
    incoming: dict[Path, int] = defaultdict(int)
    for page in pages:
        if page.relative.parts and page.relative.parts[0] == "raw":
            continue
        for raw_link in WIKILINK_RE.findall(page.text):
            target = link_target(raw_link)
            if not resolve_link(page, target, aliases, root):
                broken.append(f"{page.relative}: [[{raw_link}]]")
                continue
            matches = aliases.get(target, [])
            if len(matches) == 1:
                incoming[matches[0].relative] += 1
                continue
            for candidate in (root / f"{target}.md", page.path.parent / f"{target}.md"):
                if candidate.resolve().is_file():
                    try:
                        incoming[candidate.resolve().relative_to(root.resolve())] += 1
                    except ValueError:
                        pass
                    break
    return sorted(set(broken)), incoming


def parse_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip("'\""))
        except ValueError:
            return None
    return None


def list_items(items: list[str], limit: int) -> list[str]:
    shown = [f"- {item}" for item in items[:limit]]
    if len(items) > limit:
        shown.append(f"- ... {len(items) - limit} more")
    return shown or ["- None"]


def report(root: Path, stale_days: int, max_items: int) -> tuple[str, dict]:
    pages = markdown_pages(root)
    wiki_pages = [page for page in pages if page.relative.parts and page.relative.parts[0] == "wiki"]
    today = date.today()
    broken_links, incoming = markdown_link_issues(pages, root)

    malformed_frontmatter = [
        f"{page.relative}: {page.frontmatter_error}" for page in pages if page.frontmatter_error
    ]
    stale_pages = []
    missing_updated = []
    missing_provenance = []
    inconsistent_tags = []
    unprocessed_sources = []
    needs_revision = []
    current_stale = []

    for page in wiki_pages:
        updated = parse_date(page.metadata.get("updated"))
        if updated is None:
            missing_updated.append(str(page.relative))
        elif (today - updated).days > stale_days:
            stale_pages.append(f"{page.relative} ({(today - updated).days} days)")
            if CURRENT_RE.search(str(page.metadata.get("title", page.relative.stem))):
                current_stale.append(str(page.relative))

        if not page.metadata.get("source") and not PROVENANCE_RE.search(page.text):
            missing_provenance.append(str(page.relative))

        tags = page.metadata.get("tags")
        if not isinstance(tags, list) or not tags:
            inconsistent_tags.append(f"{page.relative}: missing or non-list tags")
        else:
            invalid = [str(tag) for tag in tags if not VALID_TAG_RE.fullmatch(str(tag))]
            duplicates = sorted({str(tag) for tag in tags if tags.count(tag) > 1})
            if invalid:
                inconsistent_tags.append(f"{page.relative}: invalid tags {invalid}")
            if duplicates:
                inconsistent_tags.append(f"{page.relative}: duplicate tags {duplicates}")

        if page.metadata.get("status") == "NEEDS_REVISION":
            needs_revision.append(str(page.relative))

    orphaned_pages = [
        str(page.relative)
        for page in wiki_pages
        if not incoming.get(page.relative) and page.relative.name != "home.md"
    ]

    inbox = root / "raw" / "inbox"
    if inbox.exists():
        unprocessed_sources.extend(
            str(path.relative_to(root))
            for path in sorted(inbox.iterdir())
            if path.is_file() and path.name != "README.md"
        )
    unprocessed_sources.extend(
        str(page.relative)
        for page in pages
        if page.relative.parts
        and page.relative.parts[0] == "raw"
        and page.metadata.get("status") == "UNREVIEWED"
    )
    unprocessed_sources = sorted(set(unprocessed_sources))

    deterministic_sections = [
        ("Broken wikilinks", broken_links),
        ("Malformed frontmatter", malformed_frontmatter),
        (f"Stale wiki pages (>{stale_days} days)", stale_pages),
        ("Wiki pages missing updated dates", missing_updated),
        ("Orphaned wiki pages", orphaned_pages),
        ("Wiki pages missing provenance links", missing_provenance),
        ("Inconsistent tags", inconsistent_tags),
        ("Unprocessed sources", unprocessed_sources),
    ]
    ai_sections = [
        ("Current-labeled stale pages", current_stale),
        ("Pages marked NEEDS_REVISION", needs_revision),
        ("Contradiction review", ["Compare current decisions and claims manually; semantic contradictions require AI judgment."]),
    ]

    counts = {heading: len(items) for heading, items in deterministic_sections + ai_sections}
    lines = [
        "# Wiki Health Check",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Vault: `{root}`",
        "",
        "## Thresholds",
        "",
        f"- Stale wiki page: more than {stale_days} days since `updated`.",
        "- Orphaned wiki page: no incoming Obsidian wikilinks from scanned Markdown.",
        "- Missing provenance: wiki page has no `source` metadata and no typed `source`, `derived_from`, or `implements` link.",
        "- Unprocessed source: file remains in `raw/inbox/` or raw Markdown has `status: UNREVIEWED`.",
        "",
        "## Deterministic Checks",
    ]
    for heading, items in deterministic_sections:
        lines.extend(["", f"### {heading} ({len(items)})", "", *list_items(items, max_items)])
    lines.extend(["", "## AI Judgment Queue"])
    for heading, items in ai_sections:
        lines.extend(["", f"### {heading} ({len(items)})", "", *list_items(items, max_items)])
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Markdown pages scanned: {len(pages)}",
            f"- Wiki pages scanned: {len(wiki_pages)}",
            f"- Deterministic findings: {sum(len(items) for _, items in deterministic_sections)}",
            f"- AI-review candidates: {len(current_stale) + len(needs_revision)}",
            "",
        ]
    )
    summary = {
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "job": "wiki-health-check",
        "markdown_pages": len(pages),
        "wiki_pages": len(wiki_pages),
        "deterministic_findings": sum(len(items) for _, items in deterministic_sections),
        "ai_review_candidates": len(current_stale) + len(needs_revision),
        "counts": counts,
    }
    return "\n".join(lines), summary


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=VAULT_ROOT, help="Vault root (default: script parent)")
    parser.add_argument("--output", type=Path, help="Write Markdown report to a file instead of stdout")
    parser.add_argument("--log-jsonl", type=Path, help="Append a compact local JSONL summary")
    parser.add_argument("--stale-days", type=int, default=90)
    parser.add_argument("--max-items", type=int, default=20)
    args = parser.parse_args()
    if args.stale_days < 1 or args.max_items < 1:
        parser.error("--stale-days and --max-items must be positive")
    return args


def main() -> None:
    args = parse_args()
    markdown, summary = report(args.root.resolve(), args.stale_days, args.max_items)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown)
        print(args.output)
    else:
        print(markdown)
    if args.log_jsonl:
        append_jsonl(args.log_jsonl, summary)


if __name__ == "__main__":
    try:
        main()
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
