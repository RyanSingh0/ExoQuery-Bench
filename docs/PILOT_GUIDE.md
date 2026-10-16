# BU and LinkedIn research pilot

## First users and the problem to test

Start with astronomy graduate students, archive users and research software engineers who check exoplanet tables or evaluate AI-generated queries. The first question is whether exposing query, units, source and failure status helps them find errors faster. We have not yet established demand or impact.

Recruit **three to five volunteers**, including **at least one experienced Exoplanet Archive user**. This is a proposed pilot target, not a claim about current users. A 20–30 minute screen-sharing session is enough for the first round; participants can also run the local package themselves.

## Session script

1. Explain that this is a development prototype and that its reference questions are not expert-approved.
2. Ask what archive task the participant performed recently. Record the task rather than leading with product features.
3. Ask them to find the transit count, inspect the TRAPPIST-1 e radius units and review the largest-radius ranking caveat.
4. In Compare, load the synthetic wrong value. Ask what the result means and whether the distinction between result agreement and scientific correctness is clear.
5. Give them a question within their expertise. Ask whether wording, table grain, null handling, limit flags and interpretation are justified. Request a source for corrections.
6. Ask them to save and download a review. Explain that it stays on their computer until they choose to share it.
7. Ask: “Would this have helped with a real task last month? What was missing? Would you use it again?”

## Record only what is needed

| Field | What to record |
|---|---|
| Session ID | Anonymous ID; keep contact information separately |
| Experience | Student / astronomer / archive engineer; voluntary |
| Question IDs | Cases reviewed |
| Completion | Completed unaided / with help / not completed |
| Error found | Specific error and supporting source |
| Time | Approximate task duration; avoid precise claims from tiny samples |
| Usefulness | Participant's own wording |
| Follow-up | Consented interest in a second test |

Do not count QA notes or reference self-checks as real user feedback. No analytics are installed. Do not record a session without permission. Invite participants to exclude personal or unpublished information. Get explicit permission before quoting or naming them publicly.

## Invitation draft — send yourself when ready

I'm building ExoQuery-Bench, a small open-source workbench for checking questions and results from the NASA Exoplanet Archive. It shows the query, units and source evidence, and flags mismatched results. The first 20 questions still need scientific review.

Would you be open to a 20-minute walkthrough and reviewing two or three questions in your area? I'm especially interested in what is scientifically wrong, unclear or missing. There are no paid tools or accounts to set up, and a screen-share is fine.

## Gate before model spending

Resolve material reference errors, document reviews of all 20 items, and identify at least two real tasks that participants want to repeat. Then compare a small number of model/tool configurations on reviewed development questions, using a separately approved budget. The proposed $10 cap is not currently authorized for use. Paid calls may help measure model behaviour; they cannot fix weak references or establish user demand.

## Impact measures after the pilot

Track useful corrections accepted, repeat users, task completion, time to identify planted errors, and real workflows improved. Publish denominators and limitations. Five useful expert reviews are more meaningful at this stage than a large number of page views.
