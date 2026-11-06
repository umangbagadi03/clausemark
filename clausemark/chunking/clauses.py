from clausemark.chunking.headings import find_headings
from clausemark.chunking.spans import split_span, trim_span
from clausemark.dataset.corpus import contract_title

# Parents are what the LLM reads, children are what we search.
PARENT_MIN_SIZE = 300
PARENT_MAX_SIZE = 4000
CHILD_SIZE = 500


def make_sections(text):
    """Cut the contract at its headings. Text before the first heading is its own section."""
    headings = find_headings(text)
    sections = []

    if len(headings) == 0 or headings[0]["start"] > 0:
        first_end = len(text)
        if len(headings) > 0:
            first_end = headings[0]["start"]
        sections.append({"start": 0, "end": first_end, "labels": [], "title": "Opening text"})

    for index, heading in enumerate(headings):
        end = len(text)
        if index + 1 < len(headings):
            end = headings[index + 1]["start"]

        labels = []
        if heading["label"]:
            labels.append(heading["label"])

        sections.append({
            "start": heading["start"],
            "end": end,
            "labels": labels,
            "title": heading["title"],
        })

    return sections


def top_number(section):
    """"7.1" and "7.2" both give "7". Other labels and no label give an empty string."""
    if len(section["labels"]) == 0:
        return ""
    label = section["labels"][0]
    if label[0].isdigit():
        return label.split(".")[0]
    return ""


def belongs_together(buffer, section):
    size_together = section["end"] - buffer["start"]
    if size_together > PARENT_MAX_SIZE:
        return False

    # 7, 7.1 and 7.2 are one clause. 6.2 and 7.1 are not.
    if top_number(section) and top_number(section) == top_number(buffer):
        return True

    # A short title with no number, like the contract name, joins the text after it
    buffer_size = buffer["end"] - buffer["start"]
    return buffer_size < PARENT_MIN_SIZE and top_number(buffer) == ""


def merge_sections(sections):
    merged = []
    buffer = None

    for section in sections:
        if buffer is None:
            buffer = dict(section)
        elif belongs_together(buffer, section):
            buffer["end"] = section["end"]
            buffer["labels"] = buffer["labels"] + section["labels"]
        else:
            merged.append(buffer)
            buffer = dict(section)

    if buffer is not None:
        merged.append(buffer)

    return merged


def build_parents(file_path, text):
    sections = merge_sections(make_sections(text))
    parents = []

    for section in sections:
        spans = [trim_span(text, section["start"], section["end"])]
        if section["end"] - section["start"] > PARENT_MAX_SIZE:
            spans = split_span(text, section["start"], section["end"], PARENT_MAX_SIZE)

        for start, end in spans:
            if end <= start:
                continue
            parents.append({
                "parent_id": file_path + "#p" + str(len(parents)),
                "file_path": file_path,
                "start": start,
                "end": end,
                "labels": section["labels"],
                "title": section["title"],
            })

    return parents


def build_children(parent, text):
    # The contract name and clause title go in the search text, not in the span.
    # That helps a query like "the agreement between Acme and Globex" find the right contract.
    header = contract_title(parent["file_path"]) + " | " + parent["title"]
    children = []

    pieces = split_span(text, parent["start"], parent["end"], CHILD_SIZE)
    for number, piece in enumerate(pieces):
        children.append({
            "chunk_id": parent["parent_id"] + "c" + str(number),
            "file_path": parent["file_path"],
            "parent_id": parent["parent_id"],
            "start": piece[0],
            "end": piece[1],
            "header": header,
        })

    return children


def split_clauses(file_path, text):
    parents = build_parents(file_path, text)
    children = []
    for parent in parents:
        children.extend(build_children(parent, text))
    return parents, children
