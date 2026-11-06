from pydantic import BaseModel


class AskRequest(BaseModel):
    file_path: str
    question: str
