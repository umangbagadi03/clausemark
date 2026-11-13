from clausemark import config
from clausemark.indexing import embeddings, vector_store
from clausemark.utils.bounded_cache import BoundedCache

# Each search brings this many candidates into fusion
CANDIDATES_PER_SEARCH = 50

# The usual constant for Reciprocal Rank Fusion
RRF_K = 60

_cache = BoundedCache(config.CACHE_MAX_ITEMS)


def dense_search(set_name, scheme, question, limit, file_path):
    query = embeddings.embed_dense_query(question)
    return vector_store.search(set_name, scheme, "dense", query, limit, file_path)


def keyword_search(set_name, scheme, question, limit, file_path):
    query = embeddings.embed_keyword_query(question)
    return vector_store.search(set_name, scheme, "bm25", query, limit, file_path)


def score_of(pair):
    # pair is (chunk_id, score)
    return pair[1]


def fuse_rankings(rankings):
    """Reciprocal Rank Fusion. A chunk scores more when it ranks high in more lists."""
    scores = {}
    chunks = {}

    for ranking in rankings:
        position = 0
        for chunk in ranking:
            chunk_id = chunk["chunk_id"]
            chunks[chunk_id] = chunk

            # The first result gets 1/61, the second 1/62, and so on
            points = 1 / (RRF_K + position + 1)
            scores[chunk_id] = scores.get(chunk_id, 0) + points
            position = position + 1

    # Sort best first. When two scores are equal, sorted() keeps the first-seen order.
    pairs = sorted(scores.items(), key=score_of, reverse=True)

    fused = []
    for chunk_id, score in pairs:
        fused.append(chunks[chunk_id])
    return fused


def run_search(set_name, scheme, mode, question, file_path):
    """mode is "dense" or "hybrid". An uploaded contract can change, so it is never cached."""
    use_cache = set_name != config.UPLOADS_SET
    key = (set_name, scheme, mode, question, file_path)

    if use_cache:
        cached = _cache.get(key)
        if cached is not None:
            return cached

    dense_results = dense_search(set_name, scheme, question, CANDIDATES_PER_SEARCH, file_path)

    if mode == "dense":
        results = dense_results
    else:
        keyword_results = keyword_search(set_name, scheme, question, CANDIDATES_PER_SEARCH, file_path)
        results = fuse_rankings([dense_results, keyword_results])

    if use_cache:
        _cache.put(key, results)
    return results
