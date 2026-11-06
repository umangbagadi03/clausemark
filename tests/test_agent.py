import json

import pytest

from clausemark import config
from clausemark.agent import ask, nodes, prompts
from clausemark.chunking.clause_store import get_parents
from clausemark.llm.errors import LLMError

CONTRACT = "sample/Harbourline_Meridian_Master_Services_Agreement.txt"
REAL_QUOTE = "This Agreement is governed by the laws of the State of Delaware."


def answer_with(quote):
    return json.dumps({
        "points": [{"text": "Delaware law applies.", "citations": [1]}],
        "citations": [{
            "number": 1,
            "clause_id": "anything",
            "exact_quote": quote,
            "explanation": "Sets the governing law.",
            "risk_flag": "LOW",
        }],
    })


GOOD_ANSWER = answer_with(REAL_QUOTE)
ENOUGH = '{"verdict": "enough"}'
NOT_ENOUGH = '{"verdict": "none", "better_query": "governing law jurisdiction"}'


class FakeLLM:
    """Replies by prompt type. A reply can be an exception to raise. The last reply repeats."""

    name = "Fake model"

    def __init__(self, grade=None, answer=None):
        self.replies = {
            prompts.GRADE_SYSTEM: grade or [ENOUGH],
            prompts.ANSWER_SYSTEM: answer or [GOOD_ANSWER],
        }
        self.calls = {"grade": 0, "answer": 0}

    def generate(self, system_prompt, user_prompt):
        if system_prompt == prompts.GRADE_SYSTEM:
            self.calls["grade"] = self.calls["grade"] + 1
            replies = self.replies[prompts.GRADE_SYSTEM]
        else:
            self.calls["answer"] = self.calls["answer"] + 1
            replies = self.replies[prompts.ANSWER_SYSTEM]

        reply = replies[0]
        if len(replies) > 1:
            replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def searches(monkeypatch):
    """Skip the real models: search returns the real clauses of the sample contract.
    The list collects every query that was searched."""
    queries = []

    def fake_retrieve(set_name, query, recipe, file_path):
        queries.append(query)
        # Last clause first, because the agent reads only the top results and the quote is near the end
        return list(reversed(get_parents(set_name, file_path)))

    monkeypatch.setattr(nodes, "retrieve", fake_retrieve)
    set_indexed_chunks(monkeypatch, 5)
    return queries


def set_indexed_chunks(monkeypatch, count):
    def fake_count(set_name, scheme, file_path):
        return count

    monkeypatch.setattr(ask.vector_store, "count_for_contract", fake_count)


def use_llm(monkeypatch, llm):
    def give_llm():
        return llm

    monkeypatch.setattr(nodes, "get_llm", give_llm)
    monkeypatch.setattr(ask, "get_llm", give_llm)


def run(question="Which law governs?"):
    return ask.ask_contract("sample", CONTRACT, question)


def test_happy_path_gives_a_verified_answer(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM())
    result = run()

    assert result["found"] is True
    citation = result["citations"][0]
    text = open("sample_data/corpus/" + CONTRACT, encoding="utf-8").read()
    assert text[citation["start_char"]:citation["end_char"]] == REAL_QUOTE
    assert citation["clause_id"] != "anything"
    assert len(searches) == 1


def test_made_up_quote_means_no_answer(monkeypatch, searches):
    made_up = answer_with("The liability of the vendor is completely unlimited.")
    use_llm(monkeypatch, FakeLLM(answer=[made_up]))
    result = run()

    assert result["found"] is False
    assert result["points"] == []
    assert len(result["rejected_quotes"]) == 1


def test_weak_clauses_search_once_more_with_the_better_query(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM(grade=[NOT_ENOUGH, ENOUGH]))
    run()
    assert searches == ["Which law governs?", "governing law jurisdiction"]


def test_search_stops_after_the_limit(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM(grade=[NOT_ENOUGH]))
    run()
    assert len(searches) == 2


def test_no_better_query_goes_straight_to_the_answer(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM(grade=['{"verdict": "none", "better_query": ""}']))
    result = run()
    assert len(searches) == 1
    assert result["found"] is True


def test_grader_failure_still_answers(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM(grade=[LLMError("busy")]))
    result = run()
    assert result["found"] is True
    assert "Could not check the clauses, so used them as found" in result["steps"]


def test_answer_failure_is_reported(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM(answer=[LLMError("busy")]))
    with pytest.raises(LLMError):
        run()


def test_unreadable_answer_is_retried_once(monkeypatch, searches):
    llm = FakeLLM(answer=["not json", GOOD_ANSWER])
    use_llm(monkeypatch, llm)
    result = run()
    assert result["found"] is True
    assert llm.calls["answer"] == 2


def test_answer_unreadable_twice_is_an_error(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM(answer=["not json"]))
    with pytest.raises(LLMError):
        run()


def test_not_indexed_contract_gives_a_clear_error(monkeypatch):
    set_indexed_chunks(monkeypatch, 0)
    with pytest.raises(ask.IndexNotReady) as error:
        run()
    assert "python main.py index --set sample" in str(error.value)


def test_each_answer_writes_a_trace(monkeypatch, searches):
    use_llm(monkeypatch, FakeLLM())
    run()
    with open(config.TRACES_FILE, encoding="utf-8") as file:
        trace = json.loads(file.readline())
    assert trace["question"] == "Which law governs?"
    assert trace["citations"] == 1
