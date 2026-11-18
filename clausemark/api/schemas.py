from pydantic import BaseModel


class AskRequest(BaseModel):
    file_path: str
    question: str

    # "search" for search only. A provider name such as "gemini" with the visitor's own key.
    # Empty means the server's own model if it has one, otherwise search only.
    provider: str = ""
    api_key: str = ""
