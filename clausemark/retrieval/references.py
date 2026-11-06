import re

from clausemark.chunking.clause_store import find_parent_by_label

# One number like 4.1 or 4.1(b)(ii)
ONE_NUMBER = r"\d{1,2}(?:\.\d{1,3})*(?:\([a-z0-9]+\))*"

# "Section 4.1", "Sections 4.1 and 4.2", "Clause 9"
SECTION_LIST = re.compile(
    r"\b(?i:sections?|clauses?|paragraphs?)\s+(" + ONE_NUMBER + r"(?:\s*(?:,|and|or)\s*" + ONE_NUMBER + r")*)"
)
BRACKETS = re.compile(r"\([a-z0-9]+\)")
SECTION_NUMBER = re.compile(r"\d{1,2}(?:\.\d{1,3})*")

# "Article IV"
ARTICLE = re.compile(r"\b(?i:article)\s+([IVXLC]+|\d+)\b")

# "Exhibit A", "Schedule 2". The name must be a capital or a number, so "the exhibit hall" does not match.
ATTACHMENT = re.compile(r"\b((?i:exhibit|schedule|annex|appendix))\s+([A-Z0-9]{1,3})\b")

MAX_REFERENCES_PER_CLAUSE = 3


def find_references(text):
    """Return the labels that this text points to, grouped by kind."""
    labels = []

    for match in SECTION_LIST.finditer(text):
        # Remove (b) first, so "4.1(b)(1)" gives 4.1 and not also 1
        numbers = BRACKETS.sub("", match.group(1))
        for number in SECTION_NUMBER.findall(numbers):
            labels.append(number)

    for match in ARTICLE.finditer(text):
        labels.append("Article " + match.group(1).upper())

    for match in ATTACHMENT.finditer(text):
        labels.append(match.group(1).capitalize() + " " + match.group(2).upper())

    unique_labels = []
    for label in labels:
        if label not in unique_labels:
            unique_labels.append(label)
    return unique_labels


def add_referenced_clauses(set_name, results, read_text):
    """Put each clause that a result points to right after that result.

    read_text(result) returns the text of a result. There is no LLM here,
    only regular expressions and a lookup in the same contract.
    """
    expanded = []
    seen = set()

    for result in results:
        key = (result["file_path"], result["start"], result["end"])
        if key in seen:
            continue
        seen.add(key)
        expanded.append(result)

        labels = find_references(read_text(result))[:MAX_REFERENCES_PER_CLAUSE]
        for label in labels:
            parent = find_parent_by_label(set_name, result["file_path"], label)
            if parent is None:
                continue

            parent_key = (parent["file_path"], parent["start"], parent["end"])
            if parent_key in seen:
                continue
            seen.add(parent_key)

            referenced = dict(parent)
            referenced["reached_by"] = label
            expanded.append(referenced)

    return expanded
