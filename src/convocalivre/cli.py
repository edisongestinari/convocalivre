"""Minimal CLI, deliberately offline to protect users' personal information."""
import argparse
import json
from pathlib import Path
import sys

from .core import analyze


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="convocalivre", description="Offline, evidence-first name matching in public gazette text."
    )
    parser.add_argument("file", help="UTF-8 .txt file containing extracted public gazette text")
    parser.add_argument("--name", required=True, help="Full name to match; not sent to any server")
    parser.add_argument("--source-url", default="", help="Original public source link (not verified)")
    parser.add_argument("--date", default="", help="Publication date, YYYY-MM-DD (not verified)")
    parser.add_argument("--output", help="JSON report output path. Omit to print to stdout.")
    args = parser.parse_args(argv)
    try:
        body = Path(args.file).read_text(encoding="utf-8")
        report = analyze(body, args.name, source_url=args.source_url, publication_date=args.date)
        encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
