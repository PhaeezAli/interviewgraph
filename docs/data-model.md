# Data model

The question bank is plain YAML that people edit by hand. Two things keep it consistent: the JSON Schemas in `schema/` (shape and allowed values) and `python -m interviewgraph validate` (the schemas plus the integrity rules below). Run `validate` before every commit.

## Files

| File | Contents |
|---|---|
| `data/questions/questions.yaml` | The question bank: a list of question records. Source of truth. |
| `data/entities/projects.yaml` | Projects that questions can relate to. |

## Question record

```yaml
- id: q0624
  question: "Why PostgreSQL?"
  domain: backend
  archetype: why-choice
  project_ids: [vissoo]
  provenance: unlabeled
  status: draft
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `q` plus at least four digits. Assigned once; never changed, never reused. |
| `question` | yes | The question as it was asked or recalled. |
| `duplicate_of` | no | Points at the canonical question when this record repeats it. |
| `domain` | yes | Coarse topic area (see below). `unassigned` means it needs a label. |
| `archetype` | yes | The shape of the question (see below). |
| `project_ids` | no | Projects from `projects.yaml` that the question relates to. |
| `tags` | no | Free-form context labels such as `banking` or `fde`. |
| `provenance` | yes | Where the question came from (see below). |
| `status` | yes | `draft`: labels not checked by a person. `reviewed`: checked. |

Unknown fields are rejected, so a typo is caught instead of silently ignored.

## Conventions

**IDs.** The questions imported from the original master list keep their list numbers: `q0435` is item 435. New questions take the next unused number. Never renumber, because other files will refer to these ids.

**Duplicates are flagged, not deleted.** Two records are duplicates when the wording is identical (ignoring case, punctuation and unicode) *and* they have the same `project_ids`. Keep both records, set `duplicate_of` on the later one, and point it at the canonical copy, which must not itself be a duplicate. The same wording asked about two different projects ("Why PostgreSQL?" for Vissoo and for MethaneGuard) is two questions. Once interviews are recorded, a repeated question becomes a frequency signal instead of clutter.

`python -m interviewgraph duplicates` also lists pairs that are similar but not identical. Those need a human decision: merge them with `duplicate_of`, or keep them as separate variants.

**Draft labels.** `domain`, `archetype`, `project_ids` and `tags` in the imported data come from section-level defaults and wording rules, not from a person reading each question. Every record therefore starts as `status: draft`. Sections that mix several domains are left `domain: unassigned` instead of guessed. If a label is wrong, change it and set `status: reviewed`.

## Domains

| Value | Covers |
|---|---|
| `behavioral` | Introductions, experience, motivation, conflict, customer-facing scenarios |
| `python` | The language and its runtime |
| `statistics` | Statistics and probability |
| `machine-learning` | Classical ML, evaluation, tabular modelling |
| `deep-learning` | Neural networks, training, distributed training |
| `computer-vision` | Detection, segmentation, matting, pose |
| `mlops` | Serving, deployment and monitoring of models |
| `cloud-devops` | Docker, Kubernetes, cloud |
| `rag` | Retrieval, embeddings, vector search, enterprise RAG |
| `llm` | Transformers and LLM concepts |
| `agents` | Agents, tool calling, MCP |
| `system-design` | Architecture and scaling |
| `databases` | SQL and data stores |
| `time-series` | Forecasting |
| `backend` | APIs, auth, storage, web services |
| `unassigned` | Not labelled yet |

## Archetypes

The archetype is the shape of the question, that is, how the interviewer is probing. It generalises across candidates better than the exact wording does.

| Value | Example |
|---|---|
| `concept` | "What is the GIL?" |
| `comparison` | "Threading vs multiprocessing." |
| `applied` | "How do you handle class imbalance?" |
| `design` | "Design a production RAG platform." |
| `coding` | "Find the second-highest salary." |
| `why-choice` | "Why PostgreSQL?" (justify a decision) |
| `walkthrough` | "Walk me through your resume." / "Explain X end-to-end." |
| `behavioral` | "Tell me about a production failure." |
| `other` | Anything that fits none of the above |

## Provenance

| Value | Meaning |
|---|---|
| `unlabeled` | Nobody has checked yet. Everything imported starts here. |
| `asked` | An interviewer asked it in a real interview. |
| `prep` | From preparation material; not confirmed as asked. |
| `followup` | A natural follow-up someone derived. |
| `generated` | Machine-generated. |
| `community` | Submitted by a contributor. |

Interview records (the job description plus the questions actually asked) are the next stage. When they exist they will be the source of truth for which interview asked what, and observed frequencies will be counted from them rather than stored on the question.
