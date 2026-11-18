from fastapi import APIRouter, HTTPException, UploadFile

from clausemark import config
from clausemark.agent.ask import IndexNotReady, ask_contract, search_contract
from clausemark.api.schemas import AskRequest
from clausemark.chunking.clause_store import get_parents
from clausemark.dataset import corpus
from clausemark.ingestion.parsers import UploadError
from clausemark.ingestion.pipeline import add_contract, remove_contract
from clausemark.llm.errors import LLMError
from clausemark.llm.provider import VISITOR_PROVIDERS, get_llm, make_client, server_has_model

router = APIRouter(prefix="/api")


def require_known_contract(file_path):
    # The path comes from the browser, so only accept contracts we already listed
    if file_path not in corpus.list_app_contracts(config.ACTIVE_SET):
        raise HTTPException(status_code=404, detail="Contract not found")


@router.get("/contracts")
def list_contracts():
    contracts = []
    for file_path in corpus.list_app_contracts(config.ACTIVE_SET):
        set_name = corpus.set_of_contract(config.ACTIVE_SET, file_path)
        contracts.append({
            "file_path": file_path,
            "title": corpus.contract_title(file_path),
            "source": corpus.contract_source(file_path),
            "characters": len(corpus.read_contract(set_name, file_path)),
            "questions": len(corpus.questions_for_contract(set_name, file_path)),
            "removable": corpus.is_upload(file_path),
        })
    return {"contracts": contracts}


@router.get("/contract")
def get_contract(file_path: str):
    require_known_contract(file_path)
    set_name = corpus.set_of_contract(config.ACTIVE_SET, file_path)

    clauses = []
    for parent in get_parents(set_name, file_path):
        clauses.append({
            "clause_id": parent["parent_id"],
            "title": parent["title"],
            "start": parent["start"],
            "end": parent["end"],
        })

    return {
        "file_path": file_path,
        "title": corpus.contract_title(file_path),
        "source": corpus.contract_source(file_path),
        "text": corpus.read_contract(set_name, file_path),
        "clauses": clauses,
        "questions": corpus.questions_for_contract(set_name, file_path),
    }


def require_uploads_allowed():
    if not config.ALLOW_UPLOADS:
        raise HTTPException(status_code=403, detail="Uploads are turned off on this server")


@router.post("/contracts")
def upload_contract(file: UploadFile):
    require_uploads_allowed()

    # Read one byte past the limit, so a huge file is not read into memory just to reject it
    data = file.file.read(config.MAX_UPLOAD_BYTES + 1)

    try:
        file_path = add_contract(file.filename or "", data)
    except UploadError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {"file_path": file_path}


@router.delete("/contract")
def delete_contract(file_path: str):
    require_uploads_allowed()
    require_known_contract(file_path)

    try:
        remove_contract(file_path)
    except UploadError as error:
        raise HTTPException(status_code=403, detail=str(error))

    return {"removed": file_path}


@router.post("/ask")
def ask(request: AskRequest):
    require_known_contract(request.file_path)

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Write a question first")

    set_name = corpus.set_of_contract(config.ACTIVE_SET, request.file_path)
    api_key = request.api_key.strip()

    try:
        llm = choose_model(request.provider, api_key)
        if llm is None:
            return search_contract(set_name, request.file_path, question)
        return ask_contract(set_name, request.file_path, question, llm)
    except IndexNotReady as error:
        raise HTTPException(status_code=409, detail=str(error))
    except LLMError as error:
        raise HTTPException(status_code=503, detail=hide_key(str(error), api_key))


def choose_model(provider, api_key):
    """Returns the model for one question, or None for search only.

    A visitor's key is used for this request only. It is never saved, logged or put in a trace.
    """
    if provider == "search":
        return None

    if api_key:
        if provider not in VISITOR_PROVIDERS:
            raise HTTPException(status_code=400, detail="Choose Gemini, Claude or OpenAI for your key")
        return make_client(provider, api_key)

    if server_has_model():
        return get_llm()
    return None


def hide_key(message, api_key):
    """Provider errors can quote part of a key. Remove it before the message leaves the server."""
    if api_key:
        message = message.replace(api_key, "[your key]")
    return message
