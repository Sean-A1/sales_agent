# RAG Pipeline — Local Notes

- OpenAI key is `RAG_OPENAI_API_KEY`, not `OPENAI_API_KEY`. This is intentional — do not rename.
- If `RAG_OPENAI_API_KEY` is absent, the pipeline skips LLM and returns raw chunks. This is by design.
- Embeddings are local (sentence-transformers, all-MiniLM-L6-v2). No API call needed for embeddings.
- Vector store is Chroma, persisted at `data/index/`. Deleting this requires `ingest --reset`.
- LlamaParse is primary PDF loader; PyPDFLoader is automatic fallback.
- All config defaults are in config.py. CLI flags override `.env` values.