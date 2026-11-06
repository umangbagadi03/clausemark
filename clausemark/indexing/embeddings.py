import logging

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client.models import SparseVector

from clausemark import config
from clausemark.utils.bounded_cache import BoundedCache

logger = logging.getLogger(__name__)

# Both models run locally on the CPU, so indexing and evaluation cost nothing.
BM25_MODEL = "Qdrant/bm25"
VECTOR_SIZE = 384
BATCH_SIZE = 16

_dense_model = None
_keyword_model = None
_dense_queries = BoundedCache(config.CACHE_MAX_ITEMS)
_keyword_queries = BoundedCache(config.CACHE_MAX_ITEMS)


def get_dense_model():
    global _dense_model
    if _dense_model is None:
        logger.info("Loading embedding model %s", config.EMBEDDING_MODEL)
        _dense_model = TextEmbedding(config.EMBEDDING_MODEL)
    return _dense_model


def get_keyword_model():
    global _keyword_model
    if _keyword_model is None:
        logger.info("Loading keyword model %s", BM25_MODEL)
        _keyword_model = SparseTextEmbedding(BM25_MODEL)
    return _keyword_model


def to_sparse_vector(embedding):
    return SparseVector(
        indices=embedding.indices.tolist(),
        values=embedding.values.tolist(),
    )


def embed_dense_texts(texts):
    vectors = []
    for vector in get_dense_model().embed(texts, batch_size=BATCH_SIZE):
        vectors.append(vector.tolist())
    return vectors


def embed_keyword_texts(texts):
    vectors = []
    for embedding in get_keyword_model().embed(texts, batch_size=BATCH_SIZE):
        vectors.append(to_sparse_vector(embedding))
    return vectors


def embed_dense_query(question):
    vector = _dense_queries.get(question)
    if vector is None:
        vectors = list(get_dense_model().query_embed(question))
        vector = vectors[0].tolist()
        _dense_queries.put(question, vector)
    return vector


def embed_keyword_query(question):
    vector = _keyword_queries.get(question)
    if vector is None:
        embeddings = list(get_keyword_model().query_embed(question))
        vector = to_sparse_vector(embeddings[0])
        _keyword_queries.put(question, vector)
    return vector
