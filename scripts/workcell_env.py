#!/usr/bin/env python3
"""Parse workspace .workcell/.env files for docker environment injection."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class EnvParseError(ValueError):
    def __init__(self, line_number: int, message: str) -> None:
        super().__init__(f"line {line_number}: {message}")
        self.line_number = line_number


def _strip_unquoted_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if in_double and char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()
    return value.rstrip()


def _unescape_double_quoted(value: str, line_number: int) -> str:
    result: list[str] = []
    escaped = False
    escapes = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "\\": "\\",
        '"': '"',
        "$": "$",
    }
    for char in value:
        if escaped:
            result.append(escapes.get(char, char))
            escaped = False
        elif char == "\\":
            escaped = True
        else:
            result.append(char)
    if escaped:
        raise EnvParseError(line_number, "unfinished escape in double-quoted value")
    return "".join(result)


def parse_env_line(raw_line: str, line_number: int) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None

    if line.startswith("export "):
        line = line[len("export ") :].lstrip()

    if "=" not in line:
        raise EnvParseError(line_number, "expected KEY=VALUE")

    key, value = line.split("=", 1)
    key = key.strip()
    if not KEY_RE.fullmatch(key):
        raise EnvParseError(line_number, f"invalid variable name {key!r}")

    value = _strip_unquoted_comment(value.lstrip())
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return key, value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return key, _unescape_double_quoted(value[1:-1], line_number)
    if value.startswith(("'", '"')) or value.endswith(("'", '"')):
        raise EnvParseError(line_number, "mismatched quotes")
    return key, value


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open(encoding="utf-8") as env_file:
        for line_number, raw_line in enumerate(env_file, start=1):
            parsed = parse_env_line(raw_line.rstrip("\n"), line_number)
            if parsed is None:
                continue
            key, value = parsed
            values[key] = value
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse a workcell dotenv file")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    try:
        values = parse_env_file(args.path)
    except OSError as exc:
        print(f"Error reading {args.path}: {exc}", file=sys.stderr)
        return 1
    except EnvParseError as exc:
        print(f"Error parsing {args.path}: {exc}", file=sys.stderr)
        return 1

    for key, value in values.items():
        if "\n" in value:
            print(
                f"Error parsing {args.path}: multiline value for {key} is not supported",
                file=sys.stderr,
            )
            return 1
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
