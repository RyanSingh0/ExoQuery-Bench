# ExoQuery-Bench

**Inspect astronomy archive evidence before trusting an answer.**

ExoQuery-Bench is a Python evaluation package and local research workbench for questions about the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/). Researchers can inspect queries and source data, compare candidate result tables, and save scientific review notes.

**Status: working development prototype; scientific review pending.** The first public set contains 20 questions, including 17 captured archive references and three clarification/abstention cases. The references were captured on **October 12, 2026**. No model benchmark, expert approval, real-user impact, or production deployment is claimed.

## Start locally

Install Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from this repository:

```sh
uv sync --locked
uv run eqb doctor
uv run eqb serve
```

Open **http://127.0.0.1:8765**. Use Ctrl+C to stop the server. Normal app use is offline after installation. No API keys or paid model calls are needed. On Windows, if `uv` is not on PATH, use its installed executable path instead.

For the locally bound container option, run `docker compose up --build` with Docker running. Reviews persist in the named `reviews` volume. Do not expose this prototype directly to the internet.

## What works

- Browse and search 20 questions, with difficulty and scientific caveats.
- Inspect reference ADQL, returned columns, units, timestamps and raw-response hashes.
- Compare manually supplied JSON results, including unit conversion, duplicates, nulls and required ordering.
- Distinguish mismatch from an unavailable, partial or otherwise inconclusive result.
- Try explicitly labelled reference self-checks and synthetic wrong values.
- Save checks and consented review notes to local SQLite; download evidence and review JSON.
- Capture fresh public archive evidence through an opt-in CLI, preserving raw VOTables and schema metadata.

The browser does not execute arbitrary queries and does not call models. A result match establishes agreement with a saved table, not the correctness of scientific reasoning. References remain visible because this is a public development set.

## Reproduce the checks

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run eqb doctor
uv run eqb replay
```

Tests block external DNS access and mock archive failures. `replay` checks the software against its own references and labels that fact; its output is not model accuracy. The evidence tests reconstruct stored reference rows from the original archive bytes.

The CI workflow runs offline checks on Windows and Linux, builds a wheel/source distribution and smoke-tests the container. Live NASA queries are deliberately excluded from CI.

## Compare a result

Save a submission as `candidate.json`:

```json
{
  "question_id": "exo-007",
  "decision": "answer",
  "result": {
    "status": "ok",
    "rows": [{"pl_rade": 1.0}],
    "units": {"pl_rade": "Rearth"}
  },
  "explanation": "Illustrative candidate, not a verified measurement."
}
```

```sh
uv run eqb evaluate candidate.json
uv run eqb prompts
uv run eqb export-feedback --data-dir .eqb
```

The example is intentionally illustrative and may not match the reference. Exported prompts omit reference queries and expected decisions; they are still from a public development set. Feedback exports can contain reviewer-authored material: review the file before sharing it.

## Refresh evidence deliberately

```sh
uv run eqb capture --output .eqb/capture-new
```

The destination must not already exist. This makes 19 bounded, sequential, read-only requests: a schema query, 17 answerable questions and one independent ranking control. Results are staged there; the command never silently replaces packaged references. Inspect failed checks, review scientific changes, then promote the complete bundle in a new commit and rerun tests. Do not regenerate a hash merely to hide an unexplained mismatch.

The capture checks catch a known direct-TAP `TOP ... ORDER BY` ranking defect. The ranking case instead retrieves the complete bounded two-column result, verifies its order and population, cross-checks its maximum, and selects ten locally. Archive observations and workarounds can change; revalidate them before scientific use.

## Project map

| Location | Purpose |
|---|---|
| `src/eqb/contracts.py` | Strict question, result and submission contracts |
| `src/eqb/archive.py` | Bounded read-only TAP/VOTable adapter |
| `src/eqb/capture.py` | Evidence capture and independent controls |
| `src/eqb/scoring.py` | Unit-aware ordered/multiset comparison |
| `src/eqb/data/` | Questions, references, raw responses and verification |
| `src/eqb/app.py`, `static/` | FastAPI and browser workbench |
| `src/eqb/store.py` | Local SQLite persistence |
| `tests/` | Scientific semantics, failures, integrity and API regressions |

Read the [architecture](docs/ARCHITECTURE.md), [dataset card](docs/DATASET_CARD.md), [pilot guide](docs/PILOT_GUIDE.md), and [gated roadmap](PROJECT_SCOPE.md).

## What comes next

First, obtain scientific review through a small astronomy pilot and correct the reference set. Then introduce recorded model experiments, retrieval/tool comparisons, a separate held-out set, calibrated answer-faithfulness review and a deployment with appropriate user-data controls. IRSA/KOA and broader research tasks follow only after the first archive is validated.

This is an independent project, not affiliated with or endorsed by Caltech, IPAC or NASA. Relevant upstream references: [archive column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html), [TAP usage](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html), and [AstroFetch](https://astrofetch.ipac.caltech.edu/).

Code and authored questions: MIT. Preserve archive provenance and cite underlying scientific sources when using the data.
