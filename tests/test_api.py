import pytest
from fastapi.testclient import TestClient

from clausemark.agent.ask import IndexNotReady
from clausemark.api import contract_routes
from clausemark.api.server import app
from clausemark.indexing import builder, vector_store
from clausemark.llm.errors import LLMError

CONTRACT = "sample/Northgate_Calder_Mutual_NDA.txt"
LONG_TEXT = ("1. Term\n\nThis agreement lasts for two years from the start date. " * 10).encode("utf-8")


@pytest.fixture
def client(monkeypatch):
    # Most tests pretend the server has its own model
    def has_model():
        return True

    def server_model():
        return "server model"

    monkeypatch.setattr(contract_routes, "server_has_model", has_model)
    monkeypatch.setattr(contract_routes, "get_llm", server_model)
    return TestClient(app)


@pytest.fixture
def calls(monkeypatch):
    """Records which mode answered and with which model, instead of running the agent."""
    seen = {}

    def fake_ask(set_name, path, question, llm):
        seen["mode"] = "answer"
        seen["llm"] = llm
        return {"mode": "answer"}

    def fake_search(set_name, path, question):
        seen["mode"] = "search"
        return {"mode": "search"}

    def fake_make_client(provider, api_key):
        return "client for " + provider + " with " + api_key

    monkeypatch.setattr(contract_routes, "ask_contract", fake_ask)
    monkeypatch.setattr(contract_routes, "search_contract", fake_search)
    monkeypatch.setattr(contract_routes, "make_client", fake_make_client)
    return seen


@pytest.fixture
def no_indexing(monkeypatch):
    """Uploads save their text, but skip the embedding models and Qdrant."""
    def fake_index(set_name, file_path):
        return 3

    def fake_delete(set_name, scheme, file_path):
        return None

    monkeypatch.setattr(builder, "index_one_contract", fake_index)
    monkeypatch.setattr(vector_store, "delete_contract", fake_delete)


def upload(client, name, data):
    return client.post("/api/contracts", files={"file": (name, data)})


def test_lists_sample_contracts(client):
    contracts = client.get("/api/contracts").json()["contracts"]
    paths = []
    for contract in contracts:
        paths.append(contract["file_path"])
    assert CONTRACT in paths


def test_contract_has_text_and_clauses(client):
    contract = client.get("/api/contract", params={"file_path": CONTRACT}).json()
    assert "MUTUAL NON-DISCLOSURE" in contract["text"]
    first_clause = contract["clauses"][0]
    assert first_clause["start"] < first_clause["end"]


def test_unknown_contract_is_404(client):
    assert client.get("/api/contract", params={"file_path": "sample/none.txt"}).status_code == 404


def test_path_outside_the_list_is_404(client):
    assert client.get("/api/contract", params={"file_path": "../../.env"}).status_code == 404
    body = {"file_path": "../../.env", "question": "x"}
    assert client.post("/api/ask", json=body).status_code == 404


def test_empty_question_is_400(client):
    body = {"file_path": CONTRACT, "question": "   "}
    assert client.post("/api/ask", json=body).status_code == 400


def test_ask_returns_the_result(client, monkeypatch):
    def fake_ask(set_name, path, question, llm):
        return {"found": True}

    monkeypatch.setattr(contract_routes, "ask_contract", fake_ask)
    body = {"file_path": CONTRACT, "question": "How long?"}
    assert client.post("/api/ask", json=body).json() == {"found": True}


