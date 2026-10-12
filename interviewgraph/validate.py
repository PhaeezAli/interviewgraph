"""Schema and integrity checks for the dataset."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field

from jsonschema import Draft202012Validator

from . import dataio
from .dedupe import exact_groups, near_pairs


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def schema_errors(instance, schema_file: str, label: str) -> list[str]:
    schema = json.loads((dataio.SCHEMA_DIR / schema_file).read_text(encoding="utf-8"))
    found = []
    for error in Draft202012Validator(schema).iter_errors(instance):
        path = list(error.absolute_path)
        index = path[0] if path and isinstance(path[0], int) else None
        where = label
        if index is not None:
            item = instance[index]
            where = f"{label}[{index}] ({item.get('id', '?') if isinstance(item, dict) else '?'})"
        field_path = ".".join(str(part) for part in path[1:])
        found.append((-1 if index is None else index, f"{where}{' ' + field_path if field_path else ''}: {error.message}"))
    return [message for _, message in sorted(found, key=lambda item: item[0])]


def integrity_errors(records: list[dict], project_ids: set[str]) -> list[str]:
    """Rules the JSON schema cannot express. Assumes the records are schema-valid."""
    errors = []
    for qid, count in Counter(r["id"] for r in records).items():
        if count > 1:
            errors.append(f"{qid}: id is used {count} times")
    by_id = {r["id"]: r for r in records}
    for record in records:
        qid = record["id"]
        target = record.get("duplicate_of")
        if target is not None:
            if target == qid:
                errors.append(f"{qid}: duplicate_of points at itself")
            elif target not in by_id:
                errors.append(f"{qid}: duplicate_of {target}, which does not exist")
            elif "duplicate_of" in by_id[target]:
                errors.append(f"{qid}: duplicate_of {target}, which is itself a duplicate; point at the canonical question")
        for project_id in record.get("project_ids", []):
            if project_id not in project_ids:
                errors.append(f"{qid}: unknown project '{project_id}' (add it to data/entities/projects.yaml)")
    canonical = [r for r in records if "duplicate_of" not in r]
    for group in exact_groups(canonical):
        ids = ", ".join(r["id"] for r in group)
        errors.append(f"{ids}: identical text and project scope; keep one and set duplicate_of on the others")
    return errors


def interview_errors(interviews: list[dict], records: list[dict]) -> list[str]:
    """Rules linking interview records to the question bank. Assumes both are schema-valid."""
    errors = []
    for iid, count in Counter(i["id"] for i in interviews).items():
        if count > 1:
            errors.append(f"{iid}: id is used {count} times")
    by_id = {r["id"]: r for r in records}
    for record in interviews:
        iid = record["id"]
        seen: Counter = Counter()
        for stage in record["stages"]:
            for qid in stage["question_ids"]:
                seen[qid] += 1
                question = by_id.get(qid)
                if question is None:
                    errors.append(f"{iid}: question {qid} does not exist")
                elif "duplicate_of" in question:
                    errors.append(f"{iid}: question {qid} is a duplicate of {question['duplicate_of']}; link the canonical question")
        for qid, n in seen.items():
            if n > 1:
                errors.append(f"{iid}: question {qid} is listed in more than one round")
    return errors


def validate_data(records, projects, interviews=None) -> list[str]:
    interviews = list(interviews or [])
    errors = schema_errors(records, "question.schema.json", "questions")
    errors += schema_errors(projects, "project.schema.json", "projects")
    errors += schema_errors(interviews, "interview.schema.json", "interviews")
    if errors:
        return errors + ["(integrity checks skipped until the schema errors above are fixed)"]
    errors = [f"projects: id '{pid}' is used more than once" for pid, n in Counter(p["id"] for p in projects).items() if n > 1]
    errors += integrity_errors(records, {p["id"] for p in projects})
    return errors + interview_errors(interviews, records)


def summarize(records: list[dict], interviews: list[dict] | None = None) -> list[str]:
    canonical = [r for r in records if "duplicate_of" not in r]
    interviews = list(interviews or [])

    def counts(key: str) -> str:
        return ", ".join(f"{name} {n}" for name, n in Counter(r[key] for r in records).most_common())

    unassigned = sum(1 for r in records if r["domain"] == "unassigned")
    return [
        f"{len(records)} questions: {len(canonical)} canonical, {len(records) - len(canonical)} flagged as duplicates",
        f"provenance: {counts('provenance')}",
        f"status: {counts('status')}",
        f"domain still unassigned: {unassigned}",
        f"archetypes: {counts('archetype')}",
        f"near-duplicate pairs awaiting review: {len(near_pairs(records))} (run: python -m interviewgraph duplicates)",
        _interview_summary(interviews),
    ]


def _interview_summary(interviews: list[dict]) -> str:
    if not interviews:
        return "interviews recorded: 0 (add the first one to data/interviews/interviews.yaml)"
    linked = {qid for i in interviews for stage in i["stages"] for qid in stage["question_ids"]}
    rounds = sum(len(i["stages"]) for i in interviews)
    families = ", ".join(f"{name} {n}" for name, n in Counter(i["role_family"] for i in interviews).most_common())
    return f"interviews recorded: {len(interviews)} ({rounds} rounds, {len(linked)} distinct questions linked); roles: {families}"


def validate_repo() -> Report:
    missing = [p for p in (dataio.QUESTIONS_PATH, dataio.PROJECTS_PATH) if not p.exists()]
    if missing:
        return Report(errors=[f"{p.relative_to(dataio.ROOT)} not found" for p in missing])
    records = dataio.load_yaml(dataio.QUESTIONS_PATH)
    projects = dataio.load_yaml(dataio.PROJECTS_PATH)
    interviews = dataio.load_interviews()
    errors = validate_data(records, projects, interviews)
    return Report(errors=errors, summary=[] if errors else summarize(records, interviews))
