import { getStatus } from "./api.js";
import { clear, el } from "./dom.js";
import { showBenchmark } from "./pages/benchmark.js";
import { showContracts } from "./pages/contracts.js";
import { showReview } from "./pages/review.js";

const page = document.getElementById("page");
const contractSlot = document.getElementById("contract-slot");

function markCurrentLink(pageName) {
  const links = document.querySelectorAll(".main-nav a");
  for (const link of links) {
    if (link.dataset.page === pageName) {
      link.classList.add("current");
    } else {
      link.classList.remove("current");
    }
  }
}

function readRoute() {
  // A route looks like #/review?file=sample%2Fa.txt
  const hash = window.location.hash.replace("#/", "");
  const parts = hash.split("?");
  const params = new URLSearchParams(parts[1] || "");
  return { name: parts[0] || "review", params: params };
}

async function showRoute() {
  const route = readRoute();
  markCurrentLink(route.name);
  clear(page);
  clear(contractSlot);

  try {
    if (route.name === "contracts") {
      await showContracts(page);
    } else if (route.name === "benchmark") {
      await showBenchmark(page);
    } else {
      await showReview(page, contractSlot, route.params.get("file"));
    }
  } catch (error) {
    clear(page);
    page.appendChild(el("p", "page-error", error.message));
  }
}

function setName(name) {
  if (name === "sample") {
    return "sample contracts";
  }
  return "LegalBench " + name;
}

async function showStatus() {
  const status = await getStatus();
  const line = document.getElementById("status-line");
  line.textContent = setName(status.active_set) + " / " + status.provider;
}

window.addEventListener("hashchange", showRoute);
showStatus();
showRoute();
