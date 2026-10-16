import os
from importlib.resources import files
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from eqb import __version__
from eqb.contracts import StrictModel, Submission
from eqb.dataset import questions, references
from eqb.evidence import verification, verify_bundle
from eqb.scoring import evaluate
from eqb.store import Store


class EvaluationRequest(StrictModel):
    submission: Submission
    source: Literal["manual_result", "reference_replay", "synthetic_failure"] = "manual_result"


class Feedback(StrictModel):
    question_id: str
    category: Literal["question", "query", "units", "reference", "interface", "other"]
    note: str = Field(min_length=10, max_length=2000)
    consent_to_retain: Literal[True]


class RequestBoundary:
    """Bound mutation bodies before JSON parsing and reject browser cross-origin writes."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        if scope["method"] in ("POST", "PUT", "PATCH", "DELETE"):
            origin = headers.get(b"origin")
            host = headers.get(b"host", b"").decode()
            if origin and urlsplit(origin.decode()).netloc != host:
                return await JSONResponse({"detail": "Cross-origin writes are disabled"}, 403)(
                    scope, receive, send
                )
            if not headers.get(b"content-type", b"").startswith(b"application/json"):
                return await JSONResponse({"detail": "Use application/json"}, 415)(
                    scope, receive, send
                )
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > 128 * 1024:
                    return await JSONResponse({"detail": "Request exceeds 128 KiB"}, 413)(
                        scope, receive, send
                    )
                if not message.get("more_body", False):
                    break
            delivered = False

            async def bounded_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            return await self.app(scope, bounded_receive, send)
        return await self.app(scope, receive, send)


def create_app(data_dir: Path | None = None) -> FastAPI:
    integrity = verify_bundle()
    if not integrity["ok"]:
        raise RuntimeError(f"Evidence integrity failure: {integrity['failures']}")
    app = FastAPI(title="ExoQuery Workbench", version=__version__, docs_url=None, redoc_url=None)

    @app.exception_handler(RequestValidationError)
    async def invalid_payload(request: Request, exc: RequestValidationError):
        # Echoing invalid input can itself fail JSON encoding (NaN/Infinity).
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()
                ]
            },
        )

    app.add_middleware(RequestBoundary)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"]
    )
    store = Store((data_dir or Path(os.environ.get("EQB_DATA_DIR", ".eqb"))) / "workbench.sqlite3")
    qs = {q.id: q for q in questions()}
    refs = references()
    static = str(files("eqb").joinpath("static"))

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    def lookup(qid):
        if qid not in qs:
            raise HTTPException(404, "Unknown question")
        return qs[qid]

    @app.get("/api/health")
    def health():
        return {
            "version": __version__,
            "evidence": integrity,
            "mode": "local-offline",
            "model_calls": 0,
            "paid_calls": False,
        }

    @app.get("/api/questions")
    def list_questions():
        return {"questions": list(qs.values()), "verification": verification()}

    @app.get("/api/questions/{qid}")
    def question(qid: str):
        return {"question": lookup(qid), "reference": refs.get(qid)}

    @app.post("/api/evaluate")
    def compare(payload: EvaluationRequest):
        q = lookup(payload.submission.question_id)
        verdict = evaluate(q, payload.submission, refs.get(q.id))
        try:
            return store.add(
                "runs",
                {
                    "question_id": q.id,
                    "source": payload.source,
                    "submission": payload.submission.model_dump(),
                    "verdict": verdict.model_dump(),
                    "reference_sha256": refs[q.id].provenance["sha256"] if q.id in refs else None,
                    "reference_captured_at": integrity["captured_at"],
                },
            )
        except ValueError as exc:
            raise HTTPException(507, str(exc)) from exc

    @app.get("/api/runs")
    def runs():
        return store.list("runs")

    @app.post("/api/feedback", status_code=201)
    def feedback(payload: Feedback):
        lookup(payload.question_id)
        if not payload.note.strip():
            raise HTTPException(422, "Feedback must contain text")
        try:
            record = store.add("feedback", payload.model_dump())
        except ValueError as exc:
            raise HTTPException(507, str(exc)) from exc
        return {"id": record["id"], "saved": True, "review_status": "pending"}

    @app.get("/")
    def home():
        return FileResponse(Path(static) / "index.html")

    app.mount("/static", StaticFiles(directory=static), name="static")
    return app
