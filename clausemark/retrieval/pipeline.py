from clausemark.chunking.clause_store import get_parent
from clausemark.retrieval.references import add_referenced_clauses
from clausemark.retrieval.reranker import rerank
from clausemark.retrieval.search import run_search


def lift_to_parents(set_name, chunks):
    """Replace each child with its full clause, in the same order and without repeats."""
    parents = []
    seen = set()

    for chunk in chunks:
        parent_id = chunk["parent_id"]
        if parent_id in seen:
            continue
        seen.add(parent_id)

        parent = get_parent(set_name, chunk["file_path"], parent_id)
        if parent is not None:
            parents.append(parent)

    return parents


def retrieve(set_name, question, recipe, file_path=None):
    """Run one retrieval recipe. Every result has file_path, start and end."""
    results = run_search(set_name, recipe["scheme"], recipe["search"], question, file_path)

    if recipe["rerank"]:
        results = rerank(set_name, question, results)

    if recipe["parents"]:
        results = lift_to_parents(set_name, results)

    if recipe["references"]:
        results = add_referenced_clauses(set_name, results)

    return results
