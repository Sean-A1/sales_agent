"""Intent classification using OpenAI."""

import json

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
    "You are an intent classifier and entity extractor for a B2C sales agent.\n"
    "Classify the user's message into exactly one intent and extract relevant entities.\n\n"
    "Intents:\n"
    "- search: 상품 검색 (키워드, 카테고리, 필터)\n"
    "- recommend: 상품 추천 요청\n"
    "- detail: 특정 상품의 상세 정보/스펙 질문\n"
    "- stock: 재고 또는 가격 확인\n"
    "- review: 리뷰 기반 질문\n"
    "- cart: 장바구니 추가/조회/삭제\n"
    "- order_track: 주문 상태 조회/추적\n"
    "- unknown: 위 카테고리에 해당하지 않는 경우\n\n"
    "Entities to extract:\n"
    "- category: 상품 카테고리 (패션/의류, 뷰티/화장품, 가전/디지털, 식품/건강, 생활/주방 중 하나)\n"
    "- product_id: 언급된 상품 ID (숫자)\n"
    "- query: 검색 키워드\n"
    "- order_id: 주문 ID (숫자)\n\n"
    "Respond in JSON format. Only include entities that are present in the message.\n"
    'Example: {"intent": "recommend", "category": "가전/디지털", "query": "청소기"}'
)

_CONTEXT_KEYS = ("category", "query", "product_id", "order_id")


async def classify_intent(state: AgentState) -> AgentState:
    """Classify the last user message intent via OpenAI."""
    messages = state["messages"]
    last_user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break

    if not last_user_msg:
        return {**state, "intent": "unknown", "context": {}}

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": last_user_msg},
        ],
        temperature=0,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {**state, "intent": "unknown", "context": {}}

    intent = data.get("intent", "unknown").lower()
    if intent not in INTENTS:
        intent = "unknown"

    context = {k: data[k] for k in _CONTEXT_KEYS if k in data}

    return {**state, "intent": intent, "context": context}
