"""First-pass labelling of a question's *shape*: how the interviewer is probing.

Labels come from surface wording only, so they are drafts. Records keep
`status: draft` until a person has reviewed them.
"""

from __future__ import annotations

import re

ARCHETYPES = (
    "concept",  # define or explain a concept or mechanism
    "comparison",  # X vs Y, differences, X instead of Y
    "applied",  # how would / do / did you handle a technical situation
    "design",  # design a system
    "coding",  # write, query or implement something
    "why-choice",  # justify a decision ("Why PostgreSQL?")
    "walkthrough",  # walk me through your resume or a project
    "behavioral",  # past experience, soft skills, motivation
    "other",
)

# All patterns run against the lower-cased question; `.match` anchors at the start.
_CODING = re.compile(r"(write|implement|code|find)\b")
_DESIGN = re.compile(r"design\b|how (would|do|should) you design\b")
_INTRO = re.compile(r"(walk me through|tell me about yourself)\b")
_PROJECT_WALKTHROUGH = re.compile(
    r"explain\b.*\b(end-to-end|architecture|complete|your|backend|repository|pipeline|flow)\b"
)
_COMPARISON = re.compile(r"\bvs\b|\bversus\b|\binstead of\b|\bdifference between\b|\bdiffer from\b")
_WHY_MECHANISM = re.compile(r"why (does|do|can|is|are|should|shouldn't)\b")
_WHY_DECISION = re.compile(r"why (did|do|would) you\b")
_SCENARIO = re.compile(r"what happens (if|when)\b")
_APPLIED = re.compile(r"(how|where|what|which)\b.*\b(would|do|did|should|can|could) (you|we|i)\b|when\b")
_CONCEPT = re.compile(
    r"(what|which)\b|explain\b|how (does|do|is|are|can|did|should)\b|why\b|define\b"
    r"|(give|list|name)\b|(does|do|is|are|can|will|should)\b"
)


def classify(question: str, *, domain: str, project_scoped: bool = False) -> str:
    """Return one of ARCHETYPES for `question`.

    `domain` and `project_scoped` (does the question belong to one of the
    maintainer's own projects?) disambiguate wording that is shared between
    archetypes, e.g. "Why PostgreSQL?" versus "Why does dropout help?".
    """
    q = question.strip().lower()
    if _CODING.match(q):
        return "coding"
    if _DESIGN.match(q):
        return "design"
    if _INTRO.match(q) or (project_scoped and _PROJECT_WALKTHROUGH.match(q)):
        return "walkthrough"
    if _COMPARISON.search(q):
        return "comparison"
    if domain == "behavioral":
        return "behavioral"
    if q.startswith("why"):
        if _WHY_DECISION.match(q) or (project_scoped and not _WHY_MECHANISM.match(q)):
            return "why-choice"
        return "concept"
    if _SCENARIO.match(q) or _APPLIED.match(q):
        return "applied"
    if _CONCEPT.match(q):
        return "concept"
    return "other"
