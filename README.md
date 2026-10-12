# InterviewGraph

An open, structured interview-question knowledge base. The goal is to map job descriptions, roles, skills, concepts and real interview questions to evidence-based interview preparation.

*InterviewGraph is a working title.*

**Status: early.** The question dataset, its schema and its validation exist. The ontology, JD parser and question ranker do not yet. See the [roadmap](#roadmap).

## Principles

- **Data first.** The question bank is useful on its own, with or without the predictor.
- **Observed vs generated.** Every question records where it came from (`provenance`). Generated questions are never mixed in unlabelled.
- **No claims of certainty.** The aim is a ranked, explainable list with observed frequencies and sample sizes, not "these are the questions you will be asked".
- **Privacy.** No confidential or NDA-protected material, and no interviewer or candidate details. Companies are anonymised by default. Raw job descriptions and personal notes stay in `data/private/` (git-ignored) unless you decide to publish them.

## Quick start

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
uv run python -m interviewgraph validate     # schema + integrity checks, plus a labelling progress summary
uv run python -m interviewgraph duplicates   # flagged and near-duplicate questions to review
uv run pytest
```

Without uv: `python -m venv .venv && .venv/bin/pip install -e ".[dev]"`.

## Repository layout

```
data/questions/questions.yaml   the question bank (source of truth)
data/entities/projects.yaml     projects that questions can relate to
schema/                         JSON Schemas; editors that support them validate as you type
docs/data-model.md              field reference and conventions
interviewgraph/                 validation, duplicate detection, text utilities
scripts/import_master_list.py   one-shot migration from the original .txt list
tests/
```

## Adding or editing a question

Edit `data/questions/questions.yaml`. Use the next unused id (`q0819`, ...), never change or reuse an existing id, and run `validate`. The field reference is in [docs/data-model.md](docs/data-model.md).

## Roadmap

1. **Dataset** with stable ids, provenance and duplicate flags. *(this stage)*
2. **Interview records**: the job description plus the questions actually asked.
3. **Baseline retriever and evaluation**: hide one interview, predict its questions from the JD, measure how many appear in the top K.
4. **Ontology and graph**, judged against that baseline.
5. **Explainable ranking**, then an API and UI.

## License

Not chosen yet. Decide before the first public release.
