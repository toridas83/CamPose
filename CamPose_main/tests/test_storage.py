import tempfile
import unittest
from pathlib import Path

import core.storage as storage
from core.config import JsonStore


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_store = storage.history_store
        storage.history_store = JsonStore(Path(self.temp_dir.name) / "history.json", [])

    def tearDown(self):
        storage.history_store = self.original_store
        self.temp_dir.cleanup()

    def test_append_delete_and_clear(self):
        storage.append_session({"started_at": "2026-08-06T10:00:00+09:00"})
        storage.append_session({"started_at": "2026-08-06T11:00:00+09:00"})
        sessions = storage.load_sessions()
        self.assertEqual(len(sessions), 2)
        self.assertTrue(storage.delete_session(storage.record_id(sessions[0])))
        self.assertEqual(len(storage.load_sessions()), 1)
        self.assertEqual(storage.clear_sessions(), 1)
        self.assertEqual(storage.load_sessions(), [])


if __name__ == "__main__":
    unittest.main()

