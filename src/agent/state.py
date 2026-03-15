"""Agent state definition for LangGraph."""

from typing import TypedDict


class AgentState(TypedDict):
    """LangGraph agent state.

    Attributes:
        session_id: 세션 식별자.
        messages: 대화 이력. [{"role": "user"/"assistant", "content": str}]
        intent: 분류된 인텐트.
        context: Neo4j 세션 컨텍스트.
        result: 최종 응답 데이터.
    """

    session_id: str
    messages: list[dict]
    intent: str
    context: dict
    result: dict
