import subprocess
import unittest
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parents[1] / 'scripts' / 'tf2coach'


class TestLauncher(unittest.TestCase):
    def test_dry_run_is_noninteractive(self):
        result = subprocess.run([str(LAUNCHER), '--dry-run'], capture_output=True, text=True, check=True)
        self.assertIn('steam -applaunch 440', result.stdout)
        self.assertIn('+ds_enable 2', result.stdout)
        self.assertIn('+ds_dir tf2coach', result.stdout)
        self.assertIn('+ds_screens 0', result.stdout)
        self.assertIn('+ds_autodelete 0', result.stdout)

    def test_help(self):
        result = subprocess.run([str(LAUNCHER), '--help'], capture_output=True, text=True, check=True)
        self.assertIn('--dry-run', result.stdout)


if __name__ == '__main__':
    unittest.main()
