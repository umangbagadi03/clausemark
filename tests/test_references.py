from clausemark.retrieval.references import find_references


def test_finds_one_section():
    assert find_references("as defined in Section 1.4 of this") == ["1.4"]


def test_finds_section_list():
    assert find_references("under Sections 4.1 and 4.2") == ["4.1", "4.2"]


def test_ignores_letter_after_section_number():
    assert find_references("the exceptions in Section 4.1(b)") == ["4.1"]


def test_finds_article_and_exhibit():
    labels = find_references("subject to Article IV and Exhibit A")
    assert "Article IV" in labels
    assert "Exhibit A" in labels


def test_plain_words_are_not_references():
    assert find_references("this section applies to the exhibit hall") == []


def test_number_after_the_reference_is_not_a_section():
    assert find_references("under Section 4 within 5 days") == ["4"]


def test_nested_brackets_do_not_add_a_section():
    assert find_references("see Section 4.1(b)(1)") == ["4.1"]


def test_repeats_are_removed():
    assert find_references("Section 6 and again Section 6") == ["6"]
