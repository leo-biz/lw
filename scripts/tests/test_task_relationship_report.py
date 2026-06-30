"""Tests for task_relationship_report.py — explicit deps, shared-page suggestions, unrelated tasks, false-positive controls."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.task_relationship_report import (
    TaskRecord,
    build_index,
    explicit_relationships,
    render_report,
    resolve_task_path,
    reverse_blocks,
    score_candidate,
    split_task,
    suggest_related,
)

SIMPLE_BODY = "\n## What\n\nExample.\n\n## Activity\n\n## Linked Nodes\n"


def make_task(directory: Path, filename: str, meta: dict, body: str = SIMPLE_BODY) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip()
    path.write_text(f"---\n{front}\n---\n{body}")
    return path


def _record(tmp: Path, subdir: str, filename: str, meta: dict, body: str = SIMPLE_BODY) -> TaskRecord:
    path = make_task(tmp / subdir, filename, meta, body)
    m, b = split_task(path)
    return TaskRecord(
        task_id=m["id"], status=m.get("status", ""), path=path, meta=m, body=b
    )


# ---------------------------------------------------------------------------
# explicit_relationships
# ---------------------------------------------------------------------------

class TestExplicitRelationships(unittest.TestCase):
    def test_empty_fields(self):
        meta = {"id": "task-2026-05-01-x", "blocked_by": "", "related_tasks": []}
        rel = explicit_relationships(meta)
        self.assertEqual(rel["blocked_by"], [])
        self.assertEqual(rel["related_tasks"], [])

    def test_single_blocked_by_string(self):
        meta = {"id": "task-2026-05-01-x", "blocked_by": "task-2026-05-01-dep"}
        rel = explicit_relationships(meta)
        self.assertEqual(rel["blocked_by"], ["task-2026-05-01-dep"])

    def test_list_related_tasks(self):
        meta = {"id": "task-2026-05-01-x", "related_tasks": ["task-a", "task-b"]}
        rel = explicit_relationships(meta)
        self.assertEqual(rel["related_tasks"], ["task-a", "task-b"])

    def test_list_depends_on(self):
        meta = {"id": "task-2026-05-01-x", "depends_on": ["task-a", "task-b"]}
        rel = explicit_relationships(meta)
        self.assertEqual(rel["depends_on"], ["task-a", "task-b"])

    def test_list_dependents(self):
        meta = {"id": "task-2026-05-01-x", "dependents": ["task-a", "task-b"]}
        rel = explicit_relationships(meta)
        self.assertEqual(rel["dependents"], ["task-a", "task-b"])

    def test_parent_task(self):
        meta = {"id": "task-2026-05-01-x", "parent_task": "task-2026-05-01-parent"}
        rel = explicit_relationships(meta)
        self.assertEqual(rel["parent_task"], ["task-2026-05-01-parent"])


# ---------------------------------------------------------------------------
# reverse_blocks
# ---------------------------------------------------------------------------

class TestReverseBlocks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_no_dependents(self):
        _record(self.tmp, "ready", "a.md", {"id": "task-a", "title": "A", "status": "READY"})
        _record(self.tmp, "blocked", "b.md",
                {"id": "task-b", "title": "B", "status": "BLOCKED", "blocked_by": "task-c"})
        index = build_index(self.tmp)
        self.assertEqual(reverse_blocks("task-a", index), [])

    def test_one_dependent(self):
        _record(self.tmp, "done", "a.md", {"id": "task-a", "title": "A", "status": "DONE"})
        _record(self.tmp, "blocked", "b.md",
                {"id": "task-b", "title": "B", "status": "BLOCKED", "blocked_by": "task-a"})
        index = build_index(self.tmp)
        self.assertIn("task-b", reverse_blocks("task-a", index))

    def test_multiple_dependents(self):
        _record(self.tmp, "done", "a.md", {"id": "task-a", "title": "A", "status": "DONE"})
        _record(self.tmp, "blocked", "b.md",
                {"id": "task-b", "title": "B", "status": "BLOCKED", "blocked_by": "task-a"})
        _record(self.tmp, "blocked", "c.md",
                {"id": "task-c", "title": "C", "status": "BLOCKED", "blocked_by": ["task-a", "task-x"]})
        index = build_index(self.tmp)
        dependents = reverse_blocks("task-a", index)
        self.assertIn("task-b", dependents)
        self.assertIn("task-c", dependents)


# ---------------------------------------------------------------------------
# score_candidate
# ---------------------------------------------------------------------------

class TestScoreCandidate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _make(self, subdir: str, filename: str, meta: dict, body: str = SIMPLE_BODY) -> TaskRecord:
        return _record(self.tmp, subdir, filename, meta, body)

    def test_unrelated_tasks_score_zero(self):
        t = self._make("ready", "a.md", {"id": "task-a", "title": "Alpha process", "status": "READY",
                                          "tags": ["foo"], "wiki_page": "[[wiki/a]]"})
        c = self._make("ready", "b.md", {"id": "task-b", "title": "Beta unrelated thing", "status": "READY",
                                          "tags": ["bar"], "wiki_page": "[[wiki/b]]"})
        result = score_candidate(t, c)
        self.assertIsNone(result)

    def test_shared_wiki_page_scores(self):
        t = self._make("ready", "a.md", {"id": "task-a", "title": "A", "status": "READY",
                                          "wiki_page": "[[wiki/systems]]"})
        c = self._make("ready", "b.md", {"id": "task-b", "title": "B", "status": "READY",
                                          "wiki_page": "[[wiki/systems]]"})
        result = score_candidate(t, c)
        self.assertIsNotNone(result)
        self.assertGreater(result.score, 0)
        self.assertTrue(any("wiki_page" in r for r in result.reasons))

    def test_shared_tags_score(self):
        t = self._make("ready", "a.md", {"id": "task-a", "title": "A", "status": "READY",
                                          "tags": ["systems", "tasks"]})
        c = self._make("ready", "b.md", {"id": "task-b", "title": "B", "status": "READY",
                                          "tags": ["systems", "unrelated"]})
        result = score_candidate(t, c)
        self.assertIsNotNone(result)
        self.assertTrue(any("systems" in r for r in result.reasons))

    def test_same_workstream_scores(self):
        t = self._make("ready", "a.md", {"id": "task-a", "title": "A", "status": "READY",
                                          "workstream": "infra"})
        c = self._make("ready", "b.md", {"id": "task-b", "title": "B", "status": "READY",
                                          "workstream": "infra"})
        result = score_candidate(t, c)
        self.assertIsNotNone(result)
        self.assertTrue(any("workstream" in r for r in result.reasons))

    def test_explicitly_related_skipped(self):
        t = self._make("ready", "a.md", {"id": "task-a", "title": "A", "status": "READY",
                                          "related_tasks": ["task-b"], "wiki_page": "[[wiki/shared]]"})
        c = self._make("ready", "b.md", {"id": "task-b", "title": "B", "status": "READY",
                                          "wiki_page": "[[wiki/shared]]"})
        result = score_candidate(t, c)
        self.assertIsNone(result, "explicitly-related task must be excluded from suggestions")

    def test_self_excluded(self):
        t = self._make("ready", "a.md", {"id": "task-a", "title": "A", "status": "READY",
                                          "tags": ["x", "y"]})
        result = score_candidate(t, t)
        self.assertIsNone(result)

    def test_title_word_overlap_scores(self):
        t = self._make("ready", "a.md", {"id": "task-a", "title": "dependency reconciliation helper", "status": "READY"})
        c = self._make("ready", "b.md", {"id": "task-b", "title": "dependency resolution workflow", "status": "READY"})
        result = score_candidate(t, c)
        self.assertIsNotNone(result)
        self.assertTrue(any("dependency" in r for r in result.reasons))

    def test_shared_wikilinks_in_body_score(self):
        body_a = "\n## Activity\n\nSee [[wiki/systems/task-system]] for details.\n"
        body_b = "\n## Activity\n\nRelated to [[wiki/systems/task-system]] workflow.\n"
        t = self._make("ready", "a.md", {"id": "task-a", "title": "Alpha", "status": "READY"}, body_a)
        c = self._make("ready", "b.md", {"id": "task-b", "title": "Beta", "status": "READY"}, body_b)
        result = score_candidate(t, c)
        self.assertIsNotNone(result)
        self.assertTrue(any("wikilinks" in r for r in result.reasons))


# ---------------------------------------------------------------------------
# suggest_related
# ---------------------------------------------------------------------------

class TestSuggestRelated(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_top_n_limit(self):
        shared_wiki = "[[wiki/systems]]"
        ready = self.tmp / "ready"
        target = _record(self.tmp, "ready", "t.md",
                          {"id": "task-target", "title": "Target", "status": "READY",
                           "wiki_page": shared_wiki})
        for i in range(10):
            _record(self.tmp, "ready", f"c{i}.md",
                    {"id": f"task-candidate-{i:02d}", "title": f"Candidate {i}", "status": "READY",
                     "wiki_page": shared_wiki})
        index = build_index(self.tmp)
        suggestions = suggest_related(target, index, top_n=5)
        self.assertLessEqual(len(suggestions), 5)

    def test_unrelated_not_suggested(self):
        target = _record(self.tmp, "ready", "t.md",
                          {"id": "task-target", "title": "Target automation", "status": "READY",
                           "tags": ["alpha"]})
        _record(self.tmp, "ready", "u.md",
                {"id": "task-unrelated", "title": "Completely different thing", "status": "READY",
                 "tags": ["omega"]})
        index = build_index(self.tmp)
        suggestions = suggest_related(target, index)
        ids = [s.task_id for s in suggestions]
        self.assertNotIn("task-unrelated", ids)

    def test_higher_score_ranked_first(self):
        shared = "[[wiki/shared]]"
        target = _record(self.tmp, "ready", "t.md",
                          {"id": "task-t", "title": "Target pipeline", "status": "READY",
                           "wiki_page": shared, "tags": ["systems", "tasks"]})
        strong = _record(self.tmp, "ready", "s.md",
                          {"id": "task-strong", "title": "Strong pipeline match", "status": "READY",
                           "wiki_page": shared, "tags": ["systems", "tasks"]})
        weak = _record(self.tmp, "ready", "w.md",
                        {"id": "task-weak", "title": "Weak mention", "status": "READY",
                         "tags": ["systems"]})
        index = build_index(self.tmp)
        suggestions = suggest_related(target, index)
        ids = [s.task_id for s in suggestions]
        self.assertIn("task-strong", ids)
        self.assertIn("task-weak", ids)
        self.assertLess(ids.index("task-strong"), ids.index("task-weak"))


# ---------------------------------------------------------------------------
# render_report
# ---------------------------------------------------------------------------

class TestRenderReport(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_report_contains_task_id(self):
        target = _record(self.tmp, "ready", "t.md",
                          {"id": "task-2026-05-31-target", "title": "My Task", "status": "READY"})
        index = build_index(self.tmp)
        output = render_report(target, index)
        self.assertIn("task-2026-05-31-target", output)
        self.assertIn("My Task", output)

    def test_report_shows_blocked_by(self):
        _record(self.tmp, "done", "dep.md",
                {"id": "task-dep", "title": "Dep", "status": "DONE"})
        target = _record(self.tmp, "blocked", "t.md",
                          {"id": "task-target", "title": "Target", "status": "BLOCKED",
                           "blocked_by": "task-dep"})
        index = build_index(self.tmp)
        output = render_report(target, index)
        self.assertIn("blocked_by", output)
        self.assertIn("task-dep", output)

    def test_report_shows_depends_on(self):
        target = _record(
            self.tmp, "ready", "target.md",
            {"id": "task-2026-05-31-target", "title": "Target", "status": "READY",
             "depends_on": ["task-2026-05-31-dep"]},
        )
        _record(
            self.tmp, "done", "dep.md",
            {"id": "task-2026-05-31-dep", "title": "Dependency", "status": "DONE"},
        )
        output = render_report(target, build_index(self.tmp))
        self.assertIn("depends_on", output)
        self.assertIn("[DONE] task-2026-05-31-dep", output)

    def test_report_shows_dependents(self):
        target = _record(
            self.tmp, "done", "target.md",
            {"id": "task-2026-05-31-target", "title": "Target", "status": "DONE",
             "dependents": ["task-2026-05-31-child"]},
        )
        _record(
            self.tmp, "ready", "child.md",
            {"id": "task-2026-05-31-child", "title": "Child", "status": "READY"},
        )
        output = render_report(target, build_index(self.tmp))
        self.assertIn("dependents", output)
        self.assertIn("[READY] task-2026-05-31-child", output)

    def test_compact_omits_reasons(self):
        target = _record(self.tmp, "ready", "t.md",
                          {"id": "task-t", "title": "T", "status": "READY", "tags": ["systems"]})
        _record(self.tmp, "ready", "c.md",
                {"id": "task-c", "title": "C", "status": "READY", "tags": ["systems"]})
        index = build_index(self.tmp)
        full = render_report(target, index, compact=False)
        compact = render_report(target, index, compact=True)
        self.assertIn("shared tags", full)
        self.assertNotIn("shared tags", compact)

    def test_no_explicit_relationships_shows_none(self):
        target = _record(self.tmp, "ready", "t.md",
                          {"id": "task-t", "title": "T", "status": "READY"})
        index = build_index(self.tmp)
        output = render_report(target, index)
        self.assertIn("(none)", output)


# ---------------------------------------------------------------------------
# resolve_task_path
# ---------------------------------------------------------------------------

class TestResolveTaskPath(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_resolves_by_file_path(self):
        path = make_task(self.tmp / "ready", "example.md",
                          {"id": "task-2026-05-01-example", "status": "READY"})
        result = resolve_task_path(path, self.tmp)
        self.assertEqual(result, path.resolve())

    def test_resolves_bare_id(self):
        make_task(self.tmp / "ready", "example.md",
                   {"id": "task-2026-05-01-example", "status": "READY"})
        result = resolve_task_path(Path("task-2026-05-01-example"), self.tmp)
        self.assertEqual(result.name, "example.md")

    def test_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            resolve_task_path(Path("task-2026-05-01-ghost"), self.tmp)


if __name__ == "__main__":
    unittest.main()
