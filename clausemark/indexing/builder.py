import logging

from qdrant_client.models import PointStruct

from clausemark.chunking.clauses import split_clauses
from clausemark.chunking.fixed import split_fixed
from clausemark.dataset.corpus import list_benchmark_contracts, read_contract
from clausemark.indexing import embeddings, vector_store

logger = logging.getLogger(__name__)

SCHEMES = ["fixed", "fixed_titled", "clause"]
BATCH_SIZE = 128


def chunks_for_contract(scheme, file_path, text):
    if scheme == "fixed":
        return split_fixed(file_path, text, False)
    if scheme == "fixed_titled":
        return split_fixed(file_path, text, True)
    parents, children = split_clauses(file_path, text)
    return children


def search_text(chunk, text):
    body = text[chunk["start"]:chunk["end"]]
    if chunk["header"]:
        return chunk["header"] + "\n" + body
    return body


def add_batch(set_name, scheme, chunks, texts):
    dense_vectors = embeddings.embed_dense_texts(texts)
    keyword_vectors = embeddings.embed_keyword_texts(texts)

    points = []
    for index, chunk in enumerate(chunks):
        points.append(PointStruct(
            id=vector_store.point_id(chunk["chunk_id"]),
            vector={"dense": dense_vectors[index], "bm25": keyword_vectors[index]},
            payload=chunk,
        ))
    vector_store.add_points(set_name, scheme, points)


def add_contracts(set_name, scheme, paths):
    """Chunk and embed these contracts in batches. Returns how many chunks were added."""
    total = 0
    batch_chunks = []
    batch_texts = []

    for file_path in paths:
        text = read_contract(set_name, file_path)
        for chunk in chunks_for_contract(scheme, file_path, text):
            batch_chunks.append(chunk)
            batch_texts.append(search_text(chunk, text))

            if len(batch_chunks) == BATCH_SIZE:
                add_batch(set_name, scheme, batch_chunks, batch_texts)
                total = total + len(batch_chunks)
                logger.info("%s chunks indexed", total)
                batch_chunks = []
                batch_texts = []

    if len(batch_chunks) > 0:
        add_batch(set_name, scheme, batch_chunks, batch_texts)
        total = total + len(batch_chunks)

    return total


def build_index(set_name, scheme):
    paths = list_benchmark_contracts(set_name)
    logger.info("Indexing %s contracts with the %s scheme", len(paths), scheme)
    vector_store.recreate_collection(set_name, scheme)
    total = add_contracts(set_name, scheme, paths)
    logger.info("Done: %s chunks", total)
    return total


def index_one_contract(set_name, file_path):
    """Add or replace one contract without rebuilding the whole index."""
    vector_store.ensure_collection(set_name, "clause")
    vector_store.delete_contract(set_name, "clause", file_path)
    return add_contracts(set_name, "clause", [file_path])
