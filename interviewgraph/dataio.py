"""Reading and writing the YAML data files with stable, review-friendly formatting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT / "data" / "questions" / "questions.yaml"
PROJECTS_PATH = ROOT / "data" / "entities" / "projects.yaml"
SCHEMA_DIR = ROOT / "schema"

QUESTIONS_HEADER = (
    "# yaml-language-server: $schema=../../schema/question.schema.json\n"
    "# Canonical question bank. Edit by hand, then run: python -m interviewgraph validate\n"
    "# Field reference: docs/data-model.md\n"
)
PROJECTS_HEADER = (
    "# yaml-language-server: $schema=../../schema/project.schema.json\n"
    "# Projects that questions can relate to (project_ids in questions.yaml).\n"
)


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate keys instead of silently keeping the last one."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                is_duplicate = key in seen
            except TypeError:  # unhashable key; the parent class reports it
                continue
            if is_duplicate:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key: {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


class _Quoted(str):
    """A string written as a double-quoted YAML scalar."""


class _Flow(list):
    """A list written in YAML flow style: [a, b]."""


class _Dumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)  # indent list items under their key


_Dumper.add_representer(_Quoted, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", str(v), style='"'))
_Dumper.add_representer(_Flow, lambda d, v: d.represent_sequence("tag:yaml.org,2002:seq", list(v), flow_style=True))


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_StrictLoader)


def _dump(items: list[dict]) -> str:
    body = yaml.dump(items, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=10_000)
    return body.replace("\n- ", "\n\n- ")  # blank line between records


def dump_questions(records: list[dict]) -> str:
    prepared = []
    for record in records:
        record = dict(record)
        record["question"] = _Quoted(record["question"])
        for key in ("project_ids", "tags"):
            if key in record:
                record[key] = _Flow(record[key])
        prepared.append(record)
    return QUESTIONS_HEADER + "\n" + _dump(prepared)


def dump_projects(projects: list[dict]) -> str:
    return PROJECTS_HEADER + "\n" + _dump(projects)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
