import json

from interviewgraph import dataio
from interviewgraph.archetype import ARCHETYPES
from interviewgraph.validate import validate_data, validate_repo

PROJECTS = [{"id": "vissoo", "name": "Vissoo"}]


def rec(qid, question, **extra):
    base = {
        "id": qid,
        "question": question,
        "domain": "python",
        "archetype": "concept",
        "provenance": "unlabeled",
        "status": "draft",
    }
    return {**base, **extra}


def test_committed_dataset_is_valid():
    report = validate_repo()
    assert report.errors == []
    assert report.summary


def test_clean_records_pass():
    assert validate_data([rec("q0001", "What is the GIL?"), rec("q0002", "What is a decorator?")], PROJECTS) == []


def test_schema_rejects_unknown_values_missing_fields_and_typos():
    bad = [
        rec("q0001", "What is the GIL?", domain="pythonn"),
        {"id": "q0002", "question": "Missing fields"},
        rec("q0003", "Typo in a field name", statuss="draft"),
    ]
    errors = validate_data(bad, PROJECTS)
    text = "\n".join(errors)
    assert "questions[0] (q0001) domain" in text
    assert "questions[1] (q0002)" in text and "required" in text
    assert "questions[2] (q0003)" in text and "statuss" in text
    assert errors[-1].startswith("(integrity checks skipped")


def test_ids_must_look_like_ids():
    assert any("does not match" in e for e in validate_data([rec("Q1", "What is the GIL?")], PROJECTS))


def test_repeated_ids_are_reported():
    errors = validate_data([rec("q0001", "One?"), rec("q0001", "Two?")], PROJECTS)
    assert "q0001: id is used 2 times" in errors


def test_duplicate_of_must_point_at_an_existing_canonical_question():
    records = [
        rec("q0001", "What is the GIL?"),
        rec("q0002", "GIL?", duplicate_of="q0001"),
        rec("q0003", "The GIL", duplicate_of="q0002"),
        rec("q0004", "Global lock", duplicate_of="q0999"),
        rec("q0005", "Itself", duplicate_of="q0005"),
    ]
    text = "\n".join(validate_data(records, PROJECTS))
    assert "q0003: duplicate_of q0002, which is itself a duplicate" in text
    assert "q0004: duplicate_of q0999, which does not exist" in text
    assert "q0005: duplicate_of points at itself" in text


def test_unknown_project_is_reported():
    errors = validate_data([rec("q0001", "Why Prisma?", project_ids=["nope"])], PROJECTS)
    assert any("unknown project 'nope'" in e for e in errors)


def test_unflagged_exact_duplicates_are_reported():
    errors = validate_data([rec("q0001", "What is the GIL?"), rec("q0002", "what is the GIL")], PROJECTS)
    assert any(e.startswith("q0001, q0002: identical text") for e in errors)


def test_flagged_duplicates_are_fine():
    records = [rec("q0001", "What is the GIL?"), rec("q0002", "what is the GIL", duplicate_of="q0001")]
    assert validate_data(records, PROJECTS) == []


def test_same_text_under_different_projects_is_allowed():
    projects = PROJECTS + [{"id": "methaneguard", "name": "MethaneGuard"}]
    records = [
        rec("q0001", "Why PostgreSQL?", project_ids=["vissoo"]),
        rec("q0002", "Why PostgreSQL?", project_ids=["methaneguard"]),
    ]
    assert validate_data(records, projects) == []


def test_repeated_project_ids_are_reported():
    errors = validate_data([], PROJECTS + PROJECTS)
    assert "projects: id 'vissoo' is used more than once" in errors


def test_schema_archetypes_match_the_code():
    schema = json.loads((dataio.SCHEMA_DIR / "question.schema.json").read_text(encoding="utf-8"))
    assert schema["$defs"]["question"]["properties"]["archetype"]["enum"] == list(ARCHETYPES)
