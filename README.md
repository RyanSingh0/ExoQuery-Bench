# ExoQuery-Bench

**How accurately do LLMs answer plain-English questions from NASA astronomy archives?**

ExoQuery-Bench is an open benchmark and evaluation harness for natural-language-to-ADQL assistants on the
[NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/). It scores Claude, OpenAI, Gemini and local
models across retrieval (RAG), self-correcting agents and the public
[AstroFetch](https://astrofetch.ipac.caltech.edu/) MCP tools, and reports *where* answers fail, not just how often.

> **Status: work in progress (started October 2026).** No results are published yet. The roadmap below shows what
> exists and what is next. Numbers in this README describe the archive itself, checked live on 2026-10-07.

---

## Why this exists

Assistants such as AstroFetch turn a question like *"How many planets has the transit method found?"* into ADQL, run
it against the archive's TAP service and explain the result. The
[AstroFetch FAQ](https://astrofetch.ipac.caltech.edu/faq) says the most common errors are wrong column names and unit
mismatches, and that quality is currently judged through user ratings. A public, reproducible score would show which
models, prompts and tools reduce those errors.

The archive has real traps for a language model. Each one below was checked live against the TAP service on
2026-10-07 and against the archive's [column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)
and [TAP guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html):

| Trap | What a model might write | What happens |
|---|---|---|
| One row per *solution*, not per planet | `select count(*) from ps where discoverymethod='Transit'` | **36,100** rows instead of **4,711** planets. The `ps` table holds 40,194 rows for 6,375 planets; only `default_flag=1` (or the `pscomppars` table) gives one row per planet. |
| Earth vs Jupiter radii | `pl_radj` when the question means Earth radii | Answers off by **11.2×** (1 R<sub>Jup</sub> = 11.21 R<sub>Earth</sub>, per `astropy.units`). |
| Case-sensitive values | `discoverymethod='transit'` | **0 rows.** Values are case-sensitive; the stored value is `'Transit'`. |
| SQL habits | `... limit 10` | **Query error.** ADQL uses `select top 10 ...`. |
| Undocumented columns | `disc_method='tran'` | Runs and returns codes (`tran`, `rv`, ...), but `disc_method` is not in `TAP_SCHEMA.columns` or the column docs, so a model cannot learn it from the schema. |
| Inconsistent unit labels | trusting unit strings | Earth radius is labelled `Rearth` in `ps`, `Earth Radius` in `pscomppars` and `R_Earth` in `toi`. |

## What the benchmark measures

**Systems under test**, from simplest to most capable:

| ID | System | Idea |
|---|---|---|
| S0 | Direct prompt | Question in, ADQL out. The baseline. |
| S1 | Schema in prompt | A curated list of tables and key columns in the system prompt. |
| S2 | RAG | Hybrid retrieval (keyword + embeddings) over column definitions, table notes and worked example queries, so the model sees the right columns first. |
| S3 | RAG + agent | A tool-using loop that validates the ADQL, runs it, reads errors, checks units and retries within a step budget. |
| S4 | AstroFetch MCP | The model drives AstroFetch's public MCP tools (`get_profile_context`, `browse_schema`, `validate_adql`, `execute_adql_query`), measuring that production tool path. |

**Providers:** Anthropic Claude, OpenAI, Google Gemini and a local model through Ollama, behind one interface.
Every system returns a structured JSON object (ADQL, tables, columns, units, assumptions) so outputs can be scored
field by field.

**Metrics**

- **Execution accuracy:** run the candidate and the gold query against the live archive at the same moment and
  compare result sets (order-insensitive, numeric tolerance). Comparing at run time keeps the score valid as the
  archive adds planets each week.
- **Component scores:** table choice, column F1, `default_flag` handling, unit correctness (checked with
  `astropy.units`), valid-ADQL rate and correct refusal on unanswerable questions.
- **Answer faithfulness:** an LLM judge checks the final plain-English answer against the returned rows. The judge is
  calibrated against human labels on a subset and reported with Cohen's kappa, because execution matching alone has
  known false positives and negatives ([FLEX, arXiv:2409.19014](https://arxiv.org/abs/2409.19014)).
- **Retrieval quality (S2, S3):** recall@k of the gold columns and context precision.
- **Cost and speed:** tokens, dollars, latency and tool calls per question.
- **Uncertainty:** bootstrap confidence intervals and paired tests between systems, so small differences are not
  over-read.

## The question set

Version 0.1 targets about **120 questions**, each written by hand and checked live. Each item records:

```json
{
  "id": "eqb-0001",
  "question": "How many confirmed planets were discovered by the transit method?",
  "archive": "nasa_exoplanet_archive",
  "gold_adql": "select count(*) from pscomppars where discoverymethod = 'Transit'",
  "tags": ["aggregation", "table_choice", "case_sensitive_value"],
  "difficulty": "easy",
  "answer_type": "scalar",
  "tolerance": 0
}
```

Categories cover lookups, filters, aggregations, unit conversions, table choice (`ps`, `pscomppars`, `stellarhosts`,
`toi`), joins, sky-position searches, TESS candidate dispositions, spectra tables and deliberately unanswerable
questions. Paraphrased variants test whether a system's answer changes when only the wording does.

## Planned repository layout

```
exoquery-bench/
├── data/questions/          # benchmark items (JSONL), versioned
├── data/schema/             # cached TAP_SCHEMA and column docs, with snapshot date
├── src/eqb/
│   ├── archive.py           # TAP client (PyVO / astroquery), caching, polite rate limits
│   ├── providers/           # Claude, OpenAI, Gemini, Ollama behind one interface
│   ├── systems/             # S0 to S4
│   ├── rag/                 # chunking, hybrid retrieval, retrieval metrics
│   ├── scoring/             # result-set comparison, unit checks, LLM judge
│   └── report/              # Bokeh leaderboard and error breakdown
├── app/                     # chat demo with ADQL shown, unit warnings and feedback capture
├── tests/                   # pytest; CI replays cached responses at $0 API cost
└── docs/
```

## Roadmap

- [x] Scope, archive traps and evaluation design (this README)
- [ ] Schema snapshot and 20 seed questions with live-checked gold ADQL
- [ ] Result-set comparator and unit checker, with tests
- [ ] S0 and S1 across all four providers
- [ ] 120-question v0.1 set; S2 (RAG) with retrieval metrics
- [ ] S3 agent and S4 AstroFetch MCP runs
- [ ] LLM judge calibrated against human labels
- [ ] Interactive Bokeh leaderboard on GitHub Pages
- [ ] Chat demo; user feedback turns into new benchmark items
- [ ] Extension to IRSA and the Keck Observatory Archive
- [ ] Short write-up (Research Notes of the AAS)

## Being a good archive citizen

Queries are cached, rate-limited and kept small. Large pulls go through a TAP client and asynchronous jobs, as the archive's
[TAP guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html) advises for big downloads. Runs through the
AstroFetch MCP endpoint are throttled and cached the same way. Feedback from the NExScI team and archive users is
very welcome through Issues.

## Related work

- [ALeRCE text-to-SQL system](https://arxiv.org/abs/2606.18108) (A&A, 2026): 110 question-SQL pairs and 13 LLMs on
  the ALeRCE transient-broker database. Schema linking and self-correction raised accuracy, which motivates S2 and S3
  here.
- [nasa-exoplanet-mcp](https://glama.ai/mcp/servers/saikrmet/nasa-exoplanet-mcp): an open MCP server for the same
  archive with a scenario test suite.
- [Ragas](https://arxiv.org/abs/2309.15217): automated metrics for retrieval-augmented generation.

## Acknowledgements and data

This project uses the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/), maintained by Caltech/IPAC
under contract with NASA, and [AstroFetch](https://astrofetch.ipac.caltech.edu/) from NExScI/IPAC. It is an
independent project and is not affiliated with or endorsed by NASA, Caltech or IPAC. Please cite the archive's DOI
when using its data.

## Author

**Aryan Meena**: MS Applied Data Analytics, Boston University. Earlier evaluation work:
[JudgeGuard](https://github.com/RyanSingh0/judgeguard) ([live app](https://huggingface.co/spaces/RugFace/judgeguard-app)).

## License

MIT
