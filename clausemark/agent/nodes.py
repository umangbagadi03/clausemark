import logging

from clausemark.agent import prompts
from clausemark.answering.citations import keep_backed_points, verify_citations
from clausemark.answering.parsing import (
    parse_json_reply,
    read_citations,
    read_grade,
    read_points,
)
from clausemark.dataset.corpus import read_contract
from clausemark.llm.errors import LLMError
from clausemark.llm.provider import get_llm
from clausemark.retrieval.pipeline import retrieve
from clausemark.retrieval.recipes import ANSWER_RECIPE

logger = logging.getLogger(__name__)

# Clauses per search, and in total, that go to the LLM
CLAUSES_PER_SEARCH = 5
MAX_CLAUSES = 8


def clause_key(clause):
    return (clause["start"], clause["end"])


def reference_name(label):
    if label[0].isdigit():
        return "Section " + label
    return label


def retrieve_node(state):
    clauses = list(state["clauses"])
    steps = list(state["steps"])

    seen = set()
    for clause in clauses:
        seen.add(clause_key(clause))

    steps.append("Searched for: " + state["query"])

    results = retrieve(state["set_name"], state["query"], ANSWER_RECIPE, state["file_path"])
    for clause in results[:CLAUSES_PER_SEARCH]:
        if clause_key(clause) not in seen and len(clauses) < MAX_CLAUSES:
            seen.add(clause_key(clause))
            clauses.append(clause)

            if clause.get("reached_by"):
                steps.append("Followed a reference to " + reference_name(clause["reached_by"]))

    steps.append("Now have " + str(len(clauses)) + " clauses")
    return {"clauses": clauses, "searches": state["searches"] + 1, "steps": steps}


def clauses_as_text(state):
    text = read_contract(state["set_name"], state["file_path"])
    parts = []
    for clause in state["clauses"]:
        part = "Clause id: " + clause["parent_id"] + "\n"
        part = part + "Title: " + clause["title"] + "\n"
        part = part + text[clause["start"]:clause["end"]]
        parts.append(part)
    return "\n\n---\n\n".join(parts)


def grade_node(state):
    prompt = "Question: " + state["question"] + "\n\nClauses:\n\n" + clauses_as_text(state)
    steps = list(state["steps"])

    # Grading only decides whether to search again, so a failure here should not stop the answer
    try:
        grade = read_grade(get_llm().generate(prompts.GRADE_SYSTEM, prompt))
    except LLMError as error:
        logger.warning("Could not grade the clauses: %s", error)
        steps.append("Could not check the clauses, so used them as found")
        return {"verdict": "enough", "better_query": "", "steps": steps}

    steps.append("Checked the clauses: " + grade.verdict)
    return {"verdict": grade.verdict, "better_query": grade.better_query.strip(), "steps": steps}


def rewrite_node(state):
    return {"query": state["better_query"]}


def answer_node(state):
    prompt = "Question: " + state["question"] + "\n\nClauses:\n\n" + clauses_as_text(state)
    llm = get_llm()

    data = parse_json_reply(llm.generate(prompts.ANSWER_SYSTEM, prompt))
    if data is None:
        logger.warning("The answer was not valid JSON, asking once more")
        data = parse_json_reply(llm.generate(prompts.ANSWER_SYSTEM + "\nReply with valid JSON only.", prompt))
    if data is None:
        raise LLMError("The model did not return a readable answer. Try again.")

    return {"points": read_points(data), "citations": read_citations(data)}


def verify_node(state):
    """No LLM here. A quote that is not in the retrieved clauses is removed,
    and so is any answer point that depended on it."""
    text = read_contract(state["set_name"], state["file_path"])

    verified, rejected_quotes = verify_citations(text, state["citations"], state["clauses"])
    points = keep_backed_points(state["points"], verified)

    steps = list(state["steps"])
    steps.append("Quotes found in the contract: " + str(len(verified)) + ". Removed: " + str(len(rejected_quotes)))
    return {"points": points, "citations": verified, "rejected_quotes": rejected_quotes, "steps": steps}
