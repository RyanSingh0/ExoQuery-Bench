from hypothesis import given
from hypothesis import strategies as st

from eqb.contracts import Column, Question, Result, Submission
from eqb.scoring import evaluate


def question(**kwargs):
    return Question(
        id="q",
        family="f",
        title="t",
        prompt="p",
        difficulty="easy",
        tags=[],
        query="select n from t",
        columns=[Column(name="n")],
        rationale="r",
        caveat="c",
        **kwargs,
    )


def score(rows, gold, q=None, **kwargs):
    return evaluate(
        q or question(),
        Submission(question_id="q", result=Result(status="ok", rows=rows, **kwargs)),
        Result(status="ok", rows=gold),
    )


@given(st.lists(st.integers(-10000, 10000), min_size=1, max_size=25))
def test_multiset_permutation(values):
    rows = [{"n": n} for n in values]
    assert score(rows[::-1], rows).status == "match"


def test_duplicate_counts():
    assert score([{"n": 1}, {"n": 2}], [{"n": 1}, {"n": 1}]).status == "mismatch"


def test_order_is_semantic():
    rows = [{"n": 1}, {"n": 2}]
    assert score(rows[::-1], rows, question(ordered=True)).status == "mismatch"


def test_semantic_columns():
    assert score([{"unrelated": 1}], [{"n": 1}]).status == "mismatch"


def test_incomplete_and_empty_are_not_passes():
    assert score([], []).status == "inconclusive"
    assert (
        evaluate(
            question(),
            Submission(question_id="q", result=Result(status="partial")),
            Result(status="ok", rows=[{"n": 1}]),
        ).status
        == "inconclusive"
    )


def test_units_require_conversion():
    q = question()
    q.columns = [Column(name="n", unit="Rearth")]
    assert (
        score([{"n": 1}], [{"n": 11.20898073093868}], q, units={"n": "Rjupiter"}).status == "match"
    )
    assert score([{"n": 1}], [{"n": 1}], q, units={"n": "Rjupiter"}).status == "mismatch"
    assert score([{"n": 1}], [{"n": 1}], q).status == "mismatch"
    assert score([{"n": 1}], [{"n": 1}], q, units={"n": "K"}).status == "mismatch"


def test_null_and_bool():
    assert score([{"n": None}], [{"n": 0}]).status == "mismatch"
    assert score([{"n": True}], [{"n": 1}]).status == "mismatch"
    assert score([{"n": None}], [{"n": None}]).status == "match"


def test_matching_is_not_greedy():
    q = question()
    q.columns = [Column(name="n", atol=1, rtol=0)]
    assert score([{"n": 1}, {"n": 0}], [{"n": 0}, {"n": 2}], q).status == "match"


def test_clarification_needs_human_review():
    q = question()
    q.decision = "clarify"
    assert (
        evaluate(q, Submission(question_id="q", decision="clarify"), None).status
        == "decision_match"
    )
