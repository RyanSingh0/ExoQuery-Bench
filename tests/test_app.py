import json

import pytest
from fastapi.testclient import TestClient

from eqb.app import create_app
from eqb.dataset import references


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        yield client


def sample():
    return {
        "source": "reference_replay",
        "submission": {"question_id": "exo-007", "result": references()["exo-007"].model_dump()},
    }


def test_api_and_static(client):
    assert client.get("/api/health").json()["evidence"]["ok"]
    assert len(client.get("/api/questions").json()["questions"]) == 20
    assert client.get("/api/questions/does-not-exist").status_code == 404
    response = client.get("/")
    assert response.status_code == 200
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert client.get("/static/app.js").status_code == 200


def test_evaluate_persists_with_evidence_identity(client):
    result = client.post("/api/evaluate", json=sample())
    assert result.status_code == 200
    run = result.json()
    assert run["verdict"]["status"] == "match"
    assert len(run["reference_sha256"]) == 64
    assert client.get("/api/runs").json()[0]["id"] == run["id"]


def test_unit_error_is_visible(client):
    payload = sample()
    payload["submission"]["result"]["units"]["pl_rade"] = "Rjupiter"
    assert client.post("/api/evaluate", json=payload).json()["verdict"]["status"] == "mismatch"


def test_no_arbitrary_query_endpoint(client):
    assert client.post("/api/query", json={"query": "select * from ps"}).status_code == 404


def test_mutation_boundaries(client):
    assert (
        client.post(
            "/api/evaluate", json=sample(), headers={"Origin": "https://unrelated.example"}
        ).status_code
        == 403
    )
    assert client.post("/api/evaluate", content="x").status_code == 415
    assert (
        client.post(
            "/api/evaluate", content="x" * 131073, headers={"Content-Type": "application/json"}
        ).status_code
        == 413
    )
    assert client.get("/", headers={"Host": "unrelated.example"}).status_code == 400
    assert client.post("/api/evaluate", json={"unexpected": 1}).status_code == 422


def test_feedback_requires_consent_and_persists_as_text(client, tmp_path):
    payload = {"question_id": "exo-007", "category": "units", "note": "<script>alert(1)</script>"}
    assert client.post("/api/feedback", json=payload).status_code == 422
    payload["consent_to_retain"] = True
    assert client.post("/api/feedback", json=payload).status_code == 201
    from eqb.store import Store

    assert Store(tmp_path / "workbench.sqlite3").list("feedback")[0]["note"] == payload["note"]


def test_database_survives_restart(tmp_path):
    with TestClient(create_app(tmp_path)) as first:
        run = first.post("/api/evaluate", json=sample()).json()
    with TestClient(create_app(tmp_path)) as second:
        assert second.get("/api/runs").json()[0]["id"] == run["id"]


def test_invalid_json(client):
    response = client.post(
        "/api/evaluate", content="{bad", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    json.loads(response.content)


@pytest.mark.parametrize("invalid_number", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_numbers_are_rejected(client, invalid_number):
    payload = sample()
    payload["submission"]["result"]["rows"][0]["pl_rade"] = invalid_number
    response = client.post(
        "/api/evaluate", content=json.dumps(payload), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
