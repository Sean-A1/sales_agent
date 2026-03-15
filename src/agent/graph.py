"""LangGraph agent graph definition."""

from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from .intent import classify_intent
from .nodes import (
    cart_node,
    detail_node,
    order_track_node,
    recommend_node,
    response_node,
    review_node,
    search_node,
    stock_node,
    unknown_node,
)
from .state import AgentState

INTENT_TO_NODE = {
    "search": "search",
    "recommend": "recommend",
    "detail": "detail",
    "stock": "stock",
    "review": "review",
    "cart": "cart",
    "order_track": "order_track",
    "unknown": "unknown",
}


def _route_by_intent(state: AgentState) -> str:
    """Route to the appropriate node based on classified intent."""
    intent = state.get("intent", "unknown")
    return INTENT_TO_NODE.get(intent, "unknown")


def build_graph() -> CompiledGraph:
    """Build and compile the sales agent graph.

    Flow: START → classify_intent → (conditional) → intent_node → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("search", search_node)
    graph.add_node("recommend", recommend_node)
    graph.add_node("detail", detail_node)
    graph.add_node("stock", stock_node)
    graph.add_node("review", review_node)
    graph.add_node("cart", cart_node)
    graph.add_node("order_track", order_track_node)
    graph.add_node("unknown", unknown_node)
    graph.add_node("response", response_node)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        _route_by_intent,
        INTENT_TO_NODE,
    )

    for node_name in INTENT_TO_NODE.values():
        graph.add_edge(node_name, "response")

    graph.add_edge("response", END)

    return graph.compile()
