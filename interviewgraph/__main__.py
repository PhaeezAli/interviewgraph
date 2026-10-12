"""Command line entry point: python -m interviewgraph <command>."""

from __future__ import annotations

import argparse

from . import dataio
from .dedupe import DEFAULT_THRESHOLD, near_pairs
from .validate import validate_repo


def _validate(_args: argparse.Namespace) -> int:
    report = validate_repo()
    if not report.ok:
        print(f"{len(report.errors)} problem(s) found:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("OK")
    for line in report.summary:
        print(line)
    return 0


def _duplicates(args: argparse.Namespace) -> int:
    records = dataio.load_yaml(dataio.QUESTIONS_PATH)
    by_id = {r["id"]: r for r in records}

    flagged = [r for r in records if "duplicate_of" in r]
    print(f"Flagged as duplicates ({len(flagged)}):")
    for record in flagged:
        canonical = by_id[record["duplicate_of"]]
        print(f"  {record['id']}  {record['question']!r}  ->  {canonical['id']}  {canonical['question']!r}")

    pairs = near_pairs(records, args.threshold)
    print(f"\nSimilar but not identical, to review (similarity >= {args.threshold:.2f}, {len(pairs)} pairs):")
    for score, a, b in pairs:
        print(f"  {score:.2f}  {a['id']}  {a['question']}")
        print(f"        {b['id']}  {b['question']}")
    print("\nTo merge a pair, add `duplicate_of: <canonical id>` to the weaker record and run validate.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="interviewgraph", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="check the dataset against the schema and integrity rules")
    validate.set_defaults(run=_validate)

    duplicates = commands.add_parser("duplicates", help="list flagged duplicates and similar pairs to review")
    duplicates.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="similarity cut-off, 0 to 1")
    duplicates.set_defaults(run=_duplicates)

    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
