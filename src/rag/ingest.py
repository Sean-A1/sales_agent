"""
Ingest pipeline: PDF files → chunks → embeddings → Chroma vector store.

Usage (via CLI):
    python main.py ingest [--reset]

Direct usage:
    from src.rag.ingest import run_ingest
    run_ingest(reset=True)
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from tqdm import tqdm

from . import config
from .loaders import load_pdf


def _get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)


def run_ingest(
    pdf_dir: Path = config.PDF_DIR,
    index_dir: Path = config.INDEX_DIR,
    reset: bool = False,
) -> None:
    """
    Ingest all PDF files from *pdf_dir* into a Chroma vector store.

    Args:
        pdf_dir:   Directory that contains .pdf files.
        index_dir: Chroma persist directory.
        reset:     Wipe existing index before ingesting when True.
    """
    # ---- optional reset ----
    if reset and index_dir.exists():
        shutil.rmtree(index_dir)
        print(f"[reset] Cleared existing index at {index_dir}")

    index_dir.mkdir(parents=True, exist_ok=True)

    # ---- discover PDFs ----
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[warn] No PDF files found in {pdf_dir}")
        return

    print(f"[ingest] Found {len(pdf_files)} PDF file(s) in {pdf_dir}")

    # ---- load + split ----
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    all_chunks: List[Document] = []
    total_pages = 0

    for pdf_path in tqdm(pdf_files, desc="Loading PDFs"):
        raw_docs = load_pdf(pdf_path)
        chunks = splitter.split_documents(raw_docs)
        total_pages += len(raw_docs)
        all_chunks.extend(chunks)
        tqdm.write(
            f"  {pdf_path.name}: {len(raw_docs)} page(s) → {len(chunks)} chunk(s)"
        )

    # Filter empty chunks (avoid chromadb empty-batch error)
    all_chunks = [doc for doc in all_chunks if doc.page_content.strip()]

    print(
        f"\n[ingest] Total: {len(pdf_files)} file(s), "
        f"{total_pages} page(s), {len(all_chunks)} chunk(s)"
    )

    if not all_chunks:
        print("[warn] No valid chunks to index. Aborting.")
        return

    # ---- embed + persist ----
    print(f"[ingest] Building embeddings ({config.EMBEDDING_MODEL}) …")
    embeddings = _get_embeddings()

    db = Chroma(
        persist_directory=str(index_dir),
        embedding_function=embeddings,
    )
    db.add_documents(all_chunks)

    print(f"[ingest] Done. Index persisted at {index_dir}")
