async function readJson(response) {
  if (response.ok) {
    return response.json();
  }

  let message = "Request failed (" + response.status + ")";
  try {
    const body = await response.json();
    if (body.detail) {
      message = body.detail;
    }
  } catch (error) {
    // The server sent no JSON, keep the plain message
  }
  throw new Error(message);
}

export async function getStatus() {
  const response = await fetch("/api/status");
  return readJson(response);
}

export async function getContracts() {
  const response = await fetch("/api/contracts");
  return readJson(response);
}

export async function getContract(filePath) {
  const response = await fetch("/api/contract?file_path=" + encodeURIComponent(filePath));
  return readJson(response);
}

export async function askContract(filePath, question) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_path: filePath, question: question }),
  });
  return readJson(response);
}

export async function uploadContract(file) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch("/api/contracts", { method: "POST", body: form });
  return readJson(response);
}

export async function removeContract(filePath) {
  const response = await fetch("/api/contract?file_path=" + encodeURIComponent(filePath), { method: "DELETE" });
  return readJson(response);
}

export async function getBenchmark() {
  const response = await fetch("/api/benchmark");
  return readJson(response);
}
