# test_wp_core.py
import tempfile
import unittest
from pathlib import Path

from parameterized import parameterized

from waypoint.cli import (
    add_waypoint,
    delete_waypoint,
    get_waypoint,
    load_waypoints,
    save_waypoints,
)


class WaypointCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "waypoints.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_and_get_last_waypoint(self) -> None:
        add_waypoint(self.db_path, Path("/tmp/foo"), None)
        add_waypoint(self.db_path, Path("/tmp/bar"), "proj")

        last = get_waypoint(self.db_path, None)
        self.assertEqual(last.directory, "/tmp/bar")
        self.assertEqual(last.name, "proj")

    @parameterized.expand(
        [
            ("by_index", "2", "/tmp/bar"),
            ("by_name", "proj", "/tmp/bar"),
        ]
    )
    def test_selector_by_index_and_name(self, _label: str, selector: str, expected_dir: str) -> None:
        add_waypoint(self.db_path, Path("/tmp/foo"), None)
        add_waypoint(self.db_path, Path("/tmp/bar"), "proj")

        wp = get_waypoint(self.db_path, selector)
        self.assertEqual(wp.directory, expected_dir)

    def test_delete_waypoint_reindexes(self) -> None:
        add_waypoint(self.db_path, Path("/tmp/a"), "a")
        add_waypoint(self.db_path, Path("/tmp/b"), "b")
        add_waypoint(self.db_path, Path("/tmp/c"), "c")

        deleted = delete_waypoint(self.db_path, "b")
        self.assertEqual(deleted.name, "b")

        wps = load_waypoints(self.db_path)
        self.assertEqual([wp.name for wp in wps], ["a", "c"])

        save_waypoints(self.db_path, wps)
        # Now index 2 should be "c"
        wp2 = get_waypoint(self.db_path, 2)
        self.assertEqual(wp2.name, "c")


if __name__ == "__main__":
    unittest.main()