"""Black-box tests with temporary Git indexes and synthetic marker phrases."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "tools/check_publication_privacy.py"
MARKER = "SYNTHETIC CAFÉ"


class PublicationCheckerTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.denylist = self.base / "private.txt"
        self.denylist.write_text(MARKER + "\n", encoding="utf-8-sig")
        self.ack_file = self.base / "review.json"

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, stderr=subprocess.PIPE)

    def stage(self, path, data):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        self.git("add", "--", path)
        return file

    def acknowledge(self, path, data):
        self.ack_file.write_text(json.dumps({path: hashlib.sha256(data).hexdigest()}),
                                 encoding="utf-8")

    def run_checker(self, *opts, use_denylist=True):
        args = ["--denylist", str(self.denylist)] if use_denylist else []
        return subprocess.run([sys.executable, str(CHECKER), *args, *opts],
                              cwd=self.repo, capture_output=True, text=True, check=False)

    def test_checks_staged_blob_not_worktree_and_normalizes(self):
        staged_value = "ＳＹＮＴＨＥＴＩＣ Cafe\u0301"
        file = self.stage("readme.md", f"okay\n{staged_value}\n".encode("utf-8"))
        file.write_text("looks clean on disk", encoding="utf-8")
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        self.assertIn('"readme.md":2:', result.stderr)
        self.assertNotIn(MARKER, result.stderr)
        self.assertNotIn(staged_value, result.stderr)
        self.git("add", "--", "readme.md")
        file.write_text(staged_value, encoding="utf-8")
        self.assertEqual(self.run_checker().returncode, 0)

    def test_checks_unchanged_tracked_files_not_only_staged_diff(self):
        self.stage("unchanged.txt", MARKER.encode("utf-8"))
        self.git("-c", "user.email=synthetic@example.invalid",
                 "-c", "user.name=Synthetic Fixture",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.stage("new.txt", b"safe")
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        self.assertIn('"unchanged.txt":1:', result.stderr)

    def test_denied_filename_is_not_echoed_even_when_content_matches(self):
        self.stage(f"{MARKER}.md", MARKER.encode("utf-8"))
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        self.assertIn("(path withheld)", result.stderr)
        self.assertNotIn("SYNTHETIC", result.stderr)

    def test_binary_review_requires_exact_path_and_staged_sha256(self):
        original = b"\x00\xffbinary"
        self.stage("a/photo.png", original)
        self.assertEqual(self.run_checker().returncode, 1)
        self.acknowledge("b/photo.png", original)
        opts = ("--opaque-reviews", str(self.ack_file))
        self.assertEqual(self.run_checker(*opts).returncode, 1)
        self.acknowledge("a/photo.png", original)
        self.assertEqual(self.run_checker(*opts).returncode, 0)
        self.stage("a/photo.png", original + b"\0updated")
        self.assertEqual(self.run_checker(*opts).returncode, 1)

    def test_acknowledgement_cannot_excuse_a_visible_literal(self):
        data = b"\x00\xff" + MARKER.encode("utf-8")
        self.stage("opaque", data)
        self.acknowledge("opaque", data)
        result = self.run_checker("--opaque-reviews", str(self.ack_file))
        self.assertEqual(result.returncode, 1)
        self.assertIn("blocked literal in staged content", result.stderr)

    def test_symlink_is_not_followed_and_needs_exact_review(self):
        target = self.base / "outside.txt"
        target.write_text(MARKER, encoding="utf-8")
        try:
            (self.repo / "reference").symlink_to("../outside.txt")
        except OSError as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        self.git("add", "--", "reference")
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        self.assertIn("symlink", result.stderr)
        self.acknowledge("reference", b"../outside.txt")
        self.assertEqual(self.run_checker("--opaque-reviews", str(self.ack_file)).returncode, 0)

    def test_lfs_reference_never_reviewed_by_pointer_digest(self):
        pointer = b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"0"*64 + b"\nsize 9\n"
        self.stage("media.lfs", pointer)
        self.acknowledge("media.lfs", pointer)
        result = self.run_checker("--opaque-reviews", str(self.ack_file))
        self.assertEqual(result.returncode, 1)
        self.assertIn("external payload", result.stderr)

    def test_missing_empty_or_repository_local_denylist_is_rejected(self):
        self.stage("safe.md", b"okay")
        self.assertEqual(self.run_checker(use_denylist=False).returncode, 2)
        self.denylist.write_text("\n \n", encoding="utf-8")
        self.assertEqual(self.run_checker().returncode, 2)
        self.denylist.unlink()
        self.assertEqual(self.run_checker().returncode, 2)
        internal = self.repo / "private.txt"
        internal.write_text(MARKER, encoding="utf-8")
        result = self.run_checker("--denylist", str(internal), use_denylist=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside the repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
