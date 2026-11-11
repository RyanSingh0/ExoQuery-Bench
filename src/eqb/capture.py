"""Opt-in live evidence capture. Stages results; never silently overwrites package gold."""

import hashlib
import json
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

from eqb.archive import TapClient
from eqb.dataset import questions
from eqb.scoring import unit

SCHEMA_QUERY = (
    "select table_name,column_name,datatype,unit,description from TAP_SCHEMA.columns "
    "where table_name in ('ps','pscomppars') order by table_name,column_name"
)


def capture(destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    tap = TapClient(raw_dir=destination / "raw")
    refs, checks = {}, []

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})

    try:
        schema = tap.query(SCHEMA_QUERY)
        (destination / "schema.json").write_text(schema.model_dump_json(indent=2), encoding="utf-8")
        check("schema_complete", schema.status == "ok" and bool(schema.rows))
        for q in questions():
            if q.decision != "answer":
                continue
            result = tap.query(q.query)
            print(f"{q.id}: {result.status}, {len(result.rows)} rows", flush=True)
            check(f"{q.id}_complete", result.status == "ok" and bool(result.rows))
            if result.status == "ok":
                check(
                    f"{q.id}_columns",
                    all(set(row) == {c.name for c in q.columns} for row in result.rows),
                )
                result.provenance["source_row_count"] = len(result.rows)
                result.provenance["schema_sha256"] = schema.provenance.get("sha256")
                result.provenance["archive_units"] = dict(result.units)
                for column in q.columns:
                    if column.unit:
                        archive_unit = result.units.get(column.name)
                        if not archive_unit:
                            check(f"{q.id}_{column.name}_unit_declared", False)
                            continue
                        try:
                            factor = unit(archive_unit).to(unit(column.unit))
                            for row in result.rows:
                                if row[column.name] is not None:
                                    row[column.name] *= factor
                            result.units[column.name] = column.unit
                            check(f"{q.id}_{column.name}_unit_compatible", True)
                        except (ValueError, TypeError):
                            check(f"{q.id}_{column.name}_unit_compatible", False)
                if q.take:
                    check(
                        "ranking_global_order",
                        result.rows
                        == sorted(result.rows, key=lambda r: (-r["pl_rade"], r["pl_name"])),
                    )
                    result.rows = result.rows[: q.take]
                    result.provenance["client_take"] = q.take
            refs[q.id] = result
        ranking_control = tap.query(
            "select count(*) as n,max(pl_rade) as largest from pscomppars where pl_rade is not null"
        )
        (destination / "ranking-control.json").write_text(
            ranking_control.model_dump_json(indent=2), encoding="utf-8"
        )
        if all(r.status == "ok" for r in refs.values()) and ranking_control.status == "ok":
            count = refs["exo-001"].rows[0]["n"]
            check("preferred_vs_composite_population", count == refs["exo-002"].rows[0]["n"])
            check(
                "method_groups_sum_to_population",
                count == sum(r["n"] for r in refs["exo-011"].rows),
            )
            check("preferred_lookup_unique", len(refs["exo-013"].rows) == 1)
            check("case_control_zero", refs["exo-017"].rows == [{"n": 0}])
            ranked = refs["exo-016"]
            control = ranking_control.rows[0]
            check("ranked_population_count", ranked.provenance["source_row_count"] == control["n"])
            check("ranked_maximum", abs(ranked.rows[0]["pl_rade"] - control["largest"]) < 1e-6)
        else:
            check("cross_query_checks_available", False)
        manifest = {
            "captured_at": datetime.now(UTC).isoformat(),
            "questions": 20,
            "answerable": len(refs),
            "checks": checks,
            "passed": all(c["passed"] for c in checks),
            "expert_review": "pending",
            "kind": "public-development-reference",
            "model_runs": 0,
            "model_cost_usd": 0,
            "questions_sha256": hashlib.sha256(
                files("eqb").joinpath("data/questions.json").read_bytes()
            ).hexdigest(),
            "limitations": [
                "Archive calls are sequential, not an atomic data snapshot.",
                "Machine checks do not replace expert scientific review.",
                "Replaying saved data does not verify current archive contents.",
            ],
        }
        ref_text = json.dumps({k: v.model_dump() for k, v in refs.items()}, indent=2) + "\n"
        (destination / "references.json").write_bytes(ref_text.encode("utf-8"))
        manifest["references_sha256"] = hashlib.sha256(ref_text.encode()).hexdigest()
        (destination / "verification.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return manifest
    finally:
        tap.close()
