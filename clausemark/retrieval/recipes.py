# Each recipe adds one change to the one before it, so we can see what each change does.
# Scope "corpus" searches every contract, like the paper does.
# Scope "contract" searches only the contract the answer is in, like a user who has opened it.


def make_recipe(name, label, scheme, search, rerank, parents, references, scope):
    return {
        "name": name,
        "label": label,
        "scheme": scheme,
        "search": search,
        "rerank": rerank,
        "parents": parents,
        "references": references,
        "scope": scope,
    }


RECIPES = [
    make_recipe("1_fixed_dense", "Fixed 500 chars, vector search", "fixed", "dense", False, False, False, "corpus"),
    make_recipe("2_fixed_hybrid", "+ BM25 with RRF", "fixed", "hybrid", False, False, False, "corpus"),
    make_recipe("3_fixed_titled", "+ contract name in search text", "fixed_titled", "hybrid", False, False, False, "corpus"),
    make_recipe("4_clause_hybrid", "Clause chunks instead of fixed", "clause", "hybrid", False, False, False, "corpus"),
    make_recipe("5_clause_rerank", "+ cross-encoder reranker", "clause", "hybrid", True, False, False, "corpus"),
    make_recipe("6_clause_parents", "+ return the full clause", "clause", "hybrid", True, True, False, "corpus"),
    make_recipe("7_references", "+ cross-reference resolver", "clause", "hybrid", True, True, True, "corpus"),
    make_recipe("8_scoped_chunks", "Recipe 5 inside one contract", "clause", "hybrid", True, False, False, "contract"),
    make_recipe("9_scoped_parents", "Recipe 6 inside one contract", "clause", "hybrid", True, True, False, "contract"),
    make_recipe("10_scoped_references", "Recipe 7 inside one contract", "clause", "hybrid", True, True, True, "contract"),
]

def get_recipe(name):
    for recipe in RECIPES:
        if recipe["name"] == name:
            return recipe
    raise ValueError("Unknown recipe: " + name)


# The recipe the app uses to answer questions. A user always has a contract open.
ANSWER_RECIPE = get_recipe("10_scoped_references")
