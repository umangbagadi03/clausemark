import logging

from fastembed.rerank.cross_encoder import TextCrossEncoder

from clausemark import config
from clausemark.dataset.corpus import read_contract
from clausemark.utils.bounded_cache import BoundedCache

logger = logging.getLogger(__name__)

# A cross-encoder reads the question and a passage together, so it judges relevance
# better than vector similarity. It is slower, so it only sees the top candidates.
RERANK_CANDIDATES = 40

_model = None
_cache = BoundedCache(config.CACHE_MAX_ITEMS)


def get_model():
    global _model
    if _model is None:
        logger.info("Loading reranker %s", config.RERANKER_MODEL)
        _model = TextCrossEncoder(config.RERANKER_MODEL)
    return _model


def passage_for(set_name, chunk):
    text = read_contract(set_name, chunk["file_path"])
    body = text[chunk["start"]:chunk["end"]]
    if chunk["header"]:
        return chunk["header"] + "\n" + body
    return body


def pair_sort_key(pair):
    # Higher score first. On equal scores keep the original order.
    return (pair[0], -pair[1])


def score_and_sort(set_name, question, candidates):
    passages = []
    for chunk in candidates:
        passages.append(passage_for(set_name, chunk))

    scores = list(get_model().rerank(question, passages))

    pairs = []
    for index, chunk in enumerate(candidates):
        pairs.append((float(scores[index]), index, chunk))
    pairs.sort(key=pair_sort_key, reverse=True)

    ranked = []
    for pair in pairs:
        ranked.append(pair[2])
    return ranked


def rerank(set_name, question, chunks):
    """Return the top candidates, best first."""
    candidates = chunks[:RERANK_CANDIDATES]
    if len(candidates) == 0:
        return []

    # An uploaded contract can change under the same name, so it is never cached
    if set_name == config.UPLOADS_SET:
        return score_and_sort(set_name, question, candidates)

    key_parts = [set_name, question]
    for chunk in candidates:
        key_parts.append(chunk["chunk_id"])
    key = tuple(key_parts)

    ranked = _cache.get(key)
    if ranked is None:
        ranked = score_and_sort(set_name, question, candidates)
        _cache.put(key, ranked)
    return ranked