def test_model_failure_is_503_with_its_message(client, monkeypatch):
    def fail(set_name, path, question, llm):
        raise LLMError("Gemini is busy")

    monkeypatch.setattr(contract_routes, "ask_contract", fail)
    response = client.post("/api/ask", json={"file_path": CONTRACT, "question": "How long?"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Gemini is busy"


def test_missing_index_is_409_with_the_fix(client, monkeypatch):
    def fail(set_name, path, question, llm):
        raise IndexNotReady("Run: python main.py index")

    monkeypatch.setattr(contract_routes, "ask_contract", fail)
    response = client.post("/api/ask", json={"file_path": CONTRACT, "question": "How long?"})
    assert response.status_code == 409
    assert "main.py index" in response.json()["detail"]


def test_upload_then_open_then_remove(client, no_indexing):
    response = upload(client, "My Vendor Deal.txt", LONG_TEXT)
    assert response.status_code == 200
    file_path = response.json()["file_path"]
    assert file_path == "uploads/My Vendor Deal.txt"

    contract = client.get("/api/contract", params={"file_path": file_path}).json()
    assert contract["text"] == LONG_TEXT.decode("utf-8")
    assert contract["questions"] == []

    assert client.delete("/api/contract", params={"file_path": file_path}).status_code == 200
    assert client.get("/api/contract", params={"file_path": file_path}).status_code == 404


def test_uploading_the_same_name_replaces_the_text(client, no_indexing):
    upload(client, "deal.txt", LONG_TEXT)
    newer = LONG_TEXT + b"Added later."
    file_path = upload(client, "deal.txt", newer).json()["file_path"]
    contract = client.get("/api/contract", params={"file_path": file_path}).json()
    assert contract["text"].endswith("Added later.")


def test_upload_name_cannot_leave_the_folder(client, no_indexing):
    file_path = upload(client, "../../../evil.txt", LONG_TEXT).json()["file_path"]
    assert file_path == "uploads/evil.txt"


def test_wrong_file_type_is_400(client):
    response = upload(client, "contract.docx", LONG_TEXT)
    assert response.status_code == 400
    assert ".pdf or .txt" in response.json()["detail"]


def test_almost_empty_file_is_400(client):
    assert upload(client, "tiny.txt", b"too short").status_code == 400


def test_too_big_file_is_400(client):
    too_big = b"x" * (5 * 1024 * 1024 + 1)
    response = upload(client, "big.txt", too_big)
    assert response.status_code == 400
    assert "too big" in response.json()["detail"]


def test_benchmark_contract_cannot_be_removed(client):
    assert client.delete("/api/contract", params={"file_path": CONTRACT}).status_code == 403


def ask_body(provider="", api_key=""):
    return {"file_path": CONTRACT, "question": "How long?", "provider": provider, "api_key": api_key}


def test_no_choice_uses_the_server_model(client, calls):
    client.post("/api/ask", json=ask_body())
    assert calls["mode"] == "answer"
    assert calls["llm"] == "server model"


def test_search_choice_skips_the_model(client, calls):
    client.post("/api/ask", json=ask_body(provider="search"))
    assert calls["mode"] == "search"


def test_no_server_model_and_no_key_means_search_only(client, calls, monkeypatch):
    def no_model():
        return False

    monkeypatch.setattr(contract_routes, "server_has_model", no_model)
    client.post("/api/ask", json=ask_body())
    assert calls["mode"] == "search"


def test_visitor_key_builds_a_model_for_this_request(client, calls):
    client.post("/api/ask", json=ask_body(provider="gemini", api_key="  visitor-key  "))
    assert calls["mode"] == "answer"
    assert calls["llm"] == "client for gemini with visitor-key"


def test_key_for_an_unknown_provider_is_400(client, calls):
    response = client.post("/api/ask", json=ask_body(provider="ollama", api_key="visitor-key"))
    assert response.status_code == 400


def test_key_never_comes_back_in_an_error(client, monkeypatch):
    def fail(set_name, path, question, llm):
        raise LLMError("Provider said: bad key secret-123-key")

    def fake_make_client(provider, api_key):
        return "client"

    monkeypatch.setattr(contract_routes, "make_client", fake_make_client)
    monkeypatch.setattr(contract_routes, "ask_contract", fail)
    response = client.post("/api/ask", json=ask_body(provider="openai", api_key="secret-123-key"))
    assert response.status_code == 503
    assert "secret-123-key" not in response.text
    assert "[your key]" in response.json()["detail"]


def test_uploads_can_be_turned_off(client, monkeypatch):
    monkeypatch.setattr(contract_routes.config, "ALLOW_UPLOADS", False)
    assert upload(client, "deal.txt", LONG_TEXT).status_code == 403
    assert client.delete("/api/contract", params={"file_path": CONTRACT}).status_code == 403


def test_status_says_what_the_server_can_do(client):
    status = client.get("/api/status").json()
    assert "server_model" in status
    assert "allow_uploads" in status
