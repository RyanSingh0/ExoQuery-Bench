import hashlib
import io
import json
from importlib.resources import files

import numpy as np
import pytest
from astropy.io.votable import parse_single_table

from eqb.dataset import questions, references
from eqb.evidence import verify_bundle
from eqb.scoring import unit


def test_bundle_hashes_and_capture_checks():
    assert verify_bundle()["ok"]


def test_reference_rows_are_reproducible_from_raw_archive_bytes():
    data = files("eqb").joinpath("data")
    refs = references()
    for q in questions():
        if q.decision != "answer":
            continue
        ref = refs[q.id]
        raw = data.joinpath(f"raw/{ref.provenance['sha256']}.xml").read_bytes()
        table = parse_single_table(io.BytesIO(raw)).to_table(use_names_over_ids=True)
        assert len(table) == ref.provenance["source_row_count"]
        rows = []
        for row in table[: q.take] if q.take else table:
            normalized = {}
            for c in q.columns:
                value = row[c.name]
                if np.ma.is_masked(value):
                    value = None
                elif isinstance(value, np.generic):
                    value = value.item()
                if value is not None and c.unit:
                    value *= unit(ref.provenance["archive_units"][c.name]).to(unit(c.unit))
                normalized[c.name] = value
            rows.append(normalized)
        assert rows == ref.rows


def test_schema_and_independent_ranking_evidence():
    data = files("eqb").joinpath("data")
    for name in ("schema", "ranking-control"):
        result = json.loads(data.joinpath(f"{name}.json").read_text(encoding="utf-8"))
        digest = result["provenance"]["sha256"]
        assert hashlib.sha256(data.joinpath(f"raw/{digest}.xml").read_bytes()).hexdigest() == digest
    refs = references()
    control = json.loads(data.joinpath("ranking-control.json").read_text(encoding="utf-8"))["rows"][
        0
    ]
    assert control["n"] == refs["exo-016"].provenance["source_row_count"]
    assert control["largest"] == pytest.approx(refs["exo-016"].rows[0]["pl_rade"], abs=1e-6)
