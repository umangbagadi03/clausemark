def trim_span(text, start, end):
    """Move start and end inwards past spaces and new lines."""
    while start < end and text[start].isspace():
        start = start + 1
    while end > start and text[end - 1].isspace():
        end = end - 1
    return start, end


def find_cut(text, start, limit):
    """Find a good place to cut text[start:limit]: a new line, else a sentence end."""
    if limit >= len(text):
        return len(text)

    # Do not cut in the first half, or the pieces become very short
    middle = start + (limit - start) // 2

    position = text.rfind("\n", middle, limit)
    if position != -1:
        return position + 1

    position = text.rfind(". ", middle, limit)
    if position != -1:
        return position + 2

    return limit


def split_span(text, start, end, max_size):
    """Split one span into pieces of at most max_size characters, without overlap."""
    pieces = []
    position = start

    while position < end:
        limit = min(position + max_size, end)
        if limit == end:
            cut = end
        else:
            cut = find_cut(text, position, limit)

        piece_start, piece_end = trim_span(text, position, cut)
        if piece_end > piece_start:
            pieces.append((piece_start, piece_end))
        position = cut

    return pieces
