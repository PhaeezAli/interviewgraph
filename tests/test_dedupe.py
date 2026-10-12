from interviewgraph.dedupe import exact_groups, near_pairs


def rec(qid, question, **extra):
    return {"id": qid, "question": question, **extra}


def test_identical_text_in_the_same_scope_is_an_exact_group():
    records = [rec("q0001", "Why use warmup?"), rec("q0002", "why use warmup")]
    assert [[r["id"] for r in group] for group in exact_groups(records)] == [["q0001", "q0002"]]


def test_same_wording_about_different_projects_is_not_a_duplicate():
    records = [
        rec("q0001", "Why PostgreSQL?", project_ids=["vissoo"]),
        rec("q0002", "Why PostgreSQL?", project_ids=["methaneguard"]),
    ]
    assert exact_groups(records) == []


def test_near_pairs_finds_similar_questions_and_skips_exact_and_flagged_ones():
    records = [
        rec("q0001", "Threading vs multiprocessing in Python?"),
        rec("q0002", "Threading vs multiprocessing vs asyncio?"),
        rec("q0003", "What is the GIL?"),
        rec("q0004", "What is the GIL?", duplicate_of="q0003"),
    ]
    pairs = near_pairs(records, threshold=0.5)
    assert [(a["id"], b["id"]) for _, a, b in pairs] == [("q0001", "q0002")]


def test_near_pairs_do_not_compare_across_project_scopes():
    records = [
        rec("q0001", "How do you handle occlusion?"),
        rec("q0002", "How do you handle occlusion?!", project_ids=["cricket-biomechanics"]),
    ]
    assert near_pairs(records, threshold=0.5) == []
