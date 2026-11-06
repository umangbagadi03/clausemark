import { clear, el, formatNumber } from "./dom.js";

const MAX_TITLE_LINE = 90;

// "7.1 Cap." gives the number and the short title at the start of a paragraph
const SUB_CLAUSE = /^(\d{1,2}\.\d{1,3}\.?)\s+([A-Z][^.\n]{1,50}\.(?=\s))?/;
const TITLE_LINE = /^(\d{1,2}\.?\s+[A-Z]|(Exhibit|Schedule|Annex|Appendix|Article)\s+\w+$|[^a-z]+$)/;

// Cut the contract into blocks, one per clause.
function makeBlocks(contract) {
  const blocks = [];
  const clauses = contract.clauses;

  for (let index = 0; index < clauses.length; index = index + 1) {
    let start = clauses[index].start;
    if (index === 0) {
      start = 0;
    }

    let end = contract.text.length;
    if (index + 1 < clauses.length) {
      end = clauses[index + 1].start;
    }

    blocks.push({ clause: clauses[index], start: start, end: end });
  }
  return blocks;
}

// Find paragraphs by their blank lines, and keep their exact character positions.
function findParagraphs(text, blockStart, blockEnd) {
  const paragraphs = [];
  const blankLine = /\n\s*\n/g;
  blankLine.lastIndex = blockStart;

  let start = blockStart;
  let match = blankLine.exec(text);

  while (match !== null && match.index < blockEnd) {
    addParagraph(paragraphs, text, start, match.index);
    start = match.index + match[0].length;
    match = blankLine.exec(text);
  }

  addParagraph(paragraphs, text, start, blockEnd);
  return paragraphs;
}

function addParagraph(paragraphs, text, start, end) {
  let cleanStart = start;
  let cleanEnd = end;

  while (cleanStart < cleanEnd && /\s/.test(text[cleanStart])) {
    cleanStart = cleanStart + 1;
  }
  while (cleanEnd > cleanStart && /\s/.test(text[cleanEnd - 1])) {
    cleanEnd = cleanEnd - 1;
  }

  if (cleanEnd > cleanStart) {
    paragraphs.push({ start: cleanStart, end: cleanEnd });
  }
}

function makeAnswerMarks(result, goldSpans) {
  const marks = [];

  if (result) {
    for (const citation of result.citations) {
      marks.push({ kind: "cited", start: citation.start_char, end: citation.end_char, number: citation.number });
    }
  }

  for (const span of goldSpans) {
    marks.push({ kind: "gold", start: span.start, end: span.end });
  }
  return marks;
}

function makeStyleMarks(text, paragraph) {
  const piece = text.slice(paragraph.start, paragraph.end);
  const match = SUB_CLAUSE.exec(piece);
  const marks = [];

  if (match === null) {
    return marks;
  }

  const numberEnd = paragraph.start + match[1].length;
  marks.push({ kind: "number", start: paragraph.start, end: numberEnd });

  if (match[2]) {
    const titleEnd = paragraph.start + match[0].length;
    marks.push({ kind: "run-in", start: titleEnd - match[2].length, end: titleEnd });
  }
  return marks;
}

function findCutPoints(paragraph, marks) {
  const points = [paragraph.start, paragraph.end];

  for (const mark of marks) {
    if (mark.start > paragraph.start && mark.start < paragraph.end) {
      points.push(mark.start);
    }
    if (mark.end > paragraph.start && mark.end < paragraph.end) {
      points.push(mark.end);
    }
  }

  const unique = Array.from(new Set(points));
  unique.sort(function (first, second) {
    return first - second;
  });
  return unique;
}

function wrap(node, tagName, className) {
  const wrapper = el(tagName, className);
  wrapper.appendChild(node);
  return wrapper;
}

function makeSegment(text, start, end, marks) {
  let node = document.createTextNode(text.slice(start, end));
  let citedMark = null;

  for (const mark of marks) {
    if (mark.start <= start && mark.end >= end) {
      if (mark.kind === "number") {
        node = wrap(node, "span", "sub-number");
      } else if (mark.kind === "run-in") {
        node = wrap(node, "span", "run-in");
      } else if (mark.kind === "gold") {
        node = wrap(node, "span", "gold");
      } else {
        citedMark = mark;
      }
    }
  }

  if (citedMark === null) {
    return node;
  }

  const markElement = wrap(node, "mark", "cited");
  markElement.dataset.citation = citedMark.number;

  const fragment = document.createDocumentFragment();
  fragment.appendChild(markElement);
  if (citedMark.end === end) {
    fragment.appendChild(el("sup", "cite-number", String(citedMark.number)));
  }
  return fragment;
}

