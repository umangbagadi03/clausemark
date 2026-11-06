from typing import Literal

from pydantic import BaseModel


class ClauseCitation(BaseModel):
    number: int
    clause_id: str
    exact_quote: str
    explanation: str
    risk_flag: Literal["LOW", "MEDIUM", "HIGH"]

    # The LLM does not fill these. Code finds the quote in the contract and sets them.
    start_char: int = -1
    end_char: int = -1


class AnswerPoint(BaseModel):
    text: str
    citations: list[int]


class GradeReply(BaseModel):
    verdict: Literal["enough", "partial", "none"]
    better_query: str = ""
