"""Smoke tests for core.py + main_decide.apply_answer. No LLM calls."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from core import (
    DEAD_LETTER_SEC,
    DEFER_AFTER_K,
    TERMINAL_STATUSES,
    append_jsonl,
    atomic_write_json,
    crash_detected,
    derive_pending,
    effective_status,
    ensure_inbox,
    inbox_paths,
    latest_checkpoint,
    load_decision,
    proposal_id,
    read_jsonl,
    schema_valid,
)
from main_decide import apply_answer


class TestProposalId(unittest.TestCase):
    def test_stable(self):
        pid1 = proposal_id("T", "Title here", "Rationale goes here")
        pid2 = proposal_id("T", "Title here", "Rationale goes here")
        self.assertEqual(pid1, pid2)
        self.assertEqual(len(pid1), 16)

    def test_changes_on_any_field(self):
        base = proposal_id("T", "A", "X")
        self.assertNotEqual(base, proposal_id("T", "A", "Y"))
        self.assertNotEqual(base, proposal_id("T", "B", "X"))
        self.assertNotEqual(base, proposal_id("U", "A", "X"))


class TestSchemaValid(unittest.TestCase):
    def _good(self):
        return {
            "title": "Switch db pool to pgbouncer",
            "rationale": "Current pool exhausts under lunch spike",
            "impact": "high",
            "affected_roles": ["pm", "oncall"],
        }

    def test_accepts_well_formed(self):
        self.assertTrue(schema_valid(self._good()))

    def test_rejects_missing_field(self):
        for missing in ("title", "rationale", "impact", "affected_roles"):
            d = self._good()
            del d[missing]
            self.assertFalse(schema_valid(d), f"missing={missing}")

    def test_rejects_bad_impact(self):
        for bad in ("", "minimal", "none", "n/a", "tbd", "CRITICAL", "urgent"):
            d = self._good()
            d["impact"] = bad
            self.assertFalse(schema_valid(d), f"impact={bad!r}")

    def test_rejects_short_strings(self):
        d = self._good()
        d["title"] = "Hi"
        self.assertFalse(schema_valid(d))
        d = self._good()
        d["rationale"] = "too short"
        self.assertFalse(schema_valid(d))

    def test_rejects_empty_affected_roles(self):
        d = self._good()
        d["affected_roles"] = []
        self.assertFalse(schema_valid(d))


class TestAtomicWrite(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.json"
            atomic_write_json(p, {"a": 1, "b": "两"})
            self.assertTrue(p.exists())
            self.assertEqual(json.loads(p.read_text("utf-8")), {"a": 1, "b": "两"})

    def test_no_tmp_remains_on_success(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.json"
            atomic_write_json(p, {"k": "v"})
            leftovers = [q for q in Path(td).iterdir() if q.name.endswith(".tmp")]
            self.assertEqual(leftovers, [])


class TestInboxLayout(unittest.TestCase):
    def test_ensure_creates_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            paths = ensure_inbox(root)
            for key in ("role_verdicts_dir", "decisions_dir", "checkpoints_dir", "root"):
                self.assertTrue(paths[key].is_dir(), key)


class TestDerivePending(unittest.TestCase):
    def test_dedup_and_terminal_exclusion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            paths = ensure_inbox(root)
            append_jsonl(
                paths["proposals_appended"],
                {"proposal_id": "a" * 16, "iter": 1, "design": {"title": "t1"}},
            )
            append_jsonl(
                paths["proposals_appended"],
                {"proposal_id": "a" * 16, "iter": 2, "design": {"title": "t1-dup"}},
            )
            append_jsonl(
                paths["proposals_appended"],
                {"proposal_id": "b" * 16, "iter": 2, "design": {"title": "t2"}},
            )
            atomic_write_json(
                paths["decisions_dir"] / f"{'b' * 16}.json",
                {"proposal_id": "b" * 16, "status": "approved", "defer_count": 0},
            )
            pending = derive_pending(root)
            ids = [p["proposal_id"] for p in pending]
            self.assertEqual(ids, ["a" * 16])

    def test_defer_k_exclusion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            paths = ensure_inbox(root)
            pid = "c" * 16
            append_jsonl(
                paths["proposals_appended"],
                {"proposal_id": pid, "iter": 1},
            )
            atomic_write_json(
                paths["decisions_dir"] / f"{pid}.json",
                {"proposal_id": pid, "status": "deferred", "defer_count": DEFER_AFTER_K},
            )
            self.assertEqual(derive_pending(root), [])


class TestCrashDetection(unittest.TestCase):
    def test_no_ckpt_no_crash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            ensure_inbox(root)
            self.assertFalse(crash_detected(root))

    def test_summary_present_no_crash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            paths = ensure_inbox(root)
            atomic_write_json(paths["checkpoints_dir"] / "iter_1.json", {"iter": 1})
            paths["summary_json"].write_text("{}", "utf-8")
            self.assertFalse(crash_detected(root))

    def test_stale_ckpt_is_crash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            paths = ensure_inbox(root)
            ck = paths["checkpoints_dir"] / "iter_1.json"
            atomic_write_json(ck, {"iter": 1})
            old = time.time() - (DEAD_LETTER_SEC + 60)
            os.utime(ck, (old, old))
            self.assertTrue(crash_detected(root))

    def test_fresh_ckpt_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            paths = ensure_inbox(root)
            atomic_write_json(paths["checkpoints_dir"] / "iter_1.json", {"iter": 1})
            self.assertFalse(crash_detected(root))


class TestLatestCheckpoint(unittest.TestCase):
    def test_picks_highest_iter(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "inbox"
            paths = ensure_inbox(root)
            for i in (1, 3, 2):
                atomic_write_json(
                    paths["checkpoints_dir"] / f"iter_{i}.json", {"iter": i}
                )
            (paths["checkpoints_dir"] / "iter_99.json.tmp").write_text("{}", "utf-8")
            ck = latest_checkpoint(root)
            self.assertIsNotNone(ck)
            self.assertEqual(ck["iter"], 3)


class TestApplyAnswer(unittest.TestCase):
    def test_approve_fresh(self):
        out = apply_answer(None, "Approve")
        self.assertEqual(out["status"], "approved")
        self.assertEqual(out["defer_count"], 0)

    def test_deny_fresh(self):
        out = apply_answer(None, "Deny")
        self.assertEqual(out["status"], "denied")

    def test_defer_escalates_to_denied(self):
        prev = None
        for _ in range(DEFER_AFTER_K - 1):
            prev = apply_answer(prev, "Defer")
            self.assertEqual(prev["status"], "deferred")
        final = apply_answer(prev, "Defer")
        self.assertEqual(final["status"], "denied")
        self.assertEqual(final["defer_count"], DEFER_AFTER_K)

    def test_terminal_no_regression(self):
        approved = {"proposal_id": "x", "status": "approved", "defer_count": 0, "history": []}
        out = apply_answer(approved, "Defer")
        self.assertEqual(out["status"], "approved")  # unchanged
        self.assertIs(out, approved)  # short-circuit returns prev dict

    def test_rejects_unknown(self):
        with self.assertRaises(ValueError):
            apply_answer(None, "Maybe")


class TestReadJsonlTolerant(unittest.TestCase):
    def test_skips_blank_and_bad_lines(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.jsonl"
            p.write_text('{"a":1}\n\nnotjson\n{"b":2}\n', "utf-8")
            recs = read_jsonl(p)
            self.assertEqual(recs, [{"a": 1}, {"b": 2}])


class TestVerdictSaysShip(unittest.TestCase):
    def test_negation_not_ship_ready(self):
        from subagent import verdict_says_ship
        self.assertFalse(verdict_says_ship("NOT ship-ready. 4 bugs未修复"))
        self.assertFalse(verdict_says_ship("结论: NOT ship-ready"))
        self.assertFalse(verdict_says_ship("not ready to ship yet"))

    def test_positive_markers(self):
        from subagent import verdict_says_ship
        self.assertTrue(verdict_says_ship("ship-ready. All clear."))
        self.assertTrue(verdict_says_ship("ready to ship."))
        self.assertTrue(verdict_says_ship("no blockers found"))
        self.assertTrue(verdict_says_ship("可出货"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
