"""
Metadata extraction stage — single LLM sandwich call.

Takes the cleaned markdown and the active profile, sends the opening and
closing sections to an LLM, and returns a flat metadata dict.
"""
from __future__ import annotations

import json
import logging

from openai import OpenAI

from .profiles.base import ConversionProfile

logger = logging.getLogger(__name__)

# How many characters to send as "header" and "footer" context.
_HEADER_CHARS = 2000
_FOOTER_CHARS = 1000


def extract_metadata(
    cleaned_md: str,
    profile: ConversionProfile,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> dict[str, str | None]:
    """Extract metadata from cleaned markdown using a single LLM call.

    Returns a dict whose keys match ``profile.metadata_schema``.
    Fields the LLM cannot determine are set to ``None``.
    """
    if not profile.metadata_schema or not profile.metadata_prompt_template:
        return {}

    header = cleaned_md[:_HEADER_CHARS]
    footer = cleaned_md[-_FOOTER_CHARS:] if len(cleaned_md) > _FOOTER_CHARS else ""

    schema_description = "\n".join(
        f'- "{k}": {v}' for k, v in profile.metadata_schema.items()
    )

    prompt = profile.metadata_prompt_template.format(
        schema_description=schema_description,
        header=header,
        footer=footer,
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )

    raw = response.choices[0].message.content or ""
    metadata = _parse_json_response(raw, profile.metadata_schema)
    return metadata


def _parse_json_response(
    raw: str,
    schema: dict[str, str],
) -> dict[str, str | None]:
    """Parse the LLM JSON response, falling back to nulls on failure."""
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Metadata LLM returned invalid JSON; using nulls. Raw: %s", raw)
        return {k: None for k in schema}

    # Normalise: keep only known keys, fill missing ones with None.
    return {k: data.get(k) for k in schema}


def metadata_to_yaml_frontmatter(metadata: dict[str, str | None]) -> str:
    """Render a metadata dict as YAML frontmatter suitable for prepending to md."""
    if not metadata:
        return ""
    lines = ["---"]
    for key, value in metadata.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, str) and _needs_yaml_quoting(value):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def _needs_yaml_quoting(value: str) -> bool:
    """Return True if the YAML value should be quoted to stay safe."""
    if not value:
        return True
    # Quote if it contains characters that could confuse a YAML parser.
    unsafe_chars = {":", "#", "[", "]", "{", "}", ",", "&", "*", "?", "|", ">", "'", '"', "%", "@", "`"}
    return any(c in value for c in unsafe_chars) or value.strip() != value
