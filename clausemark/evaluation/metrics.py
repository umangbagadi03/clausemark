def merge_spans(spans):
    """Join spans that overlap, so no character is counted twice."""
    if len(spans) == 0:
        return []

    ordered = sorted(spans)
    merged = [ordered[0]]

    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def group_spans_by_file(items):
    grouped = {}
    for item in items:
        file_path = item["file_path"]
        if file_path not in grouped:
            grouped[file_path] = []
        grouped[file_path].append((item["start"], item["end"]))

    for file_path in grouped:
        grouped[file_path] = merge_spans(grouped[file_path])
    return grouped


def total_length(spans_by_file):
    total = 0
    for spans in spans_by_file.values():
        for start, end in spans:
            total = total + (end - start)
    return total


def overlap_length(first_spans, second_spans):
    total = 0
    for first_start, first_end in first_spans:
        for second_start, second_end in second_spans:
            overlap = min(first_end, second_end) - max(first_start, second_start)
            if overlap > 0:
                total = total + overlap
    return total


def score_retrieval(retrieved, gold):
    """Character-level precision and recall, the metric of the LegalBench-RAG paper.

    The paper counts a character twice if two results overlap. Here spans are merged
    first, because parents and references can overlap. For chunks that do not overlap
    the numbers are the same.
    """
    retrieved_by_file = group_spans_by_file(retrieved)
    gold_by_file = group_spans_by_file(gold)

    relevant = 0
    for file_path, gold_spans in gold_by_file.items():
        retrieved_spans = retrieved_by_file.get(file_path, [])
        relevant = relevant + overlap_length(retrieved_spans, gold_spans)

    retrieved_total = total_length(retrieved_by_file)
    gold_total = total_length(gold_by_file)

    precision = 0.0
    if retrieved_total > 0:
        precision = relevant / retrieved_total

    recall = 0.0
    if gold_total > 0:
        recall = relevant / gold_total

    return {"precision": precision, "recall": recall, "chars": retrieved_total}


def trim_to_budget(results, budget):
    """Keep results in rank order until the character budget is used up.

    A fixed budget makes recipes fair to compare. Returning a 4000 character
    clause finds more than a 500 character chunk, but it also costs more.
    """
    kept = []
    used = 0

    for result in results:
        size = result["end"] - result["start"]
        room = budget - used
        if room <= 0:
            break

        if size <= room:
            kept.append(result)
            used = used + size
        else:
            cut = dict(result)
            cut["end"] = result["start"] + room
            kept.append(cut)
            used = budget

    return kept
