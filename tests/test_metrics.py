from clausemark.evaluation.metrics import merge_spans, score_retrieval, trim_to_budget


def span(start, end, file_path="a.txt"):
    return {"file_path": file_path, "start": start, "end": end}


def test_merge_joins_overlapping_spans():
    assert merge_spans([(10, 20), (0, 5), (15, 30)]) == [(0, 5), (10, 30)]


def test_perfect_match():
    score = score_retrieval([span(10, 20)], [span(10, 20)])
    assert score["precision"] == 1.0
    assert score["recall"] == 1.0


def test_half_overlap():
    score = score_retrieval([span(0, 20)], [span(10, 30)])
    assert score["precision"] == 0.5
    assert score["recall"] == 0.5


def test_overlapping_results_are_not_counted_twice():
    score = score_retrieval([span(0, 10), span(0, 10)], [span(0, 10)])
    assert score["recall"] == 1.0
    assert score["chars"] == 10


def test_other_file_does_not_count():
    score = score_retrieval([span(0, 10, "b.txt")], [span(0, 10, "a.txt")])
    assert score["recall"] == 0.0


def test_nothing_retrieved():
    score = score_retrieval([], [span(0, 10)])
    assert score["precision"] == 0.0
    assert score["recall"] == 0.0


def test_budget_cuts_the_last_result():
    kept = trim_to_budget([span(0, 100), span(200, 400), span(500, 600)], 150)
    assert len(kept) == 2
    assert kept[1]["end"] == 250
