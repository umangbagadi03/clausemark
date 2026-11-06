import { el } from "./dom.js";
import { scrollToClause } from "./contract_view.js";

function clauseLength(clause) {
  return clause.end - clause.start;
}

// A thin strip with one bar per clause, so a reader can see where answers sit in the contract.
export function makeDocMap(contract, desk) {
  const map = el("nav", "docmap");
  map.setAttribute("aria-label", "Jump to a clause");

  for (const clause of contract.clauses) {
    const bar = el("button");
    bar.type = "button";
    bar.title = clause.title;
    bar.setAttribute("aria-label", clause.title);
    bar.dataset.clause = clause.clause_id;
    bar.dataset.start = clause.start;
    bar.dataset.end = clause.end;
    bar.style.flexGrow = clauseLength(clause);
    bar.addEventListener("click", function () {
      scrollToClause(desk, clause.clause_id);
    });
    map.appendChild(bar);
  }
  return map;
}

export function markDocMap(map, result) {
  const bars = map.querySelectorAll("button");

  for (const bar of bars) {
    bar.classList.remove("found", "cited");
    const start = Number(bar.dataset.start);
    const end = Number(bar.dataset.end);

    for (const clause of result.clauses) {
      if (clause.start === start && clause.end === end) {
        bar.classList.add("found");
      }
    }

    for (const citation of result.citations) {
      if (citation.start_char >= start && citation.start_char < end) {
        bar.classList.add("cited");
      }
    }
  }
}
