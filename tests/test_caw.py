import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import caw


def fake_args(**kwargs):
    return type("Args", (), kwargs)()


class TestHelpers(unittest.TestCase):
    def test_next_id_empty(self):
        self.assertEqual(caw.next_task_id([]), "001")

    def test_next_id_sequence(self):
        tasks = [{"id": "001-a"}, {"id": "002-b"}]
        self.assertEqual(caw.next_task_id(tasks), "003")

    def test_next_id_skips(self):
        tasks = [{"id": "001-a"}, {"id": "009-b"}]
        self.assertEqual(caw.next_task_id(tasks), "010")

    def test_slugify_chinese(self):
        self.assertEqual(caw.slugify("全量数据刷新Job超时修复"), "全量数据刷新job超时修复")

    def test_slugify_empty(self):
        self.assertEqual(caw.slugify("!!!"), "task")


class TestParse(unittest.TestCase):
    def test_parse_tasks(self):
        bb = Path(tempfile.mkdtemp()) / "TASKS.md"
        bb.write_text(
            "# Task Blackboard\n\n"
            "| Task | Owner | Status | 规则 / 产出 | Blockers |\n"
            "|---|---|---|---|---|\n"
            "| `001-a` | codex | DONE | `artifacts/rules/001-a.md` | None |\n"
            "| `002-b` | zcode | REVIEW | `artifacts/rules/002-b.md` | `001-a` |\n",
            encoding="utf-8",
        )
        tasks = caw.parse_tasks(bb)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["id"], "001-a")
        self.assertEqual(tasks[0]["owner"], "codex")
        self.assertEqual(tasks[0]["status"], "DONE")
        self.assertEqual(tasks[1]["status"], "REVIEW")
        self.assertEqual(tasks[1]["blockers"], "`001-a`")

    def test_parse_missing(self):
        self.assertEqual(caw.parse_tasks(Path("/nonexistent/TASKS.md")), [])


class TestNewTask(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_init_creates_skeleton(self):
        caw.cmd_init(fake_args(dir=str(self.root)))
        self.assertTrue((self.root / "TASKS.md").exists())
        for sub in ("rules", "review", "verify", "handoff"):
            self.assertTrue((self.root / "artifacts" / sub).is_dir())

    def test_new_task_creates_rule_and_row(self):
        caw.cmd_init(fake_args(dir=str(self.root)))
        caw.cmd_new_task(fake_args(dir=str(self.root), title="修复登录bug", owner="codex", id=None, dep=None, force=False))
        tasks = caw.parse_tasks(self.root / "TASKS.md")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], "001")
        self.assertEqual(tasks[0]["owner"], "codex")
        self.assertEqual(tasks[0]["status"], "BACKLOG")
        rel = tasks[0]["rule"].strip("`")
        rule_path = self.root / rel
        self.assertTrue(rule_path.exists())
        self.assertIn("修复登录bug", rule_path.read_text(encoding="utf-8"))
        self.assertIn("Owner：codex", rule_path.read_text(encoding="utf-8"))

    def test_new_task_auto_increments(self):
        caw.cmd_init(fake_args(dir=str(self.root)))
        caw.cmd_new_task(fake_args(dir=str(self.root), title="A", owner="zcode", id=None, dep=None, force=False))
        caw.cmd_new_task(fake_args(dir=str(self.root), title="B", owner="codex", id=None, dep="001", force=False))
        tasks = caw.parse_tasks(self.root / "TASKS.md")
        self.assertEqual([t["id"] for t in tasks], ["001", "002"])
        self.assertEqual(tasks[1]["blockers"], "001")


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        caw.cmd_init(fake_args(dir=str(self.root)))

    def _capture(self, fn, **kwargs):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            fn(fake_args(**kwargs))
        finally:
            sys.stdout = old
        return buf.getvalue()

    def test_dispatch_zcode(self):
        caw.cmd_new_task(fake_args(dir=str(self.root), title="刷新", owner="zcode", id=None, dep=None, force=False))
        out = self._capture(caw.cmd_dispatch, dir=str(self.root), task="001", run=False)
        self.assertIn("zcode", out)
        self.assertIn("并严格执行", out)
        self.assertIn("artifacts/rules/001", out)

    def test_dispatch_codex(self):
        caw.cmd_new_task(fake_args(dir=str(self.root), title="修bug", owner="codex", id=None, dep=None, force=False))
        out = self._capture(caw.cmd_dispatch, dir=str(self.root), task="001", run=False)
        self.assertTrue(out.startswith("codex "))

    def test_dispatch_unknown_task(self):
        with self.assertRaises(SystemExit):
            caw.cmd_dispatch(fake_args(dir=str(self.root), task="999", run=False))


class TestStatus(unittest.TestCase):
    def test_status_summary(self):
        root = Path(tempfile.mkdtemp())
        caw.cmd_init(fake_args(dir=str(root)))
        caw.cmd_new_task(fake_args(dir=str(root), title="A", owner="zcode", id=None, dep=None, force=False))
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            caw.cmd_status(fake_args(dir=str(root)))
        finally:
            sys.stdout = old
        out = buf.getvalue()
        self.assertIn("任务总数: 1", out)
        self.assertIn("BACKLOG=1", out)


