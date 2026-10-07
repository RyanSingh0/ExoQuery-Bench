# ExoQuery-Bench: Project Scope

Working plan for building the benchmark, the systems under test, the chat demo and the write-up. The README holds the
public summary; this file holds the build plan, decisions and done-criteria.

## 1. Goal

Give the astronomy-archive community a reproducible answer to one question: *for natural-language questions to the
NASA Exoplanet Archive, which model, retrieval setup and tool design produce correct, faithful answers, at what cost,
and where do they fail?*

Success means: a public question set, a harness anyone can rerun, a leaderboard, an error taxonomy that maps to
fixes (for example "add `default_flag` guidance to the prompt"), and a chat demo that uses the best configuration.

## 2. Verified facts the design rests on (checked 2026-10-07)

Each fact was checked in at least three places: a live TAP query, the archive documentation, and a client library or
second source.

| Fact | Live query | Documentation | Third source |
|---|---|---|---|
| `ps` has 40,194 rows for 6,375 planets; `default_flag=1` gives 6,375 | TAP `count(*)` | Column docs: `default_flag` "selected as default (1=yes, 0=no)", PS only | PyVO `TAPService` returns 6,375 |
| `pscomppars` has one row per planet (6,375) | TAP `count(*)` | Column docs list it as the composite table | astroquery examples query it per planet |
| Values are case-sensitive (`'transit'` returns 0) | TAP | TAP guide: values are case-sensitive | `'Transit'` returns 4,711 |
| `LIMIT` fails, `TOP` works | TAP error vs rows | IVOA ADQL uses `SELECT TOP n` (GAVO ADQL 2.1 notes) | astroquery docs use `select="top 10 ..."` |
| `disc_method` works but is undocumented | TAP returns codes | Absent from column docs | Absent from `TAP_SCHEMA.columns` |
| R<sub>Jup</sub> = 11.21 R<sub>Earth</sub> | n/a | Column docs define `pl_rade` and `pl_radj` separately | `astropy.units` conversion |
| AstroFetch MCP exposes 10 tools over 3 archives | `tools/list`, `list_archives` | AstroFetch agents page | Exoplanet Archive news, 2026-10-01 |
| AstroFetch's top errors are columns and units | n/a | AstroFetch FAQ | n/a (single source, quoted as the FAQ's own claim) |

## 3. Components

### 3.1 Archive layer (`src/eqb/archive.py`)
- PyVO `TAPService` for sync queries, async jobs for anything large; astroquery as a cross-check.
- On-disk cache keyed by query text and archive snapshot date; global rate limit; retries with backoff.
- `snapshot_schema()` saves `TAP_SCHEMA.tables`, `TAP_SCHEMA.columns` and the column-docs page with a date stamp.

### 3.2 Question set (`data/questions/*.jsonl`)
- v0.1: 120 hand-written items; 20 seed items first.
- Target mix: 25% lookup and filter, 20% aggregation, 15% table choice and `default_flag`, 15% units, 10% joins and
  sky-position (`contains(point(...), circle(...))`), 10% TESS `toi` dispositions and spectra, 5% unanswerable.
- Difficulty easy / medium / hard; 2 paraphrases for 30 items to test wording robustness.
- Every gold query is executed and reviewed by hand before it is added; items carry tags for the trap they test.

### 3.3 Providers (`src/eqb/providers/`)
- Anthropic Claude, OpenAI, Google Gemini and an Ollama local model behind one `complete()` call, extended from the
  provider layer in [JudgeGuard](https://github.com/RyanSingh0/judgeguard).
- Structured output: one JSON schema (ADQL, tables, columns, units, assumptions, refusal flag), using each provider's
  native JSON or tool-calling mode, validated with Pydantic.
- Response cache so reruns and CI cost nothing.

### 3.4 Systems (`src/eqb/systems/`)
- **S0** direct prompt. **S1** curated schema in the prompt.
- **S2 RAG:** chunk column definitions, table notes and worked examples; hybrid retrieval (BM25 + embeddings) with
  top-k columns injected; log retrieved chunks for retrieval metrics.
- **S3 agent:** tools `search_schema`, `validate_adql`, `run_query`, `check_units`; step budget of 6; stops on a
  validated, executed answer.
- **S4 AstroFetch MCP:** an MCP client gives the model AstroFetch's own tools; throttled and cached.

### 3.5 Scoring (`src/eqb/scoring/`)
- Execution accuracy: run gold and candidate at the same time; compare as multisets with numeric tolerance; match
  columns by values, not names.
- Component metrics: table accuracy, column F1, `default_flag` correctness, unit check, valid-ADQL rate, refusal
  accuracy.
- LLM judge for answer faithfulness to returned rows; 60 items double-labelled by hand to report Cohen's kappa.
- Retrieval: recall@k and context precision for S2 and S3.
- Statistics: question-level bootstrap CIs; paired McNemar tests for system comparisons.

### 3.6 Error taxonomy
Automatic first-pass labels, hand-checked: wrong table, missing `default_flag`, wrong column, unit error,
case-sensitive value, SQL-not-ADQL syntax, undocumented column, wrong aggregation, timeout, hallucinated answer.

### 3.7 Leaderboard (`src/eqb/report/`)
- Static Bokeh page on GitHub Pages: accuracy by provider x system with CIs, cost-accuracy frontier, error taxonomy
  bars, per-question drill-down showing gold vs candidate ADQL.

### 3.8 Chat demo (`app/`)
- FastAPI back end with the best configuration; Gradio front end on Hugging Face Spaces.
- Shows the ADQL, retrieved documentation and unit warnings with every answer.
- Thumbs up/down with a comment; reviewed feedback becomes new benchmark items.

### 3.9 Engineering
- Python 3.11+, uv, ruff, mypy, pytest with Hypothesis for the result-set comparator.
- GitHub Actions: lint, tests, offline replay of cached runs, Docker build.
- MIT license; dataset card for the question set.

## 4. Phases and done-criteria

| Phase | Work | Done when |
|---|---|---|
| 0 | Repo, README, schema snapshot, 20 seed questions, comparator with tests | 20 gold queries run green in CI |
| 1 | Providers, S0 and S1, first table of results | All 4 providers scored on 20 questions with CIs |
| 2 | 120-question v0.1, S2 RAG, retrieval metrics | S2 vs S1 difference reported with a paired test |
| 3 | S3 agent, S4 MCP, error taxonomy | Every failure has a label; top-3 causes per system listed |
| 4 | Judge calibration, Bokeh leaderboard | Kappa reported; leaderboard live on GitHub Pages |
| 5 | Chat demo and feedback loop | Demo live; feedback stored and reviewable |
| 6 | IRSA and KOA extension; Research Note draft | 20 questions per new archive; RNAAS draft complete |

## 5. Risks and how they are handled

- **Archive changes weekly:** gold and candidate are executed together at scoring time; snapshot dates are logged.
- **API cost:** small question set, caching, local model as a free baseline; CI replays cached responses.
- **Load on public services:** rate limits and caching for both the TAP service and the AstroFetch MCP endpoint.
- **Judge bias:** judge used only for answer faithfulness, calibrated against hand labels, with kappa published.
- **Overfitting the benchmark:** a held-out split of 30 questions is never used while developing prompts.

## 6. Out of scope for v0.1
Fine-tuning models; image or light-curve analysis; write access to any archive.
