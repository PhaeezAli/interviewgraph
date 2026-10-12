import yaml

from interviewgraph import dataio
from interviewgraph.validate import validate_data

PROJECTS = [{"id": "vissoo", "name": "Vissoo"}]


def q(qid, text, **extra):
    base = {"id": qid, "question": text, "domain": "python", "archetype": "concept", "provenance": "unlabeled", "status": "draft"}
    return {**base, **extra}


QUESTIONS = [q("q0001", "What is the GIL?"), q("q0002", "What is a decorator?"), q("q0003", "GIL?", duplicate_of="q0001")]


def interview(iid="i0001", **extra):
    base = {
        "id": iid,
        "company": "fintech-a",
        "company_named": False,
        "role_title": "Forward Deployed AI Engineer",
        "role_family": "fde",
        "date": "2026-03",
        "stages": [{"kind": "technical", "format": "video", "question_ids": ["q0001", "q0002"]}],
        "source": "self",
        "status": "draft",
    }
    return {**base, **extra}


def errors_for(*interviews):
    return validate_data(QUESTIONS, PROJECTS, list(interviews))


def test_a_clean_record_passes():
    assert errors_for(interview()) == []


def test_no_interviews_is_fine():
    assert validate_data(QUESTIONS, PROJECTS) == []
    assert validate_data(QUESTIONS, PROJECTS, []) == []


def test_schema_rejects_bad_dates_unknown_fields_and_unknown_stage_kinds():
    text = "\n".join(
        errors_for(
            interview("i0001", date="2026-3"),
            interview("i0002", notes="personal notes do not belong here"),
            interview("i0003", stages=[{"kind": "lunch", "question_ids": []}]),
        )
    )
    assert "interviews[0] (i0001) date" in text
    assert "interviews[1] (i0002)" in text and "notes" in text
    assert "interviews[2] (i0003) stages.0.kind" in text


def test_jd_ref_must_point_inside_the_private_folder():
    text = "\n".join(errors_for(interview(jd_ref="data/interviews/posting.txt")))
    assert "jd_ref" in text


def test_repeated_interview_ids_are_reported():
    assert "i0001: id is used 2 times" in errors_for(interview(), interview())


def test_questions_must_exist_and_be_canonical():
    record = interview(stages=[{"kind": "technical", "question_ids": ["q0001", "q0999", "q0003"]}])
    text = "\n".join(errors_for(record))
    assert "i0001: question q0999 does not exist" in text
    assert "i0001: question q0003 is a duplicate of q0001; link the canonical question" in text


def test_the_same_question_cannot_be_listed_in_two_rounds():
    record = interview(
        stages=[
            {"kind": "screening", "question_ids": ["q0001"]},
            {"kind": "technical", "question_ids": ["q0001", "q0002"]},
        ]
    )
    assert "i0001: question q0001 is listed in more than one round" in errors_for(record)


def test_dump_then_load_round_trips():
    records = [interview(jd_skills=["python", "rag"], outcome="rejected")]
    text = dataio.dump_interviews(records)
    assert yaml.safe_load(text) == records
    assert "jd_skills: [python, rag]" in text
    assert "question_ids: [q0001, q0002]" in text


def test_committed_interviews_file_loads_as_a_list():
    assert isinstance(dataio.load_interviews(), list)
