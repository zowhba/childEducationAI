from langgraph.graph import StateGraph, START, END
from app.workflow.nodes import (
    profile_node,
    fetch_course_node,
    generate_node,
    assess_node,
    feedback_node
)
from app.models.schemas import ChildProfileInput

def create_graph() -> StateGraph:
    graph = StateGraph(state_schema=ChildProfileInput)
    graph.add_node(START, profile_node)
    graph.add_node("fetch_course", fetch_course_node)
    graph.add_node("generate", generate_node)
    graph.add_node("assess", assess_node)
    graph.add_node("feedback", feedback_node)
    graph.add_edge(START, "fetch_course")
    graph.add_edge("fetch_course", "generate")
    graph.add_edge("generate", "assess")
    graph.add_edge("assess", "feedback")
    graph.add_edge("feedback", END)
    return graph.compile()
