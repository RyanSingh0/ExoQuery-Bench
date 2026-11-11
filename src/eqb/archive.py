"""Bounded read-only TAP transport. No paid services or model calls."""

import hashlib
import io
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import numpy as np
from astropy.io.votable import parse_single_table
from defusedxml import ElementTree

from eqb.contracts import Result

ENDPOINT = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
MAX_BYTES = 8 * 1024 * 1024


class TapClient:
    def __init__(self, client=None, raw_dir: Path | None = None, interval=1.0):
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(60, connect=10),
            follow_redirects=False,
            headers={"User-Agent": "ExoQuery-Bench/0.1 research-validation"},
        )
        self.owned = client is None
        self.raw_dir = raw_dir
        self.interval = interval
        self.last_request = 0.0

    def close(self):
        if self.owned:
            self.client.close()

    def query(self, query: str) -> Result:
        if not re.match(r"^\s*select\b", query, re.I) or ";" in query:
            return Result(
                status="error", error="Only a single SELECT is supported", failure_origin="contract"
            )
        if re.search(r"\btop\s+\d+", query, re.I) and re.search(r"\border\s+by\b", query, re.I):
            return Result(
                status="error",
                error="TOP with ORDER BY is quarantined: known ranking defect",
                failure_origin="contract",
            )
        provenance = {
            "endpoint": ENDPOINT,
            "query": query,
            "started_at": datetime.now(UTC).isoformat(),
            "maxrec": 10000,
        }
        raw = b""
        for attempt in range(3):
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                with self.client.stream(
                    "GET",
                    ENDPOINT,
                    params={
                        "REQUEST": "doQuery",
                        "LANG": "ADQL",
                        "QUERY": query,
                        "FORMAT": "votable",
                        "MAXREC": 10000,
                    },
                ) as response:
                    provenance["http_status"] = response.status_code
                    provenance["attempts"] = attempt + 1
                    if response.status_code in (429, 502, 503, 504) and attempt < 2:
                        time.sleep(2**attempt)
                        continue
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            return Result(
                                status="partial",
                                error="Response exceeds 8 MiB",
                                failure_origin="transport",
                                provenance=provenance,
                            )
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                break
            except httpx.TransportError as exc:
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                return Result(
                    status="unavailable",
                    error=type(exc).__name__,
                    failure_origin="transport",
                    provenance=provenance,
                )
            except httpx.HTTPStatusError:
                return Result(
                    status="unavailable",
                    error="Archive HTTP failure",
                    failure_origin="archive",
                    provenance=provenance,
                )
        digest = hashlib.sha256(raw).hexdigest()
        provenance.update(
            {"sha256": digest, "finished_at": datetime.now(UTC).isoformat(), "bytes": len(raw)}
        )
        if self.raw_dir:
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            (self.raw_dir / f"{digest}.xml").write_bytes(raw)
        try:
            root = ElementTree.fromstring(raw)
            statuses = [
                e.attrib.get("value", "").upper()
                for e in root.iter()
                if e.tag.split("}")[-1] == "INFO"
                and e.attrib.get("name", "").upper() == "QUERY_STATUS"
            ]
            if "ERROR" in statuses:
                return Result(
                    status="error",
                    error="Archive reported QUERY_STATUS=ERROR",
                    failure_origin="archive",
                    provenance=provenance,
                )
            if "OVERFLOW" in statuses or "OK" not in statuses:
                return Result(
                    status="partial",
                    error="Overflow or missing completion status",
                    failure_origin="archive",
                    provenance=provenance,
                )
            table = parse_single_table(io.BytesIO(raw)).to_table(use_names_over_ids=True)
            if len(table) >= 10000:
                return Result(
                    status="partial",
                    error="Row cap reached; completeness uncertain",
                    failure_origin="archive",
                    provenance=provenance,
                )

            def scalar(v):
                if np.ma.is_masked(v):
                    return None
                if isinstance(v, np.generic):
                    v = v.item()
                if isinstance(v, float) and not np.isfinite(v):
                    return None
                if isinstance(v, bytes):
                    return v.decode("utf-8")
                return v

            rows = [{c: scalar(row[c]) for c in table.colnames} for row in table]
            units = {c: str(table[c].unit) if table[c].unit else None for c in table.colnames}
            return Result(status="ok", rows=rows, units=units, provenance=provenance)
        except Exception as exc:
            return Result(
                status="error",
                error=f"Invalid VOTable: {type(exc).__name__}",
                failure_origin="archive",
                provenance=provenance,
            )
