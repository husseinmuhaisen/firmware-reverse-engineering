"""Regressions for executable documentation and scoring evidence."""
import ast
from pathlib import Path
import re
import unittest
from cvss import CVSS3

SKILLS = Path(__file__).resolve().parents[1] / 'plugins/firmware-reverse-engineering/skills'


def python_blocks(path):
    return re.findall(r'^```python\n(.*?)^```\s*$', path.read_text(), re.M | re.S)


class TechnicalExamplesTests(unittest.TestCase):
    def test_python_examples_parse(self):
        for path in SKILLS.rglob('*.md'):
            for number, block in enumerate(python_blocks(path), 1):
                with self.subTest(path=path.name, block=number):
                    ast.parse(block)

    def test_cvss_vectors_match_published_scores(self):
        path = SKILLS / 'firmware-security-reports/references/cvss-scoring.md'
        matches = re.findall(r'(CVSS:3\.1/[A-Z:/]+)\n(?:Base )?Score: ([0-9.]+)', path.read_text())
        self.assertGreaterEqual(len(matches), 15)
        for vector, score in matches:
            with self.subTest(vector=vector):
                self.assertEqual(CVSS3(vector).scores()[0], float(score))

    def test_aes_probe_and_header_offsets(self):
        from Crypto.Cipher import AES
        path = SKILLS / 'firmware-extraction/references/encryption.md'
        block = next(b for b in python_blocks(path) if 'def try_aes_decrypt' in b)
        scope = {'__name__': 'test_example'}
        exec(compile(block, str(path), 'exec'), scope)
        key = bytes(range(16))
        data = b'hsqs' + b'\0' * 28
        encrypted = AES.new(key, AES.MODE_ECB).encrypt(data)
        self.assertEqual(scope['try_aes_decrypt'](encrypted, key), data)
        iv = bytes(range(16, 32))
        cbc = iv + AES.new(key, AES.MODE_CBC, iv).encrypt(data)
        self.assertEqual(scope['try_aes_decrypt'](cbc, key, 'CBC'), data)
        self.assertIsNone(scope['try_aes_decrypt'](b'short', key))
        check = scope['check_firmware_candidate']
        self.assertTrue(check(b'\0' * 0x438 + b'\x53\xef'))
        self.assertTrue(check(b'\x85\x19' + b'\0' * 16))
        self.assertTrue(check(b'\x45\x3d\xcd\x28' + b'\0' * 16))
        self.assertFalse(check(b'header comment mentions hsqs'))
        self.assertFalse(check(b'\x53\xef' + b'\0' * 0x438))
        self.assertFalse(check(b''))


if __name__ == '__main__':
    unittest.main()
