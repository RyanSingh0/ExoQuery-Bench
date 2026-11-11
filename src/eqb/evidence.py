import hashlib
import json
from importlib.resources import files

from eqb.dataset import questions, references


def verification() -> dict:
    return json.loads(files("eqb").joinpath("data/verification.json").read_text(encoding="utf-8"))


def verify_bundle() -> dict:
    data = files("eqb").joinpath("data")
    manifest = verification()
    failures = []
    for name in ("references", "questions"):
        if (
            hashlib.sha256(data.joinpath(f"{name}.json").read_bytes()).hexdigest()
            != manifest[f"{name}_sha256"]
        ):
            failures.append(f"{name} file hash differs")
    refs = references()
    for q in questions():
        if q.decision != "answer":
            continue
        result = refs.get(q.id)
        if not result or result.status != "ok":
            failures.append(f"{q.id} missing complete reference")
            continue
        if result.provenance.get("query") != q.query:
            failures.append(f"{q.id} query differs")
        digest = result.provenance.get("sha256", "")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            failures.append(f"{q.id} invalid raw hash")
            continue
        raw = data.joinpath(f"raw/{digest}.xml")
        if not raw.is_file() or hashlib.sha256(raw.read_bytes()).hexdigest() != digest:
            failures.append(f"{q.id} raw evidence missing or changed")
    if not manifest["passed"] or not all(c["passed"] for c in manifest["checks"]):
        failures.append("Capture checks did not pass")
    return {
        "ok": not failures,
        "failures": failures,
        "reference_count": len(refs),
        "expert_review": manifest["expert_review"],
        "captured_at": manifest["captured_at"],
    }
