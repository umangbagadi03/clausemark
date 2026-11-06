from typing import TypedDict


class AgentState(TypedDict):
    set_name: str
    file_path: str
    question: str
    query: str              # what we search for, can be rewritten
    searches: int           # how many search rounds we have done
    clauses: list           # the clauses found so far
    verdict: str            # "enough", "partial" or "none"
    better_query: str       # the grader's suggestion for the next search
    points: list            # the answer, as short cited statements
    citations: list         # the verified citations
    rejected_quotes: list   # quotes the LLM wrote that are not in the clauses
    steps: list             # what the agent did, shown in the UI
