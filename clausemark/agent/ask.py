import time

from clausemark.agent.graph import build_agent
from clausemark.agent.nodes import CLAUSES_PER_SEARCH
from clausemark.agent.traces import save_trace
from clausemark.indexing import vector_store
from clausemark.llm.provider import get_llm
from clausemark.retrieval.pipeline import retrieve
from clausemark.retrieval.recipes import ANSWER_RECIPE

SEARCH_ONLY_NAME = "No model: search only"

_agent = None


class IndexNotReady(Exception):
    """The contract has not been indexed. The message says how to fix it."""


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def clause_for_reply(clause):
    return {
        "clause_id": clause["parent_id"],
        "title": clause["title"],
        "start": clause["start"],
        "end": clause["end"],
        "reached_by": clause.get("reached_by", ""),
    }


def check_indexed(set_name, file_path):
    if vector_store.count_for_contract(set_name, "clause", file_path) == 0:
        raise IndexNotReady("This contract is not indexed yet. Run: python main.py index --set " + set_name)


def search_contract(set_name, file_path, question):
    """No LLM at all: run the same search the agent runs and return the clauses it found.
    The app uses this when there is no model, so a public demo still does real work."""
    started = time.time()
    check_indexed(set_name, file_path)

    results = retrieve(set_name, question, ANSWER_RECIPE, file_path)

    clauses = []
    for clause in results[:CLAUSES_PER_SEARCH]:
        clauses.append(clause_for_reply(clause))

    steps = [
        "Searched for: " + question,
        "Found " + str(len(clauses)) + " clauses",
        "No model was chosen, so no written answer and no quotes",
    ]

    result = {
        "mode": "search",
        "question": question,
        "file_path": file_path,
        "found": False,
        "points": [],
        "citations": [],
        "rejected_quotes": [],
        "clauses": clauses,
        "steps": steps,
        "model": SEARCH_ONLY_NAME,
        "seconds": round(time.time() - started, 1),
    }
    save_trace(result)
    return result


def ask_contract(set_name, file_path, question, llm=None):
    """Run the full agent. llm is the model for this question; without one, the server's own model is used."""
    started = time.time()
    check_indexed(set_name, file_path)

    if llm is None:
        llm = get_llm()

    state = get_agent().invoke({
        "set_name": set_name,
        "file_path": file_path,
        "question": question,
        "llm": llm,
        "query": question,
        "searches": 0,
        "clauses": [],
        "verdict": "",
        "better_query": "",
        "points": [],
        "citations": [],
        "rejected_quotes": [],
        "steps": [],
    })

    points = []
    for point in state["points"]:
        points.append(point.model_dump())

    citations = []
    for citation in state["citations"]:
        citations.append(citation.model_dump())

    clauses = []
    for clause in state["clauses"]:
        clauses.append(clause_for_reply(clause))

    result = {
        "mode": "answer",
        "question": question,
        "file_path": file_path,
        "found": len(points) > 0,
        "points": points,
        "citations": citations,
        "rejected_quotes": state["rejected_quotes"],
        "clauses": clauses,
        "steps": state["steps"],
        "model": llm.name,
        "seconds": round(time.time() - started, 1),
    }
    save_trace(result)
    return result
