from eqb.dataset import model_prompts, questions


def test_seed_contract_and_export_separation():
    qs = questions()
    assert len(qs) == len({q.id for q in qs}) == 20
    assert sum(q.decision == "answer" for q in qs) == 17
    assert all(q.expert_review == "pending" for q in qs)
    for prompt in model_prompts():
        assert not {"query", "rationale", "decision", "take"} & prompt.keys()


def test_ranking_never_uses_top():
    q = next(q for q in questions() if q.take)
    assert "top" not in q.query.lower()
    assert "order by pl_rade desc,pl_name asc" in q.query
