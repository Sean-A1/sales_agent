"""Intent classification using OpenAI."""

from openai import AsyncOpenAI

from src.core import get_settings

from .state import AgentState

INTENTS = [
    "search",
    "recommend",
    "detail",
    "stock",
    "review",
    "cart",
    "order_track",
    "unknown",
]

SYSTEM_PROMPT = (
    "You are an intent classifier for a B2C sales agent. "
    "Classify the user's message into exactly one intent.\n\n"
    "Intents:\n"
    "- search: 상품 검색 (키워드, 카테고리, 필터)\n"
    "- recommend: 상품 추천 요청\n"
    "- detail: 특정 상품의 상세 정보/스펙 질문\n"
    "- stock: 재고 또는 가격 확인\n"
    "- review: 리뷰 기반 질문\n"
    "- cart: 장바구니 추가/조회/삭제\n"
    "- order_track: 주문 상태 조회/추적\n"
    "- unknown: 위 카테고리에 해당하지 않는 경우\n\n"
    "Respond with the intent name only, no explanation."
)


async def classify_intent(state: AgentState) -> AgentState:
    """Classify the last user message intent via OpenAI."""
    messages = state["messages"]
    last_user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break

    if not last_user_msg:
        return {**state, "intent": "unknown"}

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": last_user_msg},
        ],
        temperature=0,
        max_tokens=20,
    )

    intent = response.choices[0].message.content.strip().lower()
    if intent not in INTENTS:
        intent = "unknown"

    return {**state, "intent": intent}
