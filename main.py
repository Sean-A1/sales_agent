"""
Project entry point – run the RAG CLI from the project root.

Examples:
    python main.py ingest --reset
    python main.py query "질문을 입력하세요"
    python main.py query "What are the key requirements?" --top-k 5
"""
from src.app.cli import app

if __name__ == "__main__":
    app()
