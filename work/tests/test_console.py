"""Live console and log streaming of jobs/overnight.py: progress detection, line splitting, log throttling."""
import io
import os
import queue
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("LP_MACHINE", "test")          # never create or read the real .lp_machine
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "jobs"))
import overnight as ov  # noqa: E402

CHILD = r"""
import sys, time
sys.stderr.write("kscreen: start\n")
for p in (10, 40, 99):
    sys.stderr.write(f"{p}.00% ({p * 1000} decodes) 5000 decodes/s, eta {100 - p} s\r")
    sys.stderr.flush(); time.sleep(0.05)
sys.stderr.write("100.00% (100000 decodes) 5000 decodes/s, eta 0 s\n")
sys.stderr.write("swept 100000 in 1 s\n")
print("result line 1"); print(); print("result line 2")
"""


class Console(unittest.TestCase):
    def test_classify(self):
        ok, txt = ov.classify("95.70% (4110417920 seeds) 817194 seeds/s, eta 226 s", 0)
        self.assertTrue(ok)
        self.assertIn("95.70%", txt)
        self.assertIn("4,110,417,920 seeds", txt)
        self.assertIn("eta 3m46s", txt)
        ok, txt = ov.classify("30/120 name best=1.2 10s", 10)
        self.assertTrue(ok)
        self.assertIn("25.00%", txt)
        self.assertIn("eta ~30s", txt)
        self.assertEqual(ov.classify("swept 1 seeds in 5 s; best score 3", 0), (False, "swept 1 seeds in 5 s; best score 3"))
        self.assertFalse(ov.classify("0/0 nothing", 0)[0])

    def test_throttled_keeps_final_progress_line(self):
        f = io.StringIO()
        w = ov.Throttled(f, every=1e9)
        for t in ("1%", "2%", "3%"):
            w.write(t, True)
        w.write("done", False)
        self.assertEqual(f.getvalue(), "1%\n3%\ndone\n")      # first and newest progress kept, 2% dropped

    def test_pump_splits_on_cr_crlf_and_lf(self):
        r, wfd = os.pipe()
        os.write(wfd, b"a\rb\r\nc\nd\r")        # chunk ends in \r: it may be half of \r\n
        os.write(wfd, b"\ne")
        os.close(wfd)
        q = queue.Queue()
        ov.pump(r, "out", q)
        os.close(r)
        got = []
        while True:
            tag, text, cr = q.get_nowait()
            if text is None:
                break
            got.append((text, cr))
        self.assertEqual(got, [("a", True), ("b", False), ("c", False), ("d", False), ("e", False)])

    def test_run_cmd_streams_and_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            out, err = Path(d) / "out.txt", Path(d) / "err.log"
            step = ov.Step("t/child", [sys.executable, "-c", CHILD], stdout_to=out, stderr_to=err)
            with open(Path(d) / "step.log", "w", encoding="utf-8") as log:
                rc = ov.run_cmd(step, dict(os.environ, PYTHONUNBUFFERED="1"), log, "1/1 t/child cpu")
            self.assertEqual(rc, 0)
            part = Path(str(out) + ".part")
            self.assertEqual(part.read_text(encoding="utf-8"), "result line 1\n\nresult line 2\n")   # in full, blank kept
            lines = err.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "kscreen: start")
            self.assertEqual(lines[-1], "swept 100000 in 1 s")
            self.assertEqual(lines[-2], "100.00% (100000 decodes) 5000 decodes/s, eta 0 s")
            self.assertLess(len(lines), 6)                                  # \r updates throttled, not all kept


if __name__ == "__main__":
    unittest.main()
