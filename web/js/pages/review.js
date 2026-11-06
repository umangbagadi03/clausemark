import { renderAnswer, renderThinking } from "../answer_view.js";
import { askContract, getContract, getContracts } from "../api.js";
import { renderContract, scrollToCitation, setActiveCitation } from "../contract_view.js";
import { makeDocMap, markDocMap } from "../doc_map.js";
import { clear, el } from "../dom.js";

function makeContractPicker(contracts, currentPath) {
  const picker = el("select", "contract-picker");
  picker.setAttribute("aria-label", "Open a contract");

  for (const contract of contracts) {
    const option = el("option", "", contract.title);
    option.value = contract.file_path;
    picker.appendChild(option);
  }
  picker.value = currentPath;

  picker.addEventListener("change", function () {
    window.location.hash = "#/review?file=" + encodeURIComponent(picker.value);
  });
  return picker;
}

function findGoldSpans(contract, question) {
  for (const item of contract.questions) {
    if (item.question === question) {
      return item.snippets;
    }
  }
  return [];
}

function makeAskForm() {
  const form = el("form", "ask-form");

  const label = el("label", "", "What do you need to find in this contract?");
  label.htmlFor = "question";

  const box = el("div", "ask-box");
  const textarea = el("textarea");
  textarea.id = "question";
  textarea.placeholder = "How much notice does the vendor need to terminate?";

  const row = el("div", "ask-row");
  row.appendChild(el("span", "", "Answers only from this contract"));
  const submit = el("button", "button", "Find clauses");
  submit.type = "submit";
  row.appendChild(submit);

  box.appendChild(textarea);
  box.appendChild(row);

  const errorLine = el("p", "ask-error");
  errorLine.hidden = true;

  form.appendChild(label);
  form.appendChild(box);
  form.appendChild(errorLine);

  return { form: form, textarea: textarea, submit: submit, errorLine: errorLine };
}

function makeQuestionList(contract, onPick) {
  const section = el("section", "panel-section");
  section.appendChild(el("h2", "eyebrow", "Try a question"));

  const list = el("ul", "question-list");
  const shown = contract.questions.slice(0, 5);
  for (const item of shown) {
    const row = el("li");
    const button = el("button", "", item.question);
    button.type = "button";
    button.addEventListener("click", function () {
      onPick(item.question);
    });
    row.appendChild(button);
    list.appendChild(row);
  }
  section.appendChild(list);
  return section;
}

export async function showReview(page, contractSlot, requestedFile) {
  const listing = await getContracts();

  let filePath = requestedFile;
  if (!filePath) {
    filePath = listing.contracts[0].file_path;
  }

  const contract = await getContract(filePath);
  contractSlot.appendChild(makeContractPicker(listing.contracts, filePath));

  const review = el("div", "review");
  const panel = el("aside", "panel");
  const desk = el("div", "desk");
  const map = makeDocMap(contract, desk);

  const ask = makeAskForm();
  const answerArea = el("div");
  const questionList = makeQuestionList(contract, function (question) {
    ask.textarea.value = question;
    ask.form.requestSubmit();
  });

  panel.appendChild(ask.form);
  panel.appendChild(answerArea);
  if (contract.questions.length > 0) {
    panel.appendChild(questionList);
  }

  const actions = {
    goToCitation: function (number) {
      scrollToCitation(desk, number);
    },
    hoverCitation: function (number) {
      setActiveCitation(desk, number);
    },
  };

  ask.form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const question = ask.textarea.value.trim();
    if (!question) {
      ask.textarea.focus();
      return;
    }

    ask.submit.disabled = true;
    ask.submit.textContent = "Searching";
    ask.errorLine.hidden = true;
    renderThinking(answerArea);

    try {
      const result = await askContract(contract.file_path, question);
      renderAnswer(answerArea, result, actions);
      renderContract(desk, contract, result, findGoldSpans(contract, question));
      markDocMap(map, result);
      if (result.citations.length > 0) {
        actions.goToCitation(result.citations[0].number);
      }
    } catch (error) {
      clear(answerArea);
      ask.errorLine.textContent = error.message;
      ask.errorLine.hidden = false;
    }

    ask.submit.disabled = false;
    ask.submit.textContent = "Find clauses";
  });

  ask.textarea.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ask.form.requestSubmit();
    }
  });

  renderContract(desk, contract, null, []);

  review.appendChild(panel);
  review.appendChild(desk);
  review.appendChild(map);
  page.appendChild(review);
}
