import unittest
import tempfile
from pathlib import Path
import hashlib

from installer import hash_file, validate_version_string, write_start_scripts


class InstallerUnitTests(unittest.TestCase):
    def test_hash_file_sha256(self):
        data = b'hello world'
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'f.bin'
            p.write_bytes(data)
            h = hash_file(p, 'sha256')
            self.assertEqual(h, hashlib.sha256(data).hexdigest())

    def test_validate_version(self):
        self.assertTrue(validate_version_string('latest'))
        self.assertTrue(validate_version_string('1.16.5'))
        self.assertFalse(validate_version_string('1.16.5-beta'))

    def test_write_start_scripts(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            write_start_scripts('1G', d)
            self.assertTrue((d / 'start.sh').exists())
            self.assertTrue((d / 'start.ps1').exists())


if __name__ == '__main__':
    unittest.main()
