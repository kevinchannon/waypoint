# test_install_shell.py
import tempfile
import unittest
from pathlib import Path

from waypoint.cli import (
    write_wp_wrapper,
    ensure_bashrc_profile_block,
    PROFILE_BLOCK_MARKER,
    WP_WRAPPER_SCRIPT,
)


class InstallShellTests(unittest.TestCase):
    def test_write_wp_wrapper_creates_script(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            profile_dir = Path(tempdir) / "profile.d"

            script_path = write_wp_wrapper(profile_dir)

            self.assertTrue(script_path.exists())
            self.assertEqual(script_path.read_text(encoding="utf-8"), WP_WRAPPER_SCRIPT)
            self.assertTrue(script_path.name, "wp.sh")

    def test_ensure_bashrc_profile_block_adds_block_once(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            bashrc_path = Path(tempdir) / ".bashrc"

            # Initially the file doesn't exist
            added_first = ensure_bashrc_profile_block(bashrc_path)
            self.assertTrue(added_first)

            content_first = bashrc_path.read_text(encoding="utf-8")
            self.assertIn(PROFILE_BLOCK_MARKER, content_first)

            # Second call should be idempotent
            added_second = ensure_bashrc_profile_block(bashrc_path)
            self.assertFalse(added_second)

            content_second = bashrc_path.read_text(encoding="utf-8")
            self.assertEqual(content_first, content_second)


if __name__ == "__main__":
    unittest.main()