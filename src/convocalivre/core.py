"""Deterministic, offline analysis of public gazette text.

This module does not establish legal status, appointments, or authenticity.
Users must independently verify the official source.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import re
import unicodedata

from .acts import classify_mention, count_act_types

DEFAULT_TERMS = (
    "convocacao", "nomeacao", "nomear", "convocado", "convocada",
    "posse", "edital de convocacao", "aprovados",
)


def normalize_with_mapping(text: str) -> tuple[str, list[int]]:
    """Accent-insensitive normalization while retaining original offsets."""
    out: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(text):
        decomposed = unicodedata.normalize("NFKD", char)
        for piece in decomposed:
            if unicodedata.combining(piece):
                continue
            folded = piece.casefold()
            for c in folded:
                out.append(c)
                positions.append(index)
    return "".join(out), positions


def _find_whole_expression(text: str, expression: str) -> list[tuple[int, int]]:
    """Return spans after normalization; use Unicode word boundaries."""
    if not expression.strip():
        return []
    pattern = re.compile(r"(?<!\w)" + re.escape(expression) + r"(?!\w)")
    return [(match.start(), match.end()) for match in pattern.finditer(text)]


def analyze(
    text: str,
    name: str,
    *,
    source_url: str = "",
    publication_date: str = "",
    context_chars: int = 400,
    terms: tuple[str, ...] = DEFAULT_TERMS,
) -> dict:
    """Find exact full-name matches and relevant terms in their context.

    Signal is 'possible_related_act' only if a term appears near a name;
    it NEVER confirms a nomination/appointment or authenticity.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("The document text must not be empty.")
    if not isinstance(name, str) or len(name.strip().split()) < 2:
        raise ValueError("Provide at least two name components to reduce false positives.")
    if context_chars < 50 or context_chars > 2000:
        raise ValueError("context_chars must be between 50 and 2000.")

    normalized, offset_map = normalize_with_mapping(text)
    norm_name, _ = normalize_with_mapping(" ".join(name.strip().split()))
    # Gazette text can contain irregular whitespace in names.
    norm_name_pattern = r"\s+".join(re.escape(word) for word in norm_name.split())
    expression = re.compile(r"(?<!\w)" + norm_name_pattern + r"(?!\w)")
    spans = [(m.start(), m.end()) for m in expression.finditer(normalized)]
    all_results: list[dict] = []
    term_norms = [normalize_with_mapping(term)[0] for term in terms]
    for start, end in spans:
        original_start = offset_map[start]
        original_end = offset_map[end - 1] + 1
        lo = max(0, original_start - context_chars)
        hi = min(len(text), original_end + context_chars)
        snippet = text[lo:hi]
        normalized_snippet, _ = normalize_with_mapping(snippet)
        found_terms = [original for original, term in zip(terms, term_norms) if _find_whole_expression(normalized_snippet, term)]
        act = classify_mention(text, original_start, original_end)
        all_results.append({
            "offset_start": original_start,
            "offset_end": original_end,
            "excerpt": snippet,
            "matched_terms": list(dict.fromkeys(found_terms)),
            "signal": "possible_related_act" if found_terms else "name_mentioned_only",
            **act,
        })

    return {
        "schema_version": "0.3",
        "tool": "ConvocaLivre",
        "analyzed_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_name": name.strip(),
        "source_url_unverified": source_url,
        "publication_date_user_supplied": publication_date,
        "document_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "document_length": len(text),
        "match_count": len(all_results),
        "result": (
            "possible_related_act" if any(r["matched_terms"] for r in all_results)
            else "name_mentioned_only" if all_results
            else "no_name_match"
        ),
        "matches": all_results,
        "act_type_counts": count_act_types(all_results),
        "important_notice": (
            "Indicacao heuristica, nao confirmacao oficial. "
            "act_type descreve apenas um indicador na mesma frase/linha. "
            "Verifique documento, autenticidade e contexto; sem OCR."

        ),
    }
