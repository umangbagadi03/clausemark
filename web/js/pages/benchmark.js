import { getBenchmark } from "../api.js";
import { clear, el, formatNumber } from "../dom.js";

// The first column is drawn as a bar, the others are plain numbers
const COLUMNS = [
  { title: "Recall@4", key: "k4", field: "recall", bar: true },
  { title: "Precision@4", key: "k4", field: "precision", bar: false },
  { title: "Recall@16", key: "k16", field: "recall", bar: false },
  { title: "Recall, 5k chars", key: "budget5000", field: "recall", bar: false },
  { title: "Precision, 5k chars", key: "budget5000", field: "precision", bar: false },
];

const SCOPE_NAMES = {
  corpus: "Searching every contract",
  contract: "Searching only the open contract",
};

function percent(value) {
  return (value * 100).toFixed(1);
}

function scoresFor(result, group) {
  if (group === "all") {
    return result.overall;
  }
  return result.by_benchmark[group];
}

function findBest(results, group, column) {
  let best = -1;
  for (const result of results) {
    const scores = scoresFor(result, group);
    if (scores[column.key][column.field] > best) {
      best = scores[column.key][column.field];
    }
  }
  return best;
}

function makeHeader() {
  const head = el("thead");
  const row = el("tr");
  row.appendChild(el("th", "", "Recipe"));
  for (const column of COLUMNS) {
    row.appendChild(el("th", "number", column.title));
  }
  head.appendChild(row);
  return head;
}

function makeBarCell(value, title) {
  const cell = el("td", "number");
  cell.title = title + ": " + percent(value) + "%";

  const barCell = el("div", "bar-cell");
  const track = el("span", "bar-track");
  const fill = el("span", "bar-fill");
  fill.style.width = percent(value) + "%";
  track.appendChild(fill);
  barCell.appendChild(track);
  barCell.appendChild(el("span", "", percent(value)));

  cell.appendChild(barCell);
  return cell;
}

function makeRow(result, results, group) {
  const scores = scoresFor(result, group);
  const row = el("tr");

  const nameCell = el("td", "recipe-name");
  nameCell.appendChild(el("small", "", result.recipe.split("_")[0]));
  nameCell.appendChild(document.createTextNode(result.label));
  row.appendChild(nameCell);

  for (const column of COLUMNS) {
    const value = scores[column.key][column.field];
    if (column.bar) {
      row.appendChild(makeBarCell(value, column.title));
    } else {
      const cell = el("td", "number", percent(value));
      if (value === findBest(results, group, column) && value > 0) {
        cell.classList.add("best");
      }
      row.appendChild(cell);
    }
  }
  return row;
}

function makeGroupRow(scope) {
  const row = el("tr", "group-row");
  const cell = el("td", "", SCOPE_NAMES[scope]);
  cell.colSpan = COLUMNS.length + 1;
  row.appendChild(cell);
  return row;
}

function makeNotes(results) {
  const notes = el("div", "method-notes");
  notes.appendChild(el("h2", "", "How to read this"));

  const list = el("ul");
  const items = [
    "Recall is the share of the answer's characters that were retrieved. Precision is the share of retrieved characters that belong to the answer.",
    "No LLM is involved. These numbers compare character positions with the marked answers.",
    "The 5k columns stop reading after 5,000 characters, so a recipe cannot win only by returning more text.",
    formatNumber(results[0].questions) + " questions per recipe. A dot marks the best value in a column.",
  ];
  for (const item of items) {
    list.appendChild(el("li", "", item));
  }
  notes.appendChild(list);
  return notes;
}

function makeAnswerScore(value, words) {
  const box = el("div", "answer-score");
  box.appendChild(el("strong", "", value));
  box.appendChild(el("span", "", words));
  return box;
}

function makeAnswersBlock(answers) {
  const block = el("section", "answers-block");
  block.appendChild(el("h2", "", "Full agent, with the LLM"));
  block.appendChild(el(
    "p",
    "",
    "Do the agent's verified quotes overlap the marked answer? " + answers.questions + " questions, " + answers.model + "."
  ));

  const scores = el("div", "answer-scores");
  scores.appendChild(makeAnswerScore(percent(answers.quote_recall) + "%", "Quote recall"));
  scores.appendChild(makeAnswerScore(percent(answers.quote_precision) + "%", "Quote precision"));
  scores.appendChild(makeAnswerScore(percent(answers.answered_share) + "%", "Questions answered"));
  scores.appendChild(makeAnswerScore(percent(answers.rejected_quote_share) + "%", "Quotes rejected by the check"));
  scores.appendChild(makeAnswerScore(answers.average_seconds + "s", "Average time"));
  block.appendChild(scores);
  return block;
}

function makeSampleWarning() {
  const note = el("p", "warning-note");
  note.appendChild(el("strong", "", "Sample data. "));
  note.appendChild(document.createTextNode(
    "These numbers come from two made-up contracts. They show that the pipeline runs and say nothing about real performance."
  ));
  return note;
}

export async function showBenchmark(page) {
  const data = await getBenchmark();
  const results = data.results;

  const wrapper = el("div", "ledger-page");
  const ledger = el("div", "ledger");
  ledger.appendChild(el("h1", "", "Retrieval benchmark"));
  ledger.appendChild(el(
    "p",
    "ledger-intro",
    "Each recipe adds one change to the one before it, so you can see what that change did."
  ));

  if (data.set === "sample") {
    ledger.appendChild(makeSampleWarning());
  }

  if (results.length === 0) {
    ledger.appendChild(el("p", "empty-note", "No results yet. Run: python main.py experiment"));
    wrapper.appendChild(ledger);
    page.appendChild(wrapper);
    return;
  }

  const tools = el("div", "ledger-tools");
  const groupNames = Object.keys(results[0].by_benchmark);
  const groupSelect = el("select");
  groupSelect.setAttribute("aria-label", "Benchmark group");
  groupSelect.hidden = groupNames.length < 2;

  const allOption = el("option", "", "All questions");
  allOption.value = "all";
  groupSelect.appendChild(allOption);
  for (const name of groupNames) {
    const option = el("option", "", name);
    option.value = name;
    groupSelect.appendChild(option);
  }
  tools.appendChild(groupSelect);
  ledger.appendChild(tools);

  const tableWrap = el("div", "table-wrap");
  const table = el("table");
  table.appendChild(makeHeader());
  const body = el("tbody");
  table.appendChild(body);
  tableWrap.appendChild(table);
  ledger.appendChild(tableWrap);
  ledger.appendChild(makeNotes(results));
  if (data.answers) {
    ledger.appendChild(makeAnswersBlock(data.answers));
  }

  function showRows() {
    clear(body);
    let previousScope = null;
    for (const result of results) {
      if (result.scope !== previousScope) {
        body.appendChild(makeGroupRow(result.scope));
      }
      body.appendChild(makeRow(result, results, groupSelect.value));
      previousScope = result.scope;
    }
  }

  groupSelect.addEventListener("change", showRows);
  showRows();

  wrapper.appendChild(ledger);
  page.appendChild(wrapper);
}
