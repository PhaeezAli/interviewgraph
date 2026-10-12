import shutil

from interviewgraph import dataio
from interviewgraph.__main__ import main


def test_validate_exits_zero_on_the_committed_data(capsys):
    assert main(["validate"]) == 0
    assert "questions:" in capsys.readouterr().out


def test_validate_exits_nonzero_and_names_the_problem(tmp_path, monkeypatch, capsys):
    broken = tmp_path / "questions.yaml"
    shutil.copy(dataio.QUESTIONS_PATH, broken)
    broken.write_text(broken.read_text(encoding="utf-8").replace("domain: python", "domain: pythonn", 1), encoding="utf-8")
    monkeypatch.setattr(dataio, "QUESTIONS_PATH", broken)
    assert main(["validate"]) == 1
    out = capsys.readouterr().out
    assert "problem(s) found" in out and "pythonn" in out


def test_duplicates_lists_flagged_and_similar_questions(capsys):
    assert main(["duplicates"]) == 0
    out = capsys.readouterr().out
    assert "Flagged as duplicates" in out
    assert "Similar but not identical" in out