class TestSet(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        caw.cmd_init(fake_args(dir=str(self.root)))
        caw.cmd_new_task(fake_args(dir=str(self.root), title="A", owner="zcode", id=None, dep=None, force=False))

    def test_set_done(self):
        caw.cmd_set(fake_args(dir=str(self.root), task="001", status="DONE"))
        tasks = caw.parse_tasks(self.root / "TASKS.md")
        self.assertEqual(tasks[0]["status"], "DONE")

    def test_set_lowercase(self):
        caw.cmd_set(fake_args(dir=str(self.root), task="001", status="review"))
        tasks = caw.parse_tasks(self.root / "TASKS.md")
        self.assertEqual(tasks[0]["status"], "REVIEW")

    def test_set_invalid_status(self):
        with self.assertRaises(SystemExit):
            caw.cmd_set(fake_args(dir=str(self.root), task="001", status="NOPE"))

    def test_set_unknown_task(self):
        with self.assertRaises(SystemExit):
            caw.cmd_set(fake_args(dir=str(self.root), task="999", status="DONE"))


class TestShow(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        caw.cmd_init(fake_args(dir=str(self.root)))
        caw.cmd_new_task(fake_args(dir=str(self.root), title="刷新任务", owner="zcode", id=None, dep=None, force=False))

    def _cap(self, fn, **kw):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            fn(fake_args(**kw))
        finally:
            sys.stdout = old
        return buf.getvalue()

    def test_show_prints_rule(self):
        out = self._cap(caw.cmd_show, dir=str(self.root), task="001")
        self.assertIn("任务：刷新任务", out)
        self.assertIn("Owner：zcode", out)


class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        caw.cmd_init(fake_args(dir=str(self.root)))
        caw.cmd_new_task(fake_args(dir=str(self.root), title="A", owner="zcode", id=None, dep=None, force=False))

    def _status(self):
        return caw.parse_tasks(self.root / "TASKS.md")[0]["status"]

    def test_review(self):
        caw.cmd_review(fake_args(dir=str(self.root), task="001", report=None))
        self.assertEqual(self._status(), "REVIEW")

    def test_review_with_report(self):
        caw.cmd_review(fake_args(dir=str(self.root), task="001", report="HIGH: 边界未覆盖，已退回修订"))
        self.assertEqual(self._status(), "REVIEW")
        report_files = list((self.root / "artifacts/review").glob("*_001.md"))
        self.assertTrue(report_files)
        self.assertIn("审查报告", report_files[0].read_text(encoding="utf-8"))
        self.assertIn("HIGH", report_files[0].read_text(encoding="utf-8"))

    def test_done(self):
        caw.cmd_done(fake_args(dir=str(self.root), task="001"))
        self.assertEqual(self._status(), "DONE")

    def test_verify_with_evidence(self):
        caw.cmd_verify(fake_args(dir=str(self.root), task="001", evidence="pytest 全绿"))
        self.assertEqual(self._status(), "DONE")
        rule = self.root / "artifacts/rules/001-a.md"
        text = rule.read_text(encoding="utf-8")
        self.assertIn("验证证据", text)
        self.assertIn("pytest 全绿", text)


class TestInstallSync(unittest.TestCase):
    def test_install_copies_all(self):
        target = Path(tempfile.mkdtemp())
        caw.cmd_install(fake_args(skills=[], target=str(target), mode="copy", force=False))
        self.assertTrue((target / "commander-executor" / "SKILL.md").exists())

    def test_install_skips_existing(self):
        target = Path(tempfile.mkdtemp())
        (target / "commander-executor").mkdir(parents=True)
        (target / "commander-executor" / "SKILL.md").write_text("旧", encoding="utf-8")
        caw.cmd_install(fake_args(skills=["commander-executor"], target=str(target), mode="copy", force=False))
        self.assertEqual((target / "commander-executor" / "SKILL.md").read_text(encoding="utf-8"), "旧")

    def test_install_force_overwrites(self):
        target = Path(tempfile.mkdtemp())
        (target / "commander-executor").mkdir(parents=True)
        (target / "commander-executor" / "SKILL.md").write_text("旧", encoding="utf-8")
        caw.cmd_install(fake_args(skills=["commander-executor"], target=str(target), mode="copy", force=True))
        self.assertNotEqual((target / "commander-executor" / "SKILL.md").read_text(encoding="utf-8"), "旧")

    def test_sync_skips_protected_by_default(self):
        target = Path(tempfile.mkdtemp())
        caw.cmd_sync(fake_args(skills=[], target=str(target), mode="copy"))
        self.assertTrue((target / "commander-executor" / "SKILL.md").exists())
        for name in caw.PROTECTED_SKILLS:
            self.assertFalse((target / name).exists(), f"{name} 应被默认保护")

    def test_sync_protected_when_named(self):
        target = Path(tempfile.mkdtemp())
        caw.cmd_sync(fake_args(skills=["resume-generator"], target=str(target), mode="copy"))
        self.assertTrue((target / "resume-generator" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