function isTitleLine(text, paragraph) {
  const piece = text.slice(paragraph.start, paragraph.end);
  if (piece.length > MAX_TITLE_LINE || piece.includes("\n")) {
    return false;
  }
  if (SUB_CLAUSE.test(piece) || piece.endsWith(".")) {
    return false;
  }
  return TITLE_LINE.test(piece);
}

function findClauseTag(block, result) {
  if (!result) {
    return null;
  }
  for (const clause of result.clauses) {
    if (clause.start === block.clause.start && clause.end === block.clause.end) {
      if (!clause.reached_by) {
        return "Matched the search";
      }
      if (/^\d/.test(clause.reached_by)) {
        return "Followed from a reference to Section " + clause.reached_by;
      }
      return "Followed from a reference to " + clause.reached_by;
    }
  }
  return null;
}

function makeClauseElement(contract, block, answerMarks, result) {
  const clauseElement = el("section", "clause");
  clauseElement.dataset.clause = block.clause.clause_id;
  clauseElement.appendChild(el("div", "clause-offset", formatNumber(block.start)));

  const body = el("div", "clause-body");
  const tag = findClauseTag(block, result);
  if (tag) {
    clauseElement.classList.add("found");
    body.appendChild(el("p", "clause-tag", tag));
  }

  for (const paragraph of findParagraphs(contract.text, block.start, block.end)) {
    const marks = makeStyleMarks(contract.text, paragraph).concat(answerMarks);

    let className = "para";
    if (isTitleLine(contract.text, paragraph)) {
      className = "clause-title";
    }
    const element = el("p", className);

    const points = findCutPoints(paragraph, marks);
    for (let pointIndex = 0; pointIndex + 1 < points.length; pointIndex = pointIndex + 1) {
      element.appendChild(makeSegment(contract.text, points[pointIndex], points[pointIndex + 1], marks));
    }
    body.appendChild(element);
  }

  clauseElement.appendChild(body);
  return clauseElement;
}

function makeLegendItem(keyClass, words) {
  const item = el("span");
  item.appendChild(el("i", keyClass));
  item.appendChild(document.createTextNode(words));
  return item;
}

function makeLegend(result, goldSpans) {
  const legend = el("div", "legend");
  if (result && result.citations.length > 0) {
    legend.appendChild(makeLegendItem("key-cited", "Verified quote"));
  }
  if (result && result.clauses.length > 0) {
    legend.appendChild(makeLegendItem("key-found", "Clause sent to the model"));
  }
  if (goldSpans.length > 0) {
    legend.appendChild(makeLegendItem("key-gold", "Benchmark answer"));
  }
  return legend;
}

export function renderContract(container, contract, result, goldSpans) {
  clear(container);

  const sheet = el("article", "sheet");
  const head = el("header", "sheet-head");
  head.appendChild(el("h1", "", contract.title));

  let clauseCount = String(contract.clauses.length) + " clauses";
  if (contract.clauses.length === 1) {
    clauseCount = "1 clause";
  }
  const sizeText = formatNumber(contract.text.length) + " characters";
  head.appendChild(el("p", "sheet-meta", clauseCount + ", " + sizeText));
  head.appendChild(makeLegend(result, goldSpans));
  sheet.appendChild(head);

  const answerMarks = makeAnswerMarks(result, goldSpans);
  for (const block of makeBlocks(contract)) {
    sheet.appendChild(makeClauseElement(contract, block, answerMarks, result));
  }

  container.appendChild(sheet);
}

export function setActiveCitation(container, number) {
  const marks = container.querySelectorAll("mark.cited");
  for (const mark of marks) {
    if (mark.dataset.citation === String(number)) {
      mark.classList.add("active");
    } else {
      mark.classList.remove("active");
    }
  }
}

export function scrollToCitation(container, number) {
  const mark = container.querySelector('mark[data-citation="' + number + '"]');
  if (mark === null) {
    return;
  }

  mark.scrollIntoView({ block: "center" });
  setActiveCitation(container, number);

  window.setTimeout(function () {
    setActiveCitation(container, null);
  }, 1500);
}

export function scrollToClause(container, clauseId) {
  const clauses = container.querySelectorAll(".clause");
  for (const clause of clauses) {
    if (clause.dataset.clause === clauseId) {
      clause.scrollIntoView({ block: "start" });
      return;
    }
  }
}
