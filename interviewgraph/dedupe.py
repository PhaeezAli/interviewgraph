"""Duplicate detection over question records."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from .textnorm import content_tokens, jaccard, normalize

DEFAULT_THRESHOLD = 0.7


def _scope(record: dict) -> tuple[str, ...]:
    return tuple(sorted(record.get("project_ids", [])))


def exact_groups(records: list[dict]) -> list[list[dict]]:
    """Groups of two or more records with identical normalised text and the same project scope.

    The same wording asked about two different projects ("Why PostgreSQL?" for Vissoo and for
    MethaneGuard) is two questions, not a duplicate.
    """
    by_identity: dict[tuple, list[dict]] = defaultdict(list)
    for record in records:
        by_identity[(normalize(record["question"]), _scope(record))].append(record)
    return [group for group in by_identity.values() if len(group) > 1]


def near_pairs(records: list[dict], threshold: float = DEFAULT_THRESHOLD) -> list[tuple[float, dict, dict]]:
    """Similar-but-not-identical pairs among canonical (non-flagged) records, most similar first.

    Only records with the same project scope are compared: a general question and its
    project-specific version are related, but deliberately kept apart.
    """
    canonical = [r for r in records if "duplicate_of" not in r]
    prepared = [(r, normalize(r["question"]), content_tokens(r["question"])) for r in canonical]
    pairs = []
    for (a, text_a, tokens_a), (b, text_b, tokens_b) in combinations(prepared, 2):
        if _scope(a) != _scope(b) or text_a == text_b:
            continue  # different scope: not a duplicate; identical text and scope: reported as exact
        score = jaccard(tokens_a, tokens_b)
        if score >= threshold:
            pairs.append((score, a, b))
    pairs.sort(key=lambda p: (-p[0], p[1]["id"], p[2]["id"]))
    return pairs
