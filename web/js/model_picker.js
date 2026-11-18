import { el } from "./dom.js";

// The choice and key live in sessionStorage, so they are gone when the tab closes.
const STORAGE_KEY = "clausemark-model";

const VISITOR_CHOICES = [
  { value: "gemini", label: "Gemini, with your key" },
  { value: "anthropic", label: "Claude, with your key" },
  { value: "openai", label: "OpenAI, with your key" },
];

function readSaved() {
  try {
    const saved = window.sessionStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (error) {
    // Storage can be blocked. The picker still works, it just forgets.
  }
  return null;
}

function save(provider, apiKey) {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ provider: provider, apiKey: apiKey }));
  } catch (error) {
    // Same as above
  }
}

function needsKey(provider) {
  for (const choice of VISITOR_CHOICES) {
    if (choice.value === provider) {
      return true;
    }
  }
  return false;
}

function addOption(select, value, label) {
  const option = el("option", "", label);
  option.value = value;
  select.appendChild(option);
}

export function makeModelPicker(status) {
  const wrapper = el("div", "model-picker");

  const label = el("label", "model-label", "Model");
  label.htmlFor = "model-choice";
  const select = el("select");
  select.id = "model-choice";

  // An empty value means the server's own model
  if (status.server_model) {
    addOption(select, "", "Built-in: " + status.provider);
  }
  addOption(select, "search", "Search only, no key needed");
  for (const choice of VISITOR_CHOICES) {
    addOption(select, choice.value, choice.label);
  }

  const keyInput = el("input");
  keyInput.type = "password";
  keyInput.placeholder = "Paste your API key";
  keyInput.autocomplete = "off";
  keyInput.setAttribute("aria-label", "Your API key");

  const note = el("p", "model-note", "Your key stays in this tab. It is used for one question and never saved.");

  const saved = readSaved();
  if (saved && select.querySelector('option[value="' + saved.provider + '"]')) {
    select.value = saved.provider;
    keyInput.value = saved.apiKey || "";
  }

  function showKeyField() {
    const show = needsKey(select.value);
    keyInput.hidden = !show;
    note.hidden = !show;
  }

  select.addEventListener("change", function () {
    showKeyField();
    save(select.value, keyInput.value.trim());
  });
  keyInput.addEventListener("input", function () {
    save(select.value, keyInput.value.trim());
  });
  showKeyField();

  wrapper.appendChild(label);
  wrapper.appendChild(select);
  wrapper.appendChild(keyInput);
  wrapper.appendChild(note);

  function read() {
    return { provider: select.value, apiKey: keyInput.value.trim(), needsKey: needsKey(select.value) };
  }

  function focusKey() {
    keyInput.focus();
  }

  return { element: wrapper, read: read, focusKey: focusKey };
}
