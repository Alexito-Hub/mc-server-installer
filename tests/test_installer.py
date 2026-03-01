import unittest
import tempfile
from pathlib import Path
import hashlib
import json

# Import functions from auralix.py
from auralix import hash_file, validate_state

class InstallerUnitTests(unittest.TestCase):
    def test_hash_file_sha256(self):
        data = b'hello world'
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'f.bin'
            p.write_bytes(data)
            h = hash_file(p, 'sha256')
            self.assertEqual(h, hashlib.sha256(data).hexdigest())

    def test_validate_state_ok(self):
        state = {
            "server_name": "My Server",
            "java_instances": [{"port": 25565}],
            "bedrock_instances": [{"port": 19132}]
        }
        ok, msgs = validate_state(state)
        self.assertTrue(ok)
        self.assertEqual(len(msgs), 0)

    def test_validate_state_fail(self):
        state = {
            "server_name": "",
            "java_instances": [{"port": 999999}],
        }
        ok, msgs = validate_state(state)
        self.assertFalse(ok)
        self.assertGreater(len(msgs), 0)

if __name__ == '__main__':
    unittest.main()
