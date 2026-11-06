import re

# A quote of a word or two, like "Section 6", is found almost anywhere and proves nothing
MIN_QUOTE_WORDS = 4


def character_pattern(character):
    if character in "'’":
        return "['’]"
    if character in '"“”':
        return '["“”]'
    return re.escape(character)


def word_pattern(word):
    pattern = ""
    for character in word:
        pattern = pattern + character_pattern(character)
    return pattern


def quote_pattern(quote):
    """Build a pattern that allows different spacing and straight or curly quote marks."""
    parts = []
    for word in quote.split():
        parts.append(word_pattern(word))
    return r"\s+".join(parts)


def locate_quote(text, quote, spans):
    """Find the quote inside the clauses that were retrieved.

    Returns (start, end), or None if the quote is not there or is too short to prove anything.
    An LLM cannot be trusted to count characters, so positions always come from this search.
    """
    if len(quote.split()) < MIN_QUOTE_WORDS:
        return None

    pattern = re.compile(quote_pattern(quote))
    for start, end in spans:
        match = pattern.search(text, start, end)
        if match:
            return match.start(), match.end()
    return None


def verify_citations(text, citations, clauses):
    """Returns the citations found in the clauses, and the quotes that were not.

    The clause id also comes from where the quote was found, not from what the LLM said.
    """
    verified = []
    rejected_quotes = []

    for citation in citations:
        found = False
        for clause in clauses:
            location = locate_quote(text, citation.exact_quote, [(clause["start"], clause["end"])])
            if location is not None:
                citation.start_char = location[0]
                citation.end_char = location[1]
                citation.clause_id = clause["parent_id"]
                verified.append(citation)
                found = True
                break

        if not found:
            rejected_quotes.append(citation.exact_quote)

    return verified, rejected_quotes


def keep_backed_points(points, citations):
    """Drop any answer point that has no verified citation behind it."""
    valid_numbers = set()
    for citation in citations:
        valid_numbers.add(citation.number)

    kept = []
    for point in points:
        backed = []
        for number in point.citations:
            if number in valid_numbers:
                backed.append(number)

        if len(backed) > 0:
            point.citations = backed
            kept.append(point)
    return kept
