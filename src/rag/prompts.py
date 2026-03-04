"""
Prompt templates for the QA chain.
Kept intentionally short to save tokens.
"""
from langchain.prompts import ChatPromptTemplate

QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a concise document assistant. "
                "Answer ONLY from the provided context. "
                "If the answer is not in the context, say \"I don't know\". "
                "Be short and factual."
            ),
        ),
        (
            "human",
            "Context:\n{context}\n\nQuestion: {question}",
        ),
    ]
)
