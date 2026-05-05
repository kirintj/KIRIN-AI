from langgraph.graph import StateGraph, END
from app.agent.langgraph_state import JobAssistantState
from app.agent.langgraph_nodes import (
    intent_router_node,
    tool_executor_node,
    workflow_continue_node,
    response_builder_node,
    should_continue,
)


def build_job_assistant_graph() -> StateGraph:
    graph = StateGraph(JobAssistantState)

    graph.add_node("intent_router", intent_router_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("workflow_continue", workflow_continue_node)
    graph.add_node("response_builder", response_builder_node)

    graph.set_entry_point("intent_router")

    graph.add_conditional_edges(
        "intent_router",
        _route_from_intent,
        {
            "tool_executor": "tool_executor",
            "response_builder": "response_builder",
        },
    )

    graph.add_conditional_edges(
        "tool_executor",
        should_continue,
        {
            "workflow_continue": "workflow_continue",
            "tool_selector": "intent_router",
            "response_builder": "response_builder",
        },
    )

    graph.add_edge("workflow_continue", "response_builder")
    graph.add_edge("response_builder", END)

    return graph.compile()


def _route_from_intent(state: JobAssistantState) -> str:
    intent = state.get("intent", "chat")
    if intent in ("chat", ""):
        return "response_builder"
    return "tool_executor"


_graph_instance = None


def get_graph():
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_job_assistant_graph()
    return _graph_instance
