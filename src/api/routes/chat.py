"""채팅 엔드포인트 — Sales Agent 대화 처리."""

from pydantic import BaseModel
from fastapi import APIRouter

from src.agent import AgentState, build_graph

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    intent: str
    result: dict


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """사용자 메시지를 에이전트에 전달하고 결과를 반환한다."""
    state: AgentState = {
        "session_id": req.session_id,
        "messages": [{"role": "user", "content": req.message}],
        "intent": "",
        "context": {},
        "result": {},
    }
    graph = build_graph()
    result_state = await graph.ainvoke(state)
    return ChatResponse(
        session_id=req.session_id,
        intent=result_state.get("intent", "unknown"),
        result=result_state.get("result", {}),
    )
