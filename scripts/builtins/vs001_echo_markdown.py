"""Render one deterministic Markdown document for the VS-001 builtin path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _load_payload(path: Path) -> tuple[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"body", "heading"}:
        raise ValueError("invalid_builtin_payload_keys")
    heading = payload["heading"]
    body = payload["body"]
    if not isinstance(heading, str) or not heading.strip():
        raise ValueError("invalid_builtin_heading")
    if not isinstance(body, str):
        raise ValueError("invalid_builtin_body")
    return heading.strip(), body


def main() -> int:
    args = _parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    try:
        heading, body = _load_payload(input_path)
        output_path.write_text(
            f"# {heading}\n\n{body.rstrip()}\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"controlled_builtin_failed:{exc}", file=sys.stderr)
        return 2
    print("controlled_builtin_completed:result.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
