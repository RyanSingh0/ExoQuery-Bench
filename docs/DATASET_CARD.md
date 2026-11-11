# Public development dataset v0.1

- **Purpose:** engineering validation and scientific review of astronomy archive question contracts.
- **Population:** 20 authored questions; 17 answerable with archived results, two clarification cases, one unsupported claim.
- **Source:** NASA Exoplanet Archive TAP; `ps`, `pscomppars`, and their advertised schema.
- **Capture:** October 12, 2026, UTC timestamps per response; 48 machine checks passed. The workbench displays the capture date.
- **Authorship:** AI-assisted development questions. **Zero expert approvals; zero real-user reviews claimed.**
- **Split:** public development only. No held-out evaluation set exists yet.
- **Coverage:** population counts, table grain, lookups, units, joint filters, reference-specific values, limit flags, aggregation, ordering, case sensitivity, clarification and abstention.
- **Missing coverage:** uncertainty propagation, joins, sky geometry, TOI dispositions, spectra, time-series data, IRSA/KOA, complex scientific synthesis.

## Files and provenance

`src/eqb/data/questions.json` contains contracts and public reference queries. `references.json` contains normalized result rows and source metadata. `raw/` preserves the original VOTable bytes. `schema.json` and `ranking-control.json` provide supporting observations. `verification.json` records checks and hashes. Git preserves the JSON/XML bytes across operating systems.

`eqb doctor` checks packaged hashes and query identities. Tests additionally reconstruct normalized reference rows from raw files. SHA-256 detects accidental changes relative to the bundled manifest; it is not a signed proof of archive authenticity.

Reference normalization converts declared archive units to question units. The ranking question truncates only after a complete response and global-order check. Null values remain null. Count tolerances are exactly zero. Numeric tolerances in other questions address representation differences, not astrophysical uncertainty.

## Appropriate and inappropriate use

Use the set to test transport, scoring, error handling, and the review workflow. Researchers can propose corrected wording, columns, filters, units and interpretation. A reference self-check is a software exercise, not an independent accuracy measurement. Do not publish model rankings, claim expert validation or use these stored values as new scientific discoveries.

The `pscomppars` composite values can originate from different references. Very large catalog radii are catalog extrema, not confirmation that every entry has that physical size. The question about life is unsupported by the selected tables, independent of wider research.

Code and authored questions use the repository MIT license. Archive data retains its source provenance; downstream scientific use should follow [archive acknowledgement guidance](https://exoplanetarchive.ipac.caltech.edu/docs/intro.html) and cite relevant underlying publications. The MIT code license does not replace source attribution.

## Review and promotion

Ask reviewers to record question ID, field of expertise, correctness judgment, correction and source, and whether the case needs another opinion. Preserve dissent. Only change `expert_review` after an actual documented review; feedback submission alone does not change it. Changing a query or unit contract requires a new capture and fresh checks. Keep previous bundles in version control for reproducibility.
