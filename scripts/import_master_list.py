#!/usr/bin/env python3
"""One-shot migration: the master question list (.txt) -> data/questions/questions.yaml.

Once this has run, the YAML files are the source of truth and are edited directly.
Running it again would overwrite hand-made labels, so it refuses to replace an existing
output file unless --force is given.

    uv run python scripts/import_master_list.py interviewgraph_question_bank_and_design_plan.txt
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from interviewgraph import dataio
from interviewgraph.archetype import classify
from interviewgraph.dedupe import exact_groups
from interviewgraph.validate import validate_data


@dataclass(frozen=True)
class Section:
    domain: str
    project: str | None = None
    tags: tuple[str, ...] = ()


# Draft, section-level defaults. Sections that mix several domains are left "unassigned"
# instead of guessed; they get labelled question by question in the labelling pass.
SECTIONS = {
    "A": Section("behavioral"),  # introduction / resume / experience
    "B": Section("python"),
    "C": Section("statistics"),
    "D": Section("machine-learning"),
    "E": Section("deep-learning"),
    "F": Section("computer-vision"),
    "G": Section("computer-vision", project="image-editing-pipeline"),
    "H": Section("deep-learning", tags=("distributed-training",)),
    "I": Section("mlops"),
    "J": Section("cloud-devops"),
    "K": Section("rag"),
    "L": Section("rag", tags=("banking", "enterprise")),
    "M": Section("llm"),
    "N": Section("agents"),
    "O": Section("system-design"),
    "P": Section("databases"),
    "Q": Section("time-series"),
    "R": Section("computer-vision", project="cricket-biomechanics"),
    "S": Section("backend"),
    "T": Section("backend", project="vissoo"),
    "U": Section("unassigned", project="snapstand"),  # mobile + on-device CV + backend
    "V": Section("rag", project="methaneguard"),
    "W": Section("behavioral", tags=("fde",)),
    "X": Section("unassigned"),  # rapid-fire comparisons across every domain
}

PROJECTS = [
    {"id": "image-editing-pipeline", "name": "AI image-editing pipeline"},
    {"id": "cricket-biomechanics", "name": "Cricket biomechanics"},
    {"id": "vissoo", "name": "Vissoo"},
    {"id": "snapstand", "name": "SnapStand"},
    {"id": "methaneguard", "name": "MethaneGuard"},
]

_SECTION = re.compile(r"^([A-Z])\. (.+)$")
_ITEM = re.compile(r"^(\d+)\. (.+)$")


@dataclass(frozen=True)
class Parsed:
    number: int
    section: str
    text: str


def parse_master_list(text: str) -> list[Parsed]:
    """Read the numbered questions of Part 1. Everything from 'PART 2' onwards is ignored."""
    lines = text.splitlines()
    end = next((i for i, line in enumerate(lines) if line.startswith("PART 2")), len(lines))
    section = None
    parsed: list[Parsed] = []
    for i, raw in enumerate(lines[:end]):
        line = raw.strip()
        header = _SECTION.match(line)
        if header and i > 0 and lines[i - 1].startswith("===="):
            section = header.group(1)
            continue
        item = _ITEM.match(line)
        if item:
            if section is None:
                raise ValueError(f"line {i + 1}: question found before any section header")
            parsed.append(Parsed(int(item.group(1)), section, item.group(2).strip()))
    if [p.number for p in parsed] != list(range(1, len(parsed) + 1)):
        raise ValueError("question numbers are not contiguous from 1; fix the source list first")
    unmapped = {p.section for p in parsed} - SECTIONS.keys()
    if unmapped:
        raise ValueError(f"no domain mapping for section(s): {', '.join(sorted(unmapped))}")
    return parsed


def _record(parsed: Parsed, duplicate_of: str | None) -> dict:
    spec = SECTIONS[parsed.section]
    record = {"id": f"q{parsed.number:04d}", "question": parsed.text}
    if duplicate_of:
        record["duplicate_of"] = duplicate_of
    record["domain"] = spec.domain
    record["archetype"] = classify(parsed.text, domain=spec.domain, project_scoped=spec.project is not None)
    if spec.project:
        record["project_ids"] = [spec.project]
    if spec.tags:
        record["tags"] = list(spec.tags)
    record["provenance"] = "unlabeled"
    record["status"] = "draft"
    return record


def build_records(parsed: list[Parsed]) -> list[dict]:
    """One record per question. Exact repeats point at a canonical copy but are never deleted."""
    first_pass = [_record(p, None) for p in parsed]
    duplicate_of: dict[str, str] = {}
    for group in exact_groups(first_pass):
        keeper = min(group, key=lambda r: r["id"])
        for record in group:
            if record is not keeper:
                duplicate_of[record["id"]] = keeper["id"]
    return [_record(p, duplicate_of.get(f"q{p.number:04d}")) for p in parsed]


def _print_summary(records: list[dict]) -> None:
    def counts(key: str) -> str:
        return ", ".join(f"{name} {n}" for name, n in Counter(r[key] for r in records).most_common())

    flagged = sum(1 for r in records if "duplicate_of" in r)
    print(f"{len(records)} questions, {flagged} flagged as exact duplicates")
    print(f"domain: {counts('domain')}")
    print(f"archetype: {counts('archetype')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="the master question list (.txt)")
    parser.add_argument("--output", type=Path, default=dataio.QUESTIONS_PATH)
    parser.add_argument("--projects-output", type=Path, default=dataio.PROJECTS_PATH)
    parser.add_argument("--dry-run", action="store_true", help="print a summary and write nothing")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output file")
    args = parser.parse_args(argv)

    records = build_records(parse_master_list(args.input.read_text(encoding="utf-8")))
    errors = validate_data(records, PROJECTS)
    if errors:
        print("Refusing to write invalid data:", *errors, sep="\n  - ")
        return 1
    _print_summary(records)
    if args.dry_run:
        return 0

    if args.output.exists() and not args.force:
        print(f"\n{args.output} already exists and may contain hand-made labels. Use --force to overwrite it.")
        return 1
    dataio.write_text(args.output, dataio.dump_questions(records))
    if not args.projects_output.exists():
        dataio.write_text(args.projects_output, dataio.dump_projects(PROJECTS))
    print(f"\nWrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
