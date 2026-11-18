// Runs in <head>, before the page is drawn, so the page never flashes the wrong colours.
// A saved choice wins. Without one, the computer's own light or dark setting is used.

const THEME_KEY = "clausemark-theme";

function readSavedTheme() {
  try {
    return localStorage.getItem(THEME_KEY);
  } catch (error) {
    return null;
  }
}

function startingTheme() {
  const saved = readSavedTheme();
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

document.documentElement.dataset.theme = startingTheme();
