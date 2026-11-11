"""Bounded, semantic-column comparison with one-to-one multiset matching."""

import math

from astropy import units as u

from eqb.contracts import Column, Question, Result, Submission, Verdict

ALIASES = {
    "Rearth": u.R_earth,
    "Earth Radius": u.R_earth,
    "R_Earth": u.R_earth,
    "Rjupiter": u.R_jup,
    "Jupiter Radius": u.R_jup,
    "R_Jup": u.R_jup,
    "Mearth": u.M_earth,
    "Earth Mass": u.M_earth,
    "M_Earth": u.M_earth,
    "day": u.day,
    "days": u.day,
    "K": u.K,
    "pc": u.pc,
}


def unit(value: str):
    return ALIASES[value] if value in ALIASES else u.Unit(value)


def cell_matches(a, b, spec: Column, candidate_unit: str | None) -> bool:
    if a is None or b is None:
        return a is b
    if spec.kind == "text":
        return isinstance(a, str) and isinstance(b, str) and a == b
    if isinstance(a, bool) or isinstance(b, bool):
        return False
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return False
    if not math.isfinite(a) or not math.isfinite(b):
        return False
    try:
        if spec.unit:
            if not candidate_unit:
                return False
            a = (a * unit(candidate_unit)).to_value(unit(spec.unit))
        elif candidate_unit:
            return False
    except (ValueError, TypeError, u.UnitConversionError):
        return False
    return math.isclose(a, b, rel_tol=spec.rtol, abs_tol=spec.atol)


def evaluate(q: Question, candidate: Submission, gold: Result | None) -> Verdict:
    def verdict(status, reason):
        return Verdict(status=status, reason=reason)

    if q.id != candidate.question_id:
        return verdict("inconclusive", "Question identity does not match")
    if candidate.decision != q.decision:
        return verdict("mismatch", f"Expected decision: {q.decision}")
    if q.decision != "answer":
        return verdict("decision_match", "Decision agrees; explanation needs human review")
    actual = candidate.result
    if gold is None or gold.status != "ok":
        return verdict("inconclusive", "Reference result is missing or incomplete")
    if actual is None or actual.status != "ok":
        return verdict("inconclusive", "Candidate result is missing or incomplete")
    if len(gold.rows) > 500 or len(actual.rows) > 500:
        return verdict("inconclusive", "Comparison limit is 500 rows")
    expected_columns = {c.name for c in q.columns}
    for result in (gold, actual):
        if any(set(row) != expected_columns for row in result.rows):
            return verdict("mismatch", "Column meanings must match the question contract exactly")
    if not actual.rows and not gold.rows:
        return verdict("inconclusive", "Two empty results do not establish semantic correctness")
    if len(actual.rows) != len(gold.rows):
        return verdict("mismatch", "Row count differs (duplicates count)")

    def row_matches(a, b):
        return all(
            cell_matches(a[c.name], b[c.name], c, actual.units.get(c.name)) for c in q.columns
        )

    if q.ordered:
        matched = all(row_matches(a, b) for a, b in zip(actual.rows, gold.rows, strict=True))
    else:
        # Augmenting-path matching avoids greedy failures with overlapping tolerances.
        edges = [[j for j, b in enumerate(gold.rows) if row_matches(a, b)] for a in actual.rows]
        assigned: dict[int, int] = {}

        def augment(i, visited):
            for j in edges[i]:
                if j in visited:
                    continue
                visited.add(j)
                if j not in assigned or augment(assigned[j], visited):
                    assigned[j] = i
                    return True
            return False

        matched = all(augment(i, set()) for i in range(len(actual.rows)))
    if not matched:
        return verdict("mismatch", "Values, units, multiplicity, or required ordering differ")
    return verdict(
        "match", "Result agrees with the stored reference; expert review is still pending"
    )
