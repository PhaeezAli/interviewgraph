import importlib.util
import json
import sys
from pathlib import Path

import pytest

from interviewgraph import dataio
from interviewgraph.validate import validate_data

_path = Path(__file__).resolve().parent.parent / "scripts" / "import_master_list.py"
_spec = importlib.util.spec_from_file_location("import_master_list", _path)
importer = importlib.util.module_from_spec(_spec)
sys.modules["import_master_list"] = importer  # dataclasses resolves annotations through sys.modules
_spec.loader.exec_module(importer)

SAMPLE = """\
PART 1 - MASTER LIST

============================================================
A. INTRODUCTION
============================================================

1. Tell me about yourself.

============================================================
K. RAG
============================================================

2. What is RAG?
3. Explain HNSW.

============================================================
X. RAPID-FIRE
============================================================

4. What is RAG?

PART 2 - DESIGN
9. Ignored: it comes after PART 2.
"""


def _build():
    return importer.build_records(importer.parse_master_list(SAMPLE))


def test_parses_numbered_questions_and_ignores_part_two():
    parsed = importer.parse_master_list(SAMPLE)
    assert [(p.number, p.section) for p in parsed] == [(1, "A"), (2, "K"), (3, "K"), (4, "X")]


def test_gaps_in_numbering_are_rejected():
    with pytest.raises(ValueError, match="contiguous"):
        importer.parse_master_list(SAMPLE.replace("3. Explain HNSW.", "5. Explain HNSW."))


def test_unknown_section_is_rejected():
    with pytest.raises(ValueError, match="no domain mapping"):
        importer.parse_master_list(SAMPLE.replace("K. RAG", "Z. RAG"))


def test_records_get_stable_ids_and_draft_labels():
    records = _build()
    assert [r["id"] for r in records] == ["q0001", "q0002", "q0003", "q0004"]
    first = records[0]
    assert (first["domain"], first["archetype"], first["provenance"], first["status"]) == (
        "behavioral",
        "walkthrough",
        "unlabeled",
        "draft",
    )


def test_exact_repeats_point_at_the_first_copy_and_are_kept():
    records = _build()
    assert len(records) == 4
    assert records[3]["duplicate_of"] == "q0002"
    assert "duplicate_of" not in records[1]


def test_built_records_pass_validation():
    assert validate_data(_build(), importer.PROJECTS) == []


def test_section_domains_and_projects_exist_in_the_schema_and_project_list():
    schema = json.loads((dataio.SCHEMA_DIR / "question.schema.json").read_text(encoding="utf-8"))
    allowed = set(schema["$defs"]["question"]["properties"]["domain"]["enum"])
    assert {s.domain for s in importer.SECTIONS.values()} <= allowed
    assert {s.project for s in importer.SECTIONS.values() if s.project} <= {p["id"] for p in importer.PROJECTS}


def _run(tmp_path, *flags):
    source = tmp_path / "list.txt"
    source.write_text(SAMPLE, encoding="utf-8")
    out, projects = tmp_path / "questions.yaml", tmp_path / "projects.yaml"
    code = importer.main([str(source), "--output", str(out), "--projects-output", str(projects), *flags])
    return code, out, projects


def test_dry_run_writes_nothing(tmp_path):
    code, out, projects = _run(tmp_path, "--dry-run")
    assert code == 0
    assert not out.exists() and not projects.exists()


def test_written_files_load_back_to_the_same_records(tmp_path):
    code, out, projects = _run(tmp_path)
    assert code == 0
    assert dataio.load_yaml(out) == _build()
    assert validate_data(dataio.load_yaml(out), dataio.load_yaml(projects)) == []


def test_refuses_to_overwrite_hand_edited_data(tmp_path):
    out = tmp_path / "questions.yaml"
    out.write_text("hand-made labels", encoding="utf-8")
    code, _, _ = _run(tmp_path)
    assert code == 1
    assert out.read_text(encoding="utf-8") == "hand-made labels"
    code, _, _ = _run(tmp_path, "--force")
    assert code == 0
