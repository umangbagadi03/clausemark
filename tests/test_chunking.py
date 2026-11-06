from clausemark.chunking.clauses import split_clauses
from clausemark.chunking.fixed import split_fixed
from clausemark.chunking.headings import find_headings, read_heading

CONTRACT = """MASTER AGREEMENT

This agreement is between two companies and sets out how they will work together over the term.

1. Definitions

1.1 "Fees" means the amounts in Schedule 2, payable each month by the client to the vendor under this agreement.

2. Term

2.1 Renewal. This agreement renews every year unless a party gives notice of non-renewal at least ninety days before the end of the period, in writing, to the address on the last invoice.

EXHIBIT A

The services are hosted software with support on business days. Availability is measured every month.
"""


def test_reads_numbered_heading():
    assert read_heading("4.1 Renewal. This renews")["label"] == "4.1"


def test_reads_section_word():
    assert read_heading("Section 12 Notices")["label"] == "12"


def test_reads_article_and_exhibit():
    assert read_heading("ARTICLE iv")["label"] == "Article IV"
    assert read_heading("EXHIBIT A")["label"] == "Exhibit A"


def test_normal_sentence_is_not_a_heading():
    assert read_heading("The parties agree to the following terms.") is None
    assert read_heading("30 days after notice") is None


def test_heading_positions_are_exact():
    for heading in find_headings(CONTRACT):
        line = CONTRACT[heading["start"]:].splitlines()[0]
        assert heading["title"] == line.strip()[:83] or line.strip().startswith(heading["title"][:40])


def test_clause_spans_point_at_the_contract_text():
    parents, children = split_clauses("a.txt", CONTRACT)
    assert len(parents) > 0
    for parent in parents:
        assert CONTRACT[parent["start"]] != " "
        assert 0 <= parent["start"] < parent["end"] <= len(CONTRACT)
    for child in children:
        assert child["end"] - child["start"] <= 500
        assert CONTRACT[child["start"]:child["end"]].strip() != ""


def test_subclauses_stay_with_their_clause_and_not_the_next_one():
    text = (
        "6. Confidentiality\n\n6.1 Duty. Keep information safe.\n\n6.2 Duration. Five years.\n\n"
        "7. Liability\n\n7.1 Cap. Fees paid in twelve months.\n"
    )
    parents, children = split_clauses("a.txt", text)
    assert parents[0]["labels"] == ["6", "6.1", "6.2"]
    assert parents[1]["labels"] == ["7", "7.1"]
    assert parents[1]["title"] == "7. Liability"


def test_no_text_is_lost_between_clauses():
    parents, children = split_clauses("a.txt", CONTRACT)
    assert "Availability is measured" in CONTRACT[parents[-1]["start"]:parents[-1]["end"]]
    joined = ""
    for parent in parents:
        joined = joined + CONTRACT[parent["start"]:parent["end"]]
    assert "".join(joined.split()) == "".join(CONTRACT.split())


def test_contract_with_no_headings_still_splits():
    text = "plain words in a long paragraph. " * 400
    parents, children = split_clauses("b.txt", text)
    assert len(parents) > 1
    for parent in parents:
        assert parent["end"] - parent["start"] <= 4000


def test_fixed_chunks_stay_inside_the_text():
    chunks = split_fixed("a.txt", "x" * 1234, False)
    assert len(chunks) == 3
    assert chunks[-1]["end"] == 1234
