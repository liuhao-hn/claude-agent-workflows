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
            "| Task | Owner | Status | Contract / Output | Blockers |\n"
            "|---|---|---|---|---|\n"
            "| `001-a` | codex | DONE | `artifacts/contract/001-a.md` | None |\n"
            "| `002-b` | zcode | REVIEW | `artifacts/contract/002-b.md` | `001-a` |\n",
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
        for sub in ("contract", "review", "verify", "handoff"):
            self.assertTrue((self.root / "artifacts" / sub).is_dir())

    def test_new_task_creates_contract_and_row(self):
        caw.cmd_init(fake_args(dir=str(self.root)))
        caw.cmd_new_task(fake_args(dir=str(self.root), title="修复登录bug", owner="codex", id=None, dep=None, force=False))
        tasks = caw.parse_tasks(self.root / "TASKS.md")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], "001")
        self.assertEqual(tasks[0]["owner"], "codex")
        self.assertEqual(tasks[0]["status"], "BACKLOG")
        rel = tasks[0]["contract"].strip("`")
        contract = self.root / rel
        self.assertTrue(contract.exists())
        self.assertIn("修复登录bug", contract.read_text(encoding="utf-8"))
        self.assertIn("Owner：codex", contract.read_text(encoding="utf-8"))

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
        self.assertIn("artifacts/contract/001", out)

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


if __name__ == "__main__":
    unittest.main()
