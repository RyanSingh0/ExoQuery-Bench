import httpx
import pytest

from eqb.archive import TapClient


def xml(status="OK", end=""):
    return f'''<?xml version="1.0"?>
    <VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
    <RESOURCE type="results"><INFO name="QUERY_STATUS" value="{status}"/>
    <TABLE><FIELD name="n" datatype="int"/>
    <DATA><TABLEDATA><TR><TD>7</TD></TR></TABLEDATA></DATA></TABLE>{end}
    </RESOURCE></VOTABLE>'''


def client(body, code=200):
    return TapClient(
        httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(code, text=body))),
        interval=0,
    )


def test_valid_votable():
    result = client(xml()).query("select count(*) as n from pscomppars")
    assert result.status == "ok"
    assert result.rows == [{"n": 7}]
    assert len(result.provenance["sha256"]) == 64


@pytest.mark.parametrize(
    "body,status",
    [
        (xml("ERROR"), "error"),
        (xml("OVERFLOW"), "partial"),
        (xml(end='<INFO name="QUERY_STATUS" value="OVERFLOW"/>'), "partial"),
        (xml("UNKNOWN"), "partial"),
        ("<html>Service error</html>", "partial"),
        ("not XML", "error"),
    ],
)
def test_bad_responses_not_success(body, status):
    assert client(body).query("select n from t").status == status


def test_rank_defect_quarantined_before_request():
    assert (
        client(xml()).query("SELECT TOP 10 n FROM t ORDER BY n DESC").failure_origin == "contract"
    )


def test_retry_transient_only(monkeypatch):
    monkeypatch.setattr("eqb.archive.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503 if len(calls) == 1 else 200, text=xml())

    tap = TapClient(httpx.Client(transport=httpx.MockTransport(handler)), interval=0)
    assert tap.query("select n from t").status == "ok"
    assert len(calls) == 2


def test_http_error_preserves_origin():
    result = client("bad query", code=400).query("select n from t")
    assert result.status == "unavailable"
    assert result.failure_origin == "archive"
