"""
NEXORA ATLAS - Context Sanitization & Prompt Injection Defense (Phase 9)
Strips AWS credentials, session tokens, passwords, and secrets.
Wraps all untrusted metadata (tags, resource names, descriptions, assumptions)
in XML containment tags to prevent prompt injection attacks.
"""

from typing import Any, Dict, List, Optional
from app.ai.models import EvidenceItem
from app.ai.context.redaction import redact_secrets, redact_data_structure


def sanitize_text(text: str) -> str:
    """Strips credentials, secrets, and role ARNs from arbitrary string text."""
    if not text or not isinstance(text, str):
        return ""
    return redact_secrets(text)


def wrap_untrusted_metadata(text: str) -> str:
    """
    Encloses untrusted user-supplied metadata in <untrusted_metadata> tags.
    Neutralizes any attempt to break out of the tag.
    """
    if not text:
        return ""
    # Strip any literal closing tag that could attempt prompt escape
    safe_text = sanitize_text(text).replace("</untrusted_metadata>", "")
    return f"<untrusted_metadata>{safe_text}</untrusted_metadata>"


def sanitize_user_question(question: str) -> Dict[str, str]:
    """
    Sanitizes user question without destroying user intent.
    Returns both original and sanitized question.
    """
    return {
        "original_question": question,
        "sanitized_question": sanitize_text(question),
    }


def sanitize_evidence_item(item: EvidenceItem) -> EvidenceItem:
    """
    Produces a safe, sanitized copy of an evidence item.
    Neutralizes secrets and frames metadata safely.
    """
    sanitized_stmt = sanitize_text(item.statement)
    sanitized_source = sanitize_text(item.source)
    sanitized_entity_id = sanitize_text(item.source_entity_id) if item.source_entity_id else None

    # Sanitize metadata dictionary
    sanitized_metadata: Dict[str, Any] = {}
    for k, v in item.metadata.items():
        clean_k = sanitize_text(str(k))
        if isinstance(v, str):
            clean_v = sanitize_text(v)
            # If this is user-supplied metadata (tag, resource name, cause, assumption), frame it
            if any(term in clean_k.lower() for term in ["tag", "name", "cause", "assumption", "user", "description"]):
                clean_v = wrap_untrusted_metadata(clean_v)
            sanitized_metadata[clean_k] = clean_v
        elif isinstance(v, dict):
            # Nested dictionary (e.g. resource tags)
            nested_dict = {}
            for sub_k, sub_v in v.items():
                safe_sub_k = sanitize_text(str(sub_k))
                safe_sub_v = wrap_untrusted_metadata(str(sub_v)) if isinstance(sub_v, str) else sub_v
                nested_dict[safe_sub_k] = safe_sub_v
            sanitized_metadata[clean_k] = nested_dict
        else:
            sanitized_metadata[clean_k] = v

    return EvidenceItem(
        id=item.id,
        type=item.type,
        epistemic_class=item.epistemic_class,
        statement=sanitized_stmt,
        value=item.value,
        unit=item.unit,
        source=sanitized_source,
        source_entity_id=sanitized_entity_id,
        confidence=item.confidence,
        period_or_timestamp=item.period_or_timestamp,
        metadata=sanitized_metadata,
    )
