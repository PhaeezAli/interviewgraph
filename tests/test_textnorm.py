from interviewgraph.textnorm import content_tokens, jaccard, normalize


def test_normalize_ignores_case_spacing_and_punctuation():
    assert normalize("MLE vs MAP.") == normalize("  mle  VS map ")


def test_normalize_folds_unicode():
    assert normalize("MODNet vs U²-Net.") == normalize("modnet vs u2-net")


def test_normalize_keeps_plus_and_hash_so_languages_stay_distinct():
    assert normalize("What is C++?") != normalize("What is C#?")


def test_content_tokens_drop_question_scaffolding():
    assert content_tokens("What is the GIL?") == frozenset({"gil"})


def test_jaccard():
    a = content_tokens("Threading vs multiprocessing in Python?")
    b = content_tokens("Threading vs multiprocessing vs asyncio?")
    assert jaccard(a, b) == 3 / 5
    assert jaccard(frozenset(), a) == 0.0
