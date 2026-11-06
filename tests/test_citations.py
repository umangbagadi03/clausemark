from clausemark.answering.citations import keep_backed_points, locate_quote, verify_citations
from clausemark.answering.parsing import (
    parse_json_reply,
    read_citations,
    read_grade,
    read_points,
)
from clausemark.answering.schema import AnswerPoint, ClauseCitation

TEXT = "Intro.\nThe vendor's total   liability\nis capped at the fees paid. Other text follows here now."
WHOLE_TEXT = [(0, len(TEXT))]
CLAUSES = [{"parent_id": "a#p0", "start": 0, "end": 40}, {"parent_id": "a#p1", "start": 40, "end": len(TEXT)}]


def make_citation(number, quote):
    return ClauseCitation(
        number=number,
        clause_id="what the model said",
        exact_quote=quote,
        explanation="why",
        risk_flag="LOW",
    )


def test_finds_exact_quote():
    start, end = locate_quote(TEXT, "Other text follows here", WHOLE_TEXT)
    assert TEXT[start:end] == "Other text follows here"


def test_allows_different_spacing_and_curly_apostrophe():
    location = locate_quote(TEXT, "The vendor’s total liability is capped", WHOLE_TEXT)
    assert location is not None
    assert TEXT[location[0]:location[1]].startswith("The vendor's")


def test_straight_apostrophe_matches_curly_text():
    text = "each party’s share of the fees"
    assert locate_quote(text, "each party's share of", [(0, len(text))]) is not None


def test_made_up_quote_is_not_found():
    assert locate_quote(TEXT, "the liability is completely unlimited", WHOLE_TEXT) is None


def test_quote_too_short_to_prove_anything_is_rejected():
    assert locate_quote(TEXT, "the fees", WHOLE_TEXT) is None


def test_quote_outside_retrieved_clauses_is_rejected():
    assert locate_quote(TEXT, "Other text follows here", [(0, 10)]) is None


def test_offsets_and_clause_id_come_from_code():
    verified, rejected = verify_citations(TEXT, [make_citation(1, "Other text follows here")], CLAUSES)
    assert rejected == []
    assert TEXT[verified[0].start_char:verified[0].end_char] == "Other text follows here"
    assert verified[0].clause_id == "a#p1"


def test_point_without_a_verified_citation_is_removed():
    good = make_citation(1, "Other text follows here")
    bad = make_citation(2, "this was never written down")
    verified, rejected = verify_citations(TEXT, [good, bad], CLAUSES)
    assert rejected == ["this was never written down"]

    points = [
        AnswerPoint(text="backed", citations=[1, 2]),
        AnswerPoint(text="not backed", citations=[2]),
    ]
    kept = keep_backed_points(points, verified)
    assert len(kept) == 1
    assert kept[0].citations == [1]


def test_parses_reply_inside_a_code_fence():
    assert parse_json_reply('```json\n{"verdict": "enough"}\n```') == {"verdict": "enough"}


def test_reply_that_is_not_an_object_gives_none():
    assert parse_json_reply("[1, 2]") is None
    assert parse_json_reply("no json here") is None


def test_lowercase_risk_flag_is_accepted():
    data = {"citations": [{"number": 1, "clause_id": "x", "exact_quote": "q", "explanation": "e", "risk_flag": "high"}]}
    assert read_citations(data)[0].risk_flag == "HIGH"


def test_bad_citation_is_skipped_and_good_one_kept():
    bad = {"number": 1, "clause_id": "x", "exact_quote": "q", "explanation": "e", "risk_flag": "SEVERE"}
    good = {"number": 2, "clause_id": "x", "exact_quote": "q", "explanation": "e", "risk_flag": "LOW"}
    citations = read_citations({"citations": [bad, "not a citation", good]})
    assert len(citations) == 1
    assert citations[0].number == 2


def test_repeated_citation_number_keeps_the_first():
    first = {"number": 1, "clause_id": "x", "exact_quote": "first", "explanation": "e", "risk_flag": "LOW"}
    second = {"number": 1, "clause_id": "x", "exact_quote": "second", "explanation": "e", "risk_flag": "LOW"}
    citations = read_citations({"citations": [first, second]})
    assert len(citations) == 1
    assert citations[0].exact_quote == "first"


def test_wrong_shapes_do_not_crash():
    assert read_points({"points": "not a list"}) == []
    assert read_citations({"citations": {"a": 1}}) == []
    assert read_points({"points": [{"text": "no citations field"}]}) == []


def test_unreadable_grade_counts_as_enough():
    assert read_grade("garbage").verdict == "enough"
    assert read_grade('{"verdict": "maybe"}').verdict == "enough"
    assert read_grade('{"verdict": "none", "better_query": "indemnity"}').better_query == "indemnity"
