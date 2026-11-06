import atexit
import threading
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    Modifier,
    SparseVectorParams,
    VectorParams,
)

from clausemark import config
from clausemark.indexing.embeddings import VECTOR_SIZE

# Qdrant local mode keeps everything in a folder, so there is no server to run.
# Only one process can open that folder at a time.
_clients = {}
_lock = threading.Lock()


def get_client(set_name):
    if set_name not in _clients:
        client = QdrantClient(path=config.qdrant_dir(set_name))
        atexit.register(client.close)
        _clients[set_name] = client
    return _clients[set_name]


def point_id(chunk_id):
    """Qdrant ids must be numbers or UUIDs. The same chunk id always gives the same UUID."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def create_collection(client, scheme):
    client.create_collection(
        collection_name=scheme,
        vectors_config={"dense": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)},
        sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
    )


def recreate_collection(set_name, scheme):
    with _lock:
        client = get_client(set_name)
        if client.collection_exists(scheme):
            client.delete_collection(scheme)
        create_collection(client, scheme)


def ensure_collection(set_name, scheme):
    with _lock:
        client = get_client(set_name)
        if not client.collection_exists(scheme):
            create_collection(client, scheme)


def add_points(set_name, scheme, points):
    with _lock:
        get_client(set_name).upsert(collection_name=scheme, points=points)


def make_contract_filter(file_path):
    if file_path is None:
        return None
    condition = FieldCondition(key="file_path", match=MatchValue(value=file_path))
    return Filter(must=[condition])


def delete_contract(set_name, scheme, file_path):
    with _lock:
        client = get_client(set_name)
        if client.collection_exists(scheme):
            client.delete(
                collection_name=scheme,
                points_selector=FilterSelector(filter=make_contract_filter(file_path)),
            )


def count_for_contract(set_name, scheme, file_path):
    with _lock:
        client = get_client(set_name)
        if not client.collection_exists(scheme):
            return 0
        response = client.count(collection_name=scheme, count_filter=make_contract_filter(file_path))
        return response.count


def search(set_name, scheme, using, query, limit, file_path):
    """using is "dense" or "bm25". file_path keeps the search inside one contract."""
    with _lock:
        response = get_client(set_name).query_points(
            collection_name=scheme,
            query=query,
            using=using,
            query_filter=make_contract_filter(file_path),
            limit=limit,
        )

    results = []
    for point in response.points:
        results.append(dict(point.payload))
    return results
