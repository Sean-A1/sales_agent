# Convert Pipeline — Local Notes

- LlamaParse key is `LLAMA_CLOUD_API_KEY`. Not `LLAMAPARSE_API_KEY` (typo caused auth failures before).
- Export quality (html/xml/json) is entirely dependent on md quality. Fix parse/clean, not export logic.
- metadata.py uses a single LLM sandwich call. Do not split into multiple calls.
- pipeline.py is the orchestrator: parse → clean → metadata → export. Keep this order.
- Profiles (profiles/financial_rfp.py) define domain-specific rules for Korean financial RFPs.
- Output goes to `data/export/<timestamp>/` with subdirs: md/, html/, xml/, json/.
- Known fidelity issues: title structure, table flattening, heading level instability.