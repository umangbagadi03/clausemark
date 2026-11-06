from langgraph.graph import END, START, StateGraph

from clausemark.agent.nodes import (
    answer_node,
    grade_node,
    retrieve_node,
    rewrite_node,
    verify_node,
)
from clausemark.agent.state import AgentState

# The first search plus at most one more
MAX_SEARCHES = 2


def route_after_grade(state):
    if state["verdict"] == "enough":
        return "answer"
    if state["searches"] >= MAX_SEARCHES:
        return "answer"
    if not state["better_query"]:
        return "answer"
    return "rewrite"


def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("answer", answer_node)
    graph.add_node("verify", verify_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", route_after_grade, ["answer", "rewrite"])
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("answer", "verify")
    graph.add_edge("verify", END)

    return graph.compile()
