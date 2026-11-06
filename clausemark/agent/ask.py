import time

from clausemark.agent.graph import build_agent
from clausemark.agent.traces import save_trace
from clausemark.indexing import vector_store
from clausemark.llm.provider import get_llm

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


def ask_contract(set_name, file_path, question):
    started = time.time()

    if vector_store.count_for_contract(set_name, "clause", file_path) == 0:
        raise IndexNotReady("This contract is not indexed yet. Run: python main.py index --set " + set_name)

    state = get_agent().invoke({
        "set_name": set_name,
        "file_path": file_path,
        "question": question,
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
        "question": question,
        "file_path": file_path,
        "found": len(points) > 0,
        "points": points,
        "citations": citations,
        "rejected_quotes": state["rejected_quotes"],
        "clauses": clauses,
        "steps": state["steps"],
        "model": get_llm().name,
        "seconds": round(time.time() - started, 1),
    }
    save_trace(result)
    return result
