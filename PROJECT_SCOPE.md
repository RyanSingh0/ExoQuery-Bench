# ExoQuery-Bench: gated roadmap

The long-term objective remains a reproducible comparison of models, retrieval and tool designs for astronomy archive questions, followed by a useful research assistant. The first implementation is a local evidence-and-review workbench. Its software can be tested now; scientific validity and user impact require external review.

## Acceptance gates

| Gate | Acceptance evidence | Current state |
|---|---|---|
| 0. Contracts and failure semantics | Explicit columns/units/grain/order; partial and unavailable not scored as zero; semantic regression tests | Implemented and locally tested |
| 1. Archive evidence | Raw responses, schema, checksums, complete results, independent rank controls | 17 references and 48 capture checks passed on Oct 12, 2026 |
| 2. Scientific approval | Documented review of all 20 items; critical disagreements resolved | Pending; no expert approvals claimed |
| 3. Usable review workflow | Browser evidence/compare/review flows, persistence, export, installation | Implemented; browser and local API checks performed |
| 4. Real-user pilot | 3–5 volunteers; at least one experienced archive user; concrete tasks and corrections documented | Pending recruitment through BU/LinkedIn contacts |
| 5. Model experiments | Reviewed references, frozen configurations, complete failure/cost logs, controlled comparison | Not started; no paid calls authorized |
| 6. Trustworthy reporting | Family-separated holdout; uncertainty estimates; calibrated human review of answer faithfulness | Not started |
| 7. Shared deployment | Auth, isolation, quotas, monitoring, backup/restore, retention and deployment smoke tests | Not ready; app is local-only |
| 8. Broader impact | Repeat use and documented improvements before expanding archives | Not measured |

Gates 2 and 4 do not block developing the review interface needed to complete them. They do block claims of scientific validation, benchmark rankings and public production readiness. Passing an automated test is not a guarantee of failure-proof operation.

## Next concrete work

1. Use the pilot guide to invite three to five relevant people; record permission to quote feedback separately. No outreach has been sent by the assistant.
2. Review all 20 question contracts, concentrating on reference grain, unit conventions, limit flags, nulls and catalog extrema. Preserve disagreement and sources.
3. Expand only the cases reviewers identify as useful. Keep new scientific families together when allocating future development/holdout splits.
4. Introduce a provider-neutral experiment record with prompt/schema versions, tool trace, costs, latency, attempts and failure origin. Start with imported or locally produced outputs.
5. Decide whether a small paid experiment would answer a specific unresolved question. The possible $10 cap requires a later explicit go-ahead; it has not been spent or activated.
6. Publish model results only after independent review and a frozen protocol. Deploy the shared service only after the operational gate passes.

## Decisions superseding the original plan

- Compare columns by declared meaning, not equal values under unrelated names.
- Preserve required ordering and duplicates, with explicit per-field tolerances and unit conversion.
- Treat empty/partial/unavailable results as inconclusive where correctness is unestablished.
- Do not use simultaneous archive requests as a substitute for an immutable snapshot.
- Separate public development data from a genuinely held-out future evaluation.
- Quarantine the observed direct-TAP TOP/ORDER ranking defect and verify references independently.
- Keep the first app and its review storage local; no model leaderboard or chat agent is implied by this prototype.

For implementation boundaries, see docs/ARCHITECTURE.md. For intended scientific use, see docs/DATASET_CARD.md. For recruitment and impact measures, see docs/PILOT_GUIDE.md.
