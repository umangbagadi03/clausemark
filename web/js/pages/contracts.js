import { getContracts, removeContract, uploadContract } from "../api.js";
import { clear, el, formatNumber } from "../dom.js";

function reviewLink(filePath) {
  return "#/review?file=" + encodeURIComponent(filePath);
}

function makeRemoveCell(contract, onRemoved) {
  const cell = el("td", "row-action");
  if (!contract.removable) {
    return cell;
  }

  const button = el("button", "link-button", "Remove");
  button.type = "button";
  button.setAttribute("aria-label", "Remove " + contract.title);
  button.addEventListener("click", async function (event) {
    event.stopPropagation();
    if (window.confirm("Remove " + contract.title + "? This deletes your uploaded copy.")) {
      await removeContract(contract.file_path);
      onRemoved();
    }
  });
  cell.appendChild(button);
  return cell;
}

function makeRow(contract, onRemoved) {
  const row = el("tr", "link-row");

  const titleCell = el("td", "contract-title");
  const link = el("a", "", contract.title);
  link.href = reviewLink(contract.file_path);
  titleCell.appendChild(link);

  row.appendChild(titleCell);
  row.appendChild(el("td", "muted", contract.source));
  row.appendChild(el("td", "number", formatNumber(contract.characters)));
  row.appendChild(el("td", "number", String(contract.questions)));
  row.appendChild(makeRemoveCell(contract, onRemoved));

  row.addEventListener("click", function () {
    window.location.hash = reviewLink(contract.file_path);
  });
  return row;
}

function makeHeader() {
  const head = el("thead");
  const row = el("tr");
  row.appendChild(el("th", "", "Contract"));
  row.appendChild(el("th", "", "Source"));
  row.appendChild(el("th", "number", "Characters"));
  row.appendChild(el("th", "number", "Questions"));
  row.appendChild(el("th", "", ""));
  head.appendChild(row);
  return head;
}

function makeUploadControl(errorLine) {
  const label = el("label", "upload-button", "Add your contract");
  const input = el("input");
  input.type = "file";
  input.accept = ".pdf,.txt";
  input.className = "upload-input";
  label.appendChild(input);

  input.addEventListener("change", async function () {
    if (input.files.length === 0) {
      return;
    }

    label.firstChild.textContent = "Reading and indexing";
    errorLine.hidden = true;

    try {
      const uploaded = await uploadContract(input.files[0]);
      window.location.hash = reviewLink(uploaded.file_path);
    } catch (error) {
      errorLine.textContent = error.message;
      errorLine.hidden = false;
      label.firstChild.textContent = "Add your contract";
      input.value = "";
    }
  });
  return label;
}

function fillSources(select, contracts) {
  const sources = [];
  for (const contract of contracts) {
    if (!sources.includes(contract.source)) {
      sources.push(contract.source);
    }
  }
  sources.sort();

  const allOption = el("option", "", "All sources");
  allOption.value = "";
  select.appendChild(allOption);

  for (const source of sources) {
    const option = el("option", "", source);
    option.value = source;
    select.appendChild(option);
  }
}

export async function showContracts(page) {
  const listing = await getContracts();
  const contracts = listing.contracts;

  function reloadPage() {
    clear(page);
    showContracts(page);
  }

  const wrapper = el("div", "ledger-page");
  const ledger = el("div", "ledger");
  ledger.appendChild(el("h1", "", "Contracts"));
  ledger.appendChild(el("p", "ledger-intro", "Open a contract to ask it questions and see the exact lines behind each answer."));

  const tools = el("div", "ledger-tools");
  const search = el("input");
  search.type = "search";
  search.placeholder = "Search by name";
  search.setAttribute("aria-label", "Search contracts by name");
  const sourceSelect = el("select");
  sourceSelect.setAttribute("aria-label", "Filter by source");
  fillSources(sourceSelect, contracts);
  const uploadError = el("p", "upload-error");
  uploadError.hidden = true;

  tools.appendChild(search);
  tools.appendChild(sourceSelect);
  tools.appendChild(makeUploadControl(uploadError));
  ledger.appendChild(tools);
  ledger.appendChild(uploadError);

  const tableWrap = el("div", "table-wrap");
  const table = el("table");
  table.appendChild(makeHeader());
  const body = el("tbody");
  table.appendChild(body);
  tableWrap.appendChild(table);
  ledger.appendChild(tableWrap);

  function showRows() {
    clear(body);
    const word = search.value.trim().toLowerCase();

    for (const contract of contracts) {
      const matchesWord = contract.title.toLowerCase().includes(word);
      const matchesSource = !sourceSelect.value || contract.source === sourceSelect.value;
      if (matchesWord && matchesSource) {
        body.appendChild(makeRow(contract, reloadPage));
      }
    }
  }

  search.addEventListener("input", showRows);
  sourceSelect.addEventListener("change", showRows);
  showRows();

  wrapper.appendChild(ledger);
  page.appendChild(wrapper);
}
