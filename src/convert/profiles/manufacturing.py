"""
manufacturing — conversion profile for manufacturing / technical documents.

Assumptions:
  - Documents contain many images: drawings, flowcharts, part photos, diagrams.
  - premium_mode parsing is needed to extract image descriptions.
  - Technical terms and error codes should stay in English; prose in Korean.
"""
from __future__ import annotations

from .base import ConversionProfile

MANUFACTURING_METADATA_PROMPT = """\
You are a document metadata extractor. You will receive the opening section \
and closing section of a manufacturing or technical document.

Extract the following fields and return ONLY a valid JSON object with these keys:
{schema_description}

If a field cannot be determined from the text, use null.

--- OPENING SECTION ---
{header}

--- CLOSING SECTION ---
{footer}

Return only the JSON object, no explanation.
"""

MANUFACTURING_LLAMAPARSE_SYSTEM_PROMPT = """\
이 문서는 제조업 기술 문서입니다. 다음 규칙을 따라 변환하세요:

1. 이미지, 도면, 순서도를 발견하면 한국어로 상세히 설명하세요.
2. 에러 코드, 모델명, 기술 용어는 영어 원문을 유지하세요.
3. 표는 markdown 표 형식으로 정확히 변환하세요.
4. 순서도(flowchart)는 단계별 텍스트 목록으로 변환하세요.
5. 부품 목록(BOM)의 번호와 수량을 정확히 보존하세요.
"""

manufacturing = ConversionProfile(
    name="manufacturing",

    # -----------------------------------------------------------------------
    # Parse
    # -----------------------------------------------------------------------
    llamaparse_instructions=(
        "This document is a manufacturing or technical manual. "
        "Describe all images, diagrams, and flowcharts in Korean. "
        "Preserve all table structures as markdown tables. "
        "Keep error codes, model names, and technical terms in English. "
        "Convert flowcharts into step-by-step text lists. "
        "Do not summarise or omit any text."
    ),
    premium_mode=True,
    llamaparse_system_prompt=MANUFACTURING_LLAMAPARSE_SYSTEM_PROMPT,

    # -----------------------------------------------------------------------
    # Clean
    # -----------------------------------------------------------------------
    remove_patterns=[
        r"(?m)^\s*Page\s+\d+\s+of\s+\d+\s*$",     # "Page 3 of 12"
        r"(?m)^\s*-\s*\d+\s*-\s*$",                  # "- 3 -" page numbers
        r"(?m)^CONFIDENTIAL\s*$",                     # confidential watermark
        r"(?m)^Copyright\s*.*$",                      # copyright lines
        r"(?m)^SPARE\s+PARTS\s*$",                    # spare parts header noise
        r"(?m)^\s*\d+\s*/\s*\d+\s*$",                # "3 / 12" page numbers
    ],
    normalize_whitespace=True,
    fix_hyphenation=True,
    preserve_table_blocks=True,
    convert_image_tags=True,

    # -----------------------------------------------------------------------
    # Metadata
    # -----------------------------------------------------------------------
    metadata_schema={
        "device_name":  "Name or model of the device / equipment described",
        "doc_title":    "Official title of the document",
        "doc_type":     "Document type (e.g. manual, specification, drawing list, BOM)",
        "version":      "Document version or revision number",
        "date":         "Document date (ISO 8601 if possible)",
        "summary":      "One-sentence summary of the document content",
    },
    metadata_prompt_template=MANUFACTURING_METADATA_PROMPT,
)
