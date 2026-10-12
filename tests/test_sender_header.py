import sys
import unittest
from pathlib import Path
from email import policy
from email.parser import Parser
from email.header import decode_header, make_header

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'brother_smtp_relay'))
from sender_header import make_sender_header


class SenderHeaderTests(unittest.TestCase):
    def test_display_name_round_trip(self):
        for name in ['Dokumentenscanner', 'Büro Müller', 'Name "quoted", $1 / Scanner', 'Ä' * 200]:
            with self.subTest(name=name):
                header = make_sender_header(name, 'scanner@example.com')
                parsed = Parser(policy=policy.default).parsestr(header + '\n\n')['From'].addresses[0]
                # Decode the RFC 2047 phrase directly: older Python address
                # parsers insert spaces between adjacent encoded words.
                phrase = header.removeprefix('From: ').rsplit(' <', 1)[0]
                self.assertEqual(str(make_header(decode_header(phrase))), name)
                self.assertEqual(parsed.addr_spec, 'scanner@example.com')
                self.assertNotIn('\n', header)
                self.assertNotIn('\r', header)

    def test_empty_name_preserves_original(self):
        for name in ['', '   ']:
            self.assertIsNone(make_sender_header(name, 'scanner@example.com'))

    def test_control_characters_rejected(self):
        for char in ['\r', '\n', '\x00', '\t', '\x7f']:
            with self.assertRaises(ValueError):
                make_sender_header('Scanner' + char + 'Bcc: other@example.com', 'scanner@example.com')

    def test_overlong_name_rejected(self):
        with self.assertRaises(ValueError):
            make_sender_header('x' * 201, 'scanner@example.com')


if __name__ == '__main__':
    unittest.main()
