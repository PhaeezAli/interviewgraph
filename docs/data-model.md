# Data model

The question bank is plain YAML that people edit by hand. Two things keep it consistent: the JSON Schemas in `schema/` (shape and allowed values) and `python -m interviewgraph validate` (the schemas plus the integrity rules below). Run `validate` before every commit.

## Files

| File | Contents |
|---|---|
| `data/questions/questions.yaml` | The question bank: a list of question records. Source of truth. |
| `data/entities/projects.yaml` | Projects that questions can relate to. |
| `data/interviews/interviews.yaml` | Interview records: which role asked which questions. |
| `data/private/` | Raw postings and personal notes. Git-ignored; never published. |

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

## Interview record

One record per application: the role, the company (anonymised unless you say otherwise), the rounds, and the questions asked in each round. Interview records are the source of truth for *which interview asked what*. Observed frequencies ("asked in 5 of 7 FDE interviews") are counted from them, never stored on the question.

```yaml
- id: i0001
  company: fintech-a
  company_named: false
  industry: fintech
  company_size: scaleup
  role_title: Forward Deployed AI Engineer
  role_family: fde
  seniority: mid
  location: Dubai, UAE
  date: 2026-03
  jd_skills: [python, llm, rag, agents, fastapi]
  jd_summary: Customer-facing engineer building LLM agents on top of the company's banking data platform.
  jd_ref: data/private/jd/i0001-fintech-a.txt
  stages:
    - kind: screening
      format: phone
      duration_minutes: 30
      question_ids: [q0001, q0004]
    - kind: technical
      format: video
      duration_minutes: 60
      question_ids: [q0435, q0441, q0612]
  outcome: rejected
  source: self
  status: draft
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `i` plus at least four digits. Assigned once; never changed, never reused. |
| `company` | yes | The employer, or an anonymised label such as `fintech-a` when `company_named` is false. |
| `company_named` | yes | `true` only when the real name may be published. Default to `false`. |
| `industry` | no | Slug such as `fintech`, `media`, `government`. Carries signal even when the company is anonymised. |
| `company_size` | no | `startup`, `scaleup` or `enterprise`. |
| `role_title` | yes | The title as the posting wrote it. |
| `role_family` | yes | Normalised role (see below) so different titles can be compared. |
| `seniority` | no | `intern`, `junior`, `mid`, `senior` or `lead`, as the posting framed it. |
| `location` | no | City and country, or `remote`. |
| `date` | yes | Month of the first round, `YYYY-MM`. Day-level dates could identify people. |
| `jd_skills` | no | Slugs for what the posting asked for. This is the public, reusable summary of the JD and the main input to the ranker. |
| `jd_summary` | no | Two or three sentences in your own words. Never paste the posting. |
| `jd_ref` | no | Path under `data/private/` to the raw posting on your machine. |
| `stages` | yes | The rounds in order. Each has a `kind`, optional `format` and `duration_minutes`, and `question_ids`. |
| `outcome` | no | `offer`, `rejected`, `withdrew`, `no-response` or `in-progress`. |
| `source` | yes | `self` for the maintainer's own interviews, `community` for contributed ones. |
| `status` | yes | `draft` until a person has checked the record and its question links. |

**Rules `validate` enforces.** Every `question_ids` entry must exist in `questions.yaml` and be canonical (not a `duplicate_of` record). A question appears at most once per interview, even across rounds. Unknown fields are rejected, so personal notes cannot slip in.

**Role families:** `ai-engineer`, `ml-engineer`, `fde`, `computer-vision`, `data-scientist`, `mlops`, `backend`, `full-stack`, `data-engineer`, `research`, `other`.

**Stage kinds:** `screening`, `technical`, `coding`, `system-design`, `take-home`, `hiring-manager`, `behavioral`, `final`, `other`.

**Privacy.** No interviewer names, no candidate names, no day-level dates, no pasted postings, no personal notes. Companies are anonymised by default; set `company_named: true` only when the name is already public knowledge for that role or the company has no objection. Questions covered by an NDA must not be recorded.

**Recording a question that is new to the bank.** Add it to `questions.yaml` first with `provenance: asked`, then link its id here.
