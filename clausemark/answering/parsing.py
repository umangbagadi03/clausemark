import json

from pydantic import ValidationError

from clausemark.answering.schema import AnswerPoint, ClauseCitation, GradeReply


def parse_json_reply(text):
    """LLMs often wrap JSON in fences or add a sentence around it.
    Take the part between the first '{' and the last '}' and parse that.
    Returns a dict, or None if the reply is not a JSON object."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None

    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None
    return data


def read_list(data, key):
    items = data.get(key, [])
    if isinstance(items, list):
        return items
    return []


def read_citations(data):
    """Bad citations are skipped one by one, so one mistake does not lose the whole answer."""
    citations = []
    used_numbers = set()

    for item in read_list(data, "citations"):
        if not isinstance(item, dict):
            continue

        # Models sometimes write "high" instead of "HIGH"
        item = dict(item)
        item["risk_flag"] = str(item.get("risk_flag", "")).upper()

        try:
            citation = ClauseCitation.model_validate(item)
        except ValidationError:
            continue

        if citation.number not in used_numbers:
            used_numbers.add(citation.number)
            citations.append(citation)

    return citations


def read_points(data):
    points = []
    for item in read_list(data, "points"):
        try:
            points.append(AnswerPoint.model_validate(item))
        except ValidationError:
            continue
    return points


def read_grade(reply_text):
    """A reply we cannot read counts as "enough", so a bad reply never starts a useless new search."""
    data = parse_json_reply(reply_text)
    if data is None:
        return GradeReply(verdict="enough")

    try:
        return GradeReply.model_validate(data)
    except ValidationError:
        return GradeReply(verdict="enough")
