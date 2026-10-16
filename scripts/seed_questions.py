"""Author the public development set. No expert approval is implied."""

import json
from pathlib import Path

items = []


def add(
    title,
    prompt,
    query,
    columns=None,
    family="population",
    difficulty="easy",
    tags=None,
    caveat=None,
    rationale=None,
    ordered=False,
    take=None,
    decision="answer",
):
    items.append(
        dict(
            id=f"exo-{len(items) + 1:03}",
            title=title,
            prompt=prompt,
            query=query,
            columns=columns if columns is not None else [dict(name="n", rtol=0, atol=0)],
            family=family,
            difficulty=difficulty,
            tags=tags or [family],
            caveat=caveat or "Counts describe the retrieved catalog, not an immutable population.",
            rationale=rationale
            or "The question states the table, row grain, and filters explicitly.",
            ordered=ordered,
            take=take,
            decision=decision,
            expert_review="pending",
        )
    )


def col(name, unit=None, kind="number"):
    return dict(name=name, unit=unit, kind=kind)


add(
    "Catalog planets",
    "How many planet rows are in pscomppars at retrieval time?",
    "select count(*) as n from pscomppars",
)
add(
    "Preferred solutions",
    "How many preferred planet solutions are in ps (default_flag=1)?",
    "select count(*) as n from ps where default_flag=1",
    family="table-grain",
)
add(
    "All reference solutions",
    "How many rows, including multiple references per planet, are in ps?",
    "select count(*) as n from ps",
    family="table-grain",
)
add(
    "Transit discoveries",
    "How many pscomppars planets have discoverymethod exactly 'Transit'?",
    "select count(*) as n from pscomppars where discoverymethod='Transit'",
    tags=["case", "grain"],
)
add(
    "Radial velocity discoveries",
    "How many pscomppars planets have discoverymethod 'Radial Velocity'?",
    "select count(*) as n from pscomppars where discoverymethod='Radial Velocity'",
)
add(
    "Distinct catalog hosts",
    "How many distinct hostname values occur in pscomppars?",
    "select count(distinct hostname) as n from pscomppars",
    family="aggregation",
    caveat="Hostname strings are catalog identifiers; "
    "this is not a resolved multiplicity analysis.",
)
add(
    "TRAPPIST-1 e radius",
    "What is the composite radius of TRAPPIST-1 e in Earth radii?",
    "select pl_rade from pscomppars where pl_name='TRAPPIST-1 e'",
    [col("pl_rade", "Rearth")],
    family="units",
    caveat="Composite parameters can come from different references.",
)
add(
    "TRAPPIST-1 e period",
    "What is TRAPPIST-1 e's composite orbital period in days?",
    "select pl_orbper from pscomppars where pl_name='TRAPPIST-1 e'",
    [col("pl_orbper", "day")],
    family="lookup",
    caveat="A reported value is not an uncertainty estimate.",
)
add(
    "TRAPPIST-1 e distance",
    "What is the pscomppars system distance for TRAPPIST-1 e in parsecs?",
    "select sy_dist from pscomppars where pl_name='TRAPPIST-1 e'",
    [col("sy_dist", "pc")],
    family="units",
    caveat="System distance is not planet-star separation.",
)
add(
    "Small, short-period planets",
    "Count pscomppars rows with measured (pl_radelim=0), non-null radius below 2 Earth radii "
    "and non-null period below 10 days. Treat these as catalog filters, not a completeness study.",
    "select count(*) as n from pscomppars where pl_rade is not null and pl_rade<2 "
    "and pl_radelim=0 and pl_orbper is not null and pl_orbper<10",
    family="joint-filter",
    difficulty="medium",
)
add(
    "Discovery method breakdown",
    "Count pscomppars planets by discoverymethod; order by method ascending.",
    "select discoverymethod,count(*) as n from pscomppars "
    "group by discoverymethod order by discoverymethod",
    [col("discoverymethod", kind="text"), dict(name="n", rtol=0, atol=0)],
    family="aggregation",
    difficulty="medium",
    ordered=True,
)
add(
    "Reference-specific radii",
    "List all ps references for TRAPPIST-1 e with their Earth-radius values and default flags; "
    "retain nulls and every reference. Ordering is irrelevant.",
    "select pl_refname,pl_rade,default_flag from ps where pl_name='TRAPPIST-1 e'",
    [
        col("pl_refname", kind="text"),
        col("pl_rade", "Rearth"),
        dict(name="default_flag", rtol=0, atol=0),
    ],
    family="table-grain",
    difficulty="hard",
    caveat="Reference strings can contain archive HTML; "
    "render them as text, not executable markup.",
)
add(
    "Preferred radius",
    "Return TRAPPIST-1 e's ps radius in Earth radii from the preferred solution (default_flag=1).",
    "select pl_rade from ps where pl_name='TRAPPIST-1 e' and default_flag=1",
    [col("pl_rade", "Rearth")],
    family="table-grain",
    caveat="Preferred ps solution and composite pscomppars values need not be identical.",
)
add(
    "Measured true masses",
    "Count pscomppars rows with non-null pl_bmasse, pl_bmassprov='Mass' and pl_bmasselim=0.",
    "select count(*) as n from pscomppars where pl_bmasse is not null "
    "and pl_bmassprov='Mass' and pl_bmasselim=0",
    family="limits",
    difficulty="medium",
    caveat="Exclude Msini and limits; this is a provenance-filtered count.",
)
add(
    "Radius upper limits",
    "Count pscomppars rows with a non-null radius and pl_radelim=1 (upper limit).",
    "select count(*) as n from pscomppars where pl_rade is not null and pl_radelim=1",
    family="limits",
    difficulty="medium",
)
add(
    "Largest reported catalog radii",
    "List the 10 largest non-null pscomppars pl_rade values with planet names. "
    "Sort radius descending, then name ascending to break ties. "
    "Include catalog entries regardless of limit flag; do not infer physical validity.",
    "select pl_name,pl_rade from pscomppars where pl_rade is not null "
    "order by pl_rade desc,pl_name asc",
    [col("pl_name", kind="text"), col("pl_rade", "Rearth")],
    family="ranking",
    difficulty="hard",
    tags=["top-order-defect", "ordering", "units"],
    ordered=True,
    take=10,
    rationale="Retrieve the complete bounded two-column result, "
    "verify its global order, then take ten locally.",
    caveat="TOP plus ORDER BY is quarantined. "
    "These are catalog extrema, not confirmed physical sizes.",
)
add(
    "Case-sensitive negative control",
    "Count pscomppars rows whose discoverymethod equals the lowercase string 'transit' exactly.",
    "select count(*) as n from pscomppars where discoverymethod='transit'",
    family="case",
    caveat="This is a case-sensitivity control, not the number of transit discoveries.",
)
add(
    "Nearby needs a boundary",
    "Show me the nearby planets.",
    None,
    [],
    family="ambiguity",
    decision="clarify",
    caveat="Ask for a distance threshold, catalog population, and desired fields.",
)
add(
    "Life is not a catalog field",
    "Which exoplanet is proven to host life, according to these tables?",
    None,
    [],
    family="unsupported",
    decision="abstain",
    caveat="The supported tables cannot establish this claim; do not invent a detection.",
)
add(
    "Best needs a metric",
    "What is the best exoplanet?",
    None,
    [],
    family="ambiguity",
    decision="clarify",
    caveat="Ask for the user's scientific objective and ranking criterion.",
)

target = Path(__file__).resolve().parents[1] / "src/eqb/data/questions.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes((json.dumps(items, indent=2) + "\n").encode("utf-8"))
print(f"Wrote {len(items)} public development questions; expert review pending.")
