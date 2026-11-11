import json
from importlib.resources import files

from eqb.contracts import Question, Result


def questions() -> list[Question]:
    return [
        Question.model_validate(q)
        for q in json.loads(
            files("eqb").joinpath("data/questions.json").read_text(encoding="utf-8")
        )
    ]


def references() -> dict[str, Result]:
    path = files("eqb").joinpath("data/references.json")
    if not path.is_file():
        return {}
    return {
        k: Result.model_validate(v) for k, v in json.loads(path.read_text(encoding="utf-8")).items()
    }


def model_prompts() -> list[dict]:
    """Separate model-facing contracts from public development reference queries."""
    return [
        {
            "id": q.id,
            "prompt": q.prompt,
            "columns": [c.model_dump() for c in q.columns],
            "ordered": q.ordered,
        }
        for q in questions()
    ]
