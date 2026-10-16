import argparse
import json
from pathlib import Path

from eqb.contracts import Submission
from eqb.dataset import model_prompts, questions, references
from eqb.evidence import verify_bundle
from eqb.scoring import evaluate


def main():
    parser = argparse.ArgumentParser(description="ExoQuery evidence and comparison workbench")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check packaged evidence integrity without network access")
    commands.add_parser("prompts", help="Export model-facing prompts without reference queries")
    commands.add_parser("replay", help="Replay reference self-checks (not a model benchmark)")
    serve = commands.add_parser("serve", help="Start the local-only browser workbench")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--data-dir", type=Path, default=Path(".eqb"))
    live = commands.add_parser("capture", help="Opt-in read-only live NASA evidence capture")
    live.add_argument("--output", type=Path, required=True)
    score = commands.add_parser("evaluate", help="Compare one candidate submission JSON offline")
    score.add_argument("submission", type=Path)
    export = commands.add_parser(
        "export-feedback", help="Export this installation's local review notes"
    )
    export.add_argument("--data-dir", type=Path, default=Path(".eqb"))
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn

        from eqb.app import create_app

        uvicorn.run(create_app(args.data_dir), host="127.0.0.1", port=args.port)
        return
    if args.command == "capture":
        from eqb.capture import capture

        result = capture(args.output)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["passed"] else 1)
    if args.command == "doctor":
        result = verify_bundle()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["ok"] else 1)
    if args.command == "prompts":
        print(json.dumps(model_prompts(), indent=2))
    elif args.command == "evaluate":
        if not verify_bundle()["ok"]:
            parser.error("Evidence bundle failed integrity checks")
        candidate = Submission.model_validate_json(args.submission.read_text(encoding="utf-8"))
        qs = {q.id: q for q in questions()}
        if candidate.question_id not in qs:
            parser.error("Unknown question ID")
        result = evaluate(
            qs[candidate.question_id], candidate, references().get(candidate.question_id)
        )
        print(result.model_dump_json(indent=2))
        raise SystemExit(0 if result.status in ("match", "decision_match") else 1)
    elif args.command == "replay":
        integrity = verify_bundle()
        if not integrity["ok"]:
            print(json.dumps(integrity, indent=2))
            raise SystemExit(1)
        refs = references()
        results = [
            {
                "id": q.id,
                "verdict": evaluate(
                    q,
                    Submission(question_id=q.id, decision=q.decision, result=refs.get(q.id)),
                    refs.get(q.id),
                ).model_dump(),
            }
            for q in questions()
        ]
        print(
            json.dumps({"kind": "reference_replay", "model_runs": 0, "results": results}, indent=2)
        )
        raise SystemExit(
            0 if all(r["verdict"]["status"] in ("match", "decision_match") for r in results) else 1
        )
    elif args.command == "export-feedback":
        from eqb.store import Store

        print(
            json.dumps(Store(args.data_dir / "workbench.sqlite3").list("feedback", 10000), indent=2)
        )


if __name__ == "__main__":
    main()
