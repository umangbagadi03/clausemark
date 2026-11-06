from clausemark.chunking.spans import trim_span
from clausemark.dataset.corpus import contract_title

# The same size as the naive method in the LegalBench-RAG paper
FIXED_SIZE = 500


def split_fixed(file_path, text, with_title):
    """Cut every 500 characters. This is the baseline to beat."""
    header = ""
    if with_title:
        header = contract_title(file_path)

    chunks = []
    number = 0

    for position in range(0, len(text), FIXED_SIZE):
        limit = min(position + FIXED_SIZE, len(text))
        start, end = trim_span(text, position, limit)
        if end <= start:
            continue

        chunks.append({
            "chunk_id": file_path + "#f" + str(number),
            "file_path": file_path,
            "parent_id": "",
            "start": start,
            "end": end,
            "header": header,
        })
        number = number + 1

    return chunks
