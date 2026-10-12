"""Text normalisation shared by duplicate detection and, later, retrieval."""

from __future__ import annotations

import re
import unicodedata

# '+' and '#' survive so that "C++" and "C#" do not collapse into the same token.
_NON_WORD = re.compile(r"[^a-z0-9+#]+")

# Words that carry no topical signal in an interview question. Used only when
# comparing questions for similarity, never for exact-duplicate detection.
STOPWORDS = frozenset(
    "what is are the a an of to in and does do you how would why when your can with for it on by".split()
)


def normalize(text: str) -> str:
    """Lower-case, fold unicode and collapse punctuation so trivial variants compare equal."""
    folded = unicodedata.normalize("NFKC", text).lower()
    return _NON_WORD.sub(" ", folded).strip()


def content_tokens(text: str) -> frozenset[str]:
    return frozenset(t for t in normalize(text).split() if t not in STOPWORDS)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
