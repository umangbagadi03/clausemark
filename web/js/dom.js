// A small helper to make elements. Text always goes through textContent,
// so words from a contract or a model can never run as HTML.
export function el(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

export function clear(element) {
  element.textContent = "";
}

export function formatNumber(number) {
  return number.toLocaleString("en-US");
}
