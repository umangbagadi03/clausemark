import { clear, el, formatNumber } from "./dom.js";

function makePoints(result, actions) {
  const list = el("ul", "answer-points");

  for (const point of result.points) {
    const item = el("li", "", point.text);
    for (const number of point.citations) {
      const link = el("button", "cite-link", String(number));
      link.type = "button";
      link.setAttribute("aria-label", "Show quote " + number + " in the contract");
      link.addEventListener("click", function () {
        actions.goToCitation(number);
      });
      item.appendChild(link);
    }
    list.appendChild(item);
  }
  return list;
}

function makeCitation(citation, actions) {
  const button = el("button", "citation");
  button.type = "button";

  const head = el("div", "citation-head");
  head.appendChild(el("span", "citation-number", String(citation.number)));
  const place = "chars " + formatNumber(citation.start_char) + "-" + formatNumber(citation.end_char);
  head.appendChild(el("span", "", place));

  const riskWords = citation.risk_flag.charAt(0) + citation.risk_flag.slice(1).toLowerCase() + " risk";
  head.appendChild(el("span", "risk " + citation.risk_flag, riskWords));

  button.appendChild(head);
  button.appendChild(el("p", "citation-quote", citation.exact_quote));
  button.appendChild(el("p", "citation-why", citation.explanation));

  button.addEventListener("click", function () {
    actions.goToCitation(citation.number);
  });
  button.addEventListener("mouseenter", function () {
    actions.hoverCitation(citation.number);
  });
  button.addEventListener("mouseleave", function () {
    actions.hoverCitation(null);
  });
  return button;
}

function makeAudit(result) {
  const section = el("section", "panel-section");
  const details = el("details", "audit");
  details.appendChild(el("summary", "", "How this answer was checked"));

  const list = el("ol");
  for (const step of result.steps) {
    list.appendChild(el("li", "", step));
  }
  details.appendChild(list);
  details.appendChild(el("p", "audit-foot", result.model + ", " + result.seconds + "s"));

  section.appendChild(details);
  return section;
}

export function renderThinking(container) {
  clear(container);
  const block = el("section", "thinking");
  block.appendChild(el("p", "", "Searching clauses and checking quotes. A free API tier can take up to a minute."));
  block.appendChild(el("span"));
  block.appendChild(el("span"));
  block.appendChild(el("span"));
  container.appendChild(block);
}

export function renderAnswer(container, result, actions) {
  clear(container);

  const answerSection = el("section", "panel-section");
  answerSection.appendChild(el("h2", "eyebrow", "Answer"));

  if (result.found) {
    answerSection.appendChild(makePoints(result, actions));
  } else {
    answerSection.appendChild(el("p", "not-found", "No clause in this contract answers that."));
    answerSection.appendChild(el("p", "not-found-hint", "Nothing was verified, so no answer is shown. Try the legal term, like \"termination\" or \"indemnification\"."));
  }
  container.appendChild(answerSection);

  if (result.citations.length > 0) {
    const quoteSection = el("section", "panel-section");
    quoteSection.appendChild(el("h2", "eyebrow", "Quotes found in the contract"));
    for (const citation of result.citations) {
      quoteSection.appendChild(makeCitation(citation, actions));
    }
    container.appendChild(quoteSection);
  }

  container.appendChild(makeAudit(result));
}
