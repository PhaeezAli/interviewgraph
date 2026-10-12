import pytest

from interviewgraph.archetype import ARCHETYPES, classify

# (question, domain, belongs to one of the maintainer's projects, expected archetype)
CASES = [
    ("What is the GIL?", "python", False, "concept"),
    ("Explain Bayes' theorem.", "statistics", False, "concept"),
    ("What assumptions does a t-test make?", "statistics", False, "concept"),
    ("Why does dropout reduce overfitting?", "deep-learning", False, "concept"),
    ("Why use warmup?", "deep-learning", False, "concept"),
    ("What happens during an all-reduce operation?", "deep-learning", False, "concept"),
    ("Explain an end-to-end RAG pipeline.", "rag", False, "concept"),
    ("Why can alpha mattes contain gradients?", "computer-vision", True, "concept"),
    ("Type I vs Type II error.", "statistics", False, "comparison"),
    ("Why use RAG instead of fine-tuning?", "rag", False, "comparison"),
    ("When would you use rules instead of ML?", "behavioral", False, "comparison"),
    ("How do you handle class imbalance?", "machine-learning", False, "applied"),
    ("What happens if one worker crashes?", "deep-learning", False, "applied"),
    ("When is MAPE problematic?", "time-series", False, "applied"),
    ("What embedding model did you use?", "rag", True, "applied"),
    ("Design ChatGPT.", "system-design", False, "design"),
    ("How would you design multi-tenancy?", "system-design", False, "design"),
    ("Find the second-highest salary.", "databases", False, "coding"),
    ("Write a query for the top 5 regions by average claim amount.", "databases", False, "coding"),
    ("Tell me about a production failure.", "behavioral", False, "behavioral"),
    ("Why should we hire you?", "behavioral", False, "behavioral"),
    ("Tell me about yourself.", "behavioral", False, "walkthrough"),
    ("Walk me through your resume.", "behavioral", False, "walkthrough"),
    ("Explain Vissoo end-to-end.", "backend", True, "walkthrough"),
    ("Why PostgreSQL?", "backend", True, "why-choice"),
    ("Why did you use MODNet?", "computer-vision", True, "why-choice"),
]


@pytest.mark.parametrize(("question", "domain", "project_scoped", "expected"), CASES)
def test_classify(question, domain, project_scoped, expected):
    assert classify(question, domain=domain, project_scoped=project_scoped) == expected


def test_unrecognised_wording_falls_back_to_other():
    assert classify("Cricket ball spin?", domain="computer-vision") == "other"


def test_every_result_is_a_known_archetype():
    for question, domain, project_scoped, _ in CASES:
        assert classify(question, domain=domain, project_scoped=project_scoped) in ARCHETYPES
