import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from workcell_env import EnvParseError, parse_env_file, parse_env_line


class WorkcellEnvTests(unittest.TestCase):
    def test_parse_comments_blank_lines_and_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n"
                "# comment\n"
                "PLAIN=value\n"
                "SPACED = value with spaces  # trailing comment\n"
                "HASH=foo#bar\n"
                "export EXPORTED=yes\n",
                encoding="utf-8",
            )

            self.assertEqual(
                parse_env_file(env_path),
                {
                    "PLAIN": "value",
                    "SPACED": "value with spaces",
                    "HASH": "foo#bar",
                    "EXPORTED": "yes",
                },
            )

    def test_parse_quoted_values(self):
        self.assertEqual(parse_env_line("SINGLE='quoted # value'", 1), ("SINGLE", "quoted # value"))
        self.assertEqual(
            parse_env_line('DOUBLE="quoted \\"value\\""', 1),
            ("DOUBLE", 'quoted "value"'),
        )
        self.assertEqual(parse_env_line('ESCAPES="line\\nnext\\tend"', 1), ("ESCAPES", "line\nnext\tend"))

    def test_duplicate_keys_last_value_wins(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("KEY=first\nKEY=second\n", encoding="utf-8")

            self.assertEqual(parse_env_file(env_path), {"KEY": "second"})

    def test_invalid_lines_raise_parse_errors(self):
        invalid_lines = [
            "MISSING_VALUE",
            "1BAD=value",
            "BAD-NAME=value",
            "BROKEN='value",
            'BROKEN="value',
        ]

        for line in invalid_lines:
            with self.subTest(line=line):
                with self.assertRaises(EnvParseError):
                    parse_env_line(line, 3)


if __name__ == "__main__":
    unittest.main()
