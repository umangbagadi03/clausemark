import re

# "4.1 Renewal", "4.1. Renewal", "Section 4.1 Renewal", "12) Notices"
# The text after the number must start with a capital, so "30 days after notice" is not a heading.
NUMBERED = re.compile(r"^\s*(?:(?i:section|sec\.|clause)\s+)?(\d{1,2}(?:\.\d{1,3})*)[.):]?\s+[\"“]?[A-Z]")

# "ARTICLE IV", "Article 4"
ARTICLE = re.compile(r"^\s*article\s+([IVXLC]+|\d+)\b", re.IGNORECASE)

# "EXHIBIT A", "Schedule 2", "Annex B"
ATTACHMENT = re.compile(r"^\s*(exhibit|schedule|annex|appendix)\s+([A-Z0-9]{1,3})\b", re.IGNORECASE)

MAX_TITLE_SIZE = 80


def make_title(line):
    title = line.strip()
    if len(title) > MAX_TITLE_SIZE:
        title = title[:MAX_TITLE_SIZE].rstrip() + "..."
    return title


def is_capital_heading(line):
    # "GOVERNING LAW" or "HOW WE USE YOUR DATA", common in privacy policies
    text = line.strip()
    if len(text) < 4 or len(text) > MAX_TITLE_SIZE:
        return False
    if not text.isupper():
        return False
    return len(text.split()) <= 12


def read_heading(line):
    """Return {label, title} if this line starts a new clause, otherwise None."""
    match = ARTICLE.match(line)
    if match:
        return {"label": "Article " + match.group(1).upper(), "title": make_title(line)}

    match = ATTACHMENT.match(line)
    if match:
        label = match.group(1).capitalize() + " " + match.group(2).upper()
        return {"label": label, "title": make_title(line)}

    match = NUMBERED.match(line)
    if match:
        return {"label": match.group(1), "title": make_title(line)}

    if is_capital_heading(line):
        return {"label": "", "title": make_title(line)}

    return None


def find_headings(text):
    """Return every heading with the character position where its line starts."""
    headings = []
    position = 0

    # keepends=True keeps the new lines, so adding up the lengths gives exact positions
    for line in text.splitlines(keepends=True):
        heading = read_heading(line)
        if heading is not None:
            heading["start"] = position
            headings.append(heading)
        position = position + len(line)

    return headings
