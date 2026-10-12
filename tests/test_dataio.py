import pytest
import yaml

from interviewgraph import dataio


def test_dump_then_load_round_trips_awkward_text():
    records = [
        {
            "id": "q0001",
            "question": "Explain \"Bayes' theorem\": why? #1 - MODNet vs U²-Net – ok",
            "domain": "statistics",
            "archetype": "concept",
            "project_ids": ["vissoo"],
            "tags": ["banking", "enterprise"],
            "provenance": "unlabeled",
            "status": "draft",
        },
        {
            "id": "q0002",
            "question": "yes",
            "duplicate_of": "q0001",
            "domain": "python",
            "archetype": "other",
            "provenance": "unlabeled",
            "status": "draft",
        },
    ]
    text = dataio.dump_questions(records)
    assert yaml.safe_load(text) == records
    assert "project_ids: [vissoo]" in text
    assert 'question: "yes"' in text
    assert "U²-Net – ok" in text  # non-ASCII stays readable


def test_duplicate_keys_are_rejected(tmp_path):
    path = tmp_path / "questions.yaml"
    path.write_text("- id: q0001\n  status: draft\n  status: reviewed\n", encoding="utf-8")
    with pytest.raises(yaml.YAMLError, match="duplicate key"):
        dataio.load_yaml(path)
