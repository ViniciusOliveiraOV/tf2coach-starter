import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from demo_inventory import inventory  # noqa: E402


class TestInventory(unittest.TestCase):
    def test_counts_only_dem_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'test.dem').write_bytes(b'12345')
            (folder / 'notes.txt').write_bytes(b'abc')
            result = inventory(folder, now=10**10)
            self.assertEqual(result['count'], 1)
            self.assertEqual(result['total_bytes'], 5)
            self.assertEqual(result['files'][0]['name'], 'test.dem')
            self.assertFalse(result['files'][0]['possible_in_progress'])

    def test_missing_directory_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(NotADirectoryError):
                inventory(Path(temporary) / 'missing')

    def test_never_changes_demo(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            testfile = folder / 'match.dem'
            testfile.write_bytes(b'private match bytes')
            before = testfile.read_bytes()
            inventory(folder, now=10**10)
            self.assertEqual(testfile.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
