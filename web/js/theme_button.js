// The "Dark mode" button in the top bar. It flips the theme and remembers the choice.

const THEME_KEY = "clausemark-theme";

function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch (error) {
    // Private windows can block storage. The theme still changes for this visit.
  }
}

function showState(button) {
  const isDark = document.documentElement.dataset.theme === "dark";
  button.setAttribute("aria-pressed", String(isDark));
}

export function setupThemeButton() {
  const button = document.getElementById("theme-button");
  showState(button);

  button.addEventListener("click", function () {
    let next = "dark";
    if (document.documentElement.dataset.theme === "dark") {
      next = "light";
    }
    document.documentElement.dataset.theme = next;
    saveTheme(next);
    showState(button);
  });
}
