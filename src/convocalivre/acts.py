"""Conservative, local classification of *possible* administrative acts.

This module only inspects the clause containing the exact matched name.
It never verifies the legal effect, source, candidate status or authenticity.
"""

from __future__ import annotations

import re
import unicodedata

EVENT_TYPES = (
    "convocacao",
    "nomeacao",
    "desistencia_exclusao",
    "resultado_homologacao",
    "indeterminado",
)

# Indicators are deliberately narrow and explainable. NOT an exhaustive legal
# vocabulary; a missing indicator is preferable to an invented definitive act.
PATTERNS = {
    "convocacao": re.compile(
        r"\bconvoca(?:cao|r|d[oa]s?|ndo|m)?\b"
    ),
    "nomeacao": re.compile(
        r"\b(?:nomea(?:cao|r|d[oa]s?|ndo|m)?|nomeou|nomeia)\b"
    ),
    "desistencia_exclusao": re.compile(
        r"\b(?:desistencia|desistiu|desistente|exclusao|exclui(?:d[oa]s?)?|"
        r"excluido|excluida|eliminad[oa]s?|desclassificad[oa]s?|"
        r"anulad[oa]s?|anulacao|revogad[oa]s?)\b|"
        r"\b(?:torna(?:r)?|tornou)\s+sem\s+efeito\b|"
        r"\bsem\s+efeito\s+(?:a\s+|o\s+)?nomeacao\b"
    ),
    "resultado_homologacao": re.compile(
        r"\b(?:homolog(?:acao|ar|ad[oa]s?|a|ou)|"
        r"resultad[oa]s?|classificacao|classificad[oa]s?|aprovad[oa]s?)\b"
    ),
}

_BOUNDARY = re.compile(r"[\r\n.;!?]")
_NEGATION_BEFORE = re.compile(r"\bnao(?:\s+\w+){0,3}\s*$")
MAX_TRIGGER_DISTANCE = 120


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in decomposed.casefold()
        if not unicodedata.combining(char)
    )


def count_act_types(matches: list[dict]) -> dict[str, int]:
    """Counts act labels for name matches; counts are NOT legal acts."""
    counts = {key: 0 for key in EVENT_TYPES}
    for match in matches:
        label = match.get("act_type", "indeterminado")
        if label in counts:
            counts[label] += 1
    return counts


def classify_mention(text: str, start: int, end: int) -> dict:
    """Label a name occurrence from its own clause only.

    An unrelated keyword in an earlier/later line or sentence cannot supply
    evidence. All results require review. Strong cancellation/exclusion terms
    take precedence over incidental 'nomeacao' ('desistencia da nomeacao').
    Conflicting other categories cause abstention.
    """
    if not (0 <= start < end <= len(text)):
        raise ValueError("Invalid mention offsets")

    preceding = list(_BOUNDARY.finditer(text, 0, start))
    following = _BOUNDARY.search(text, end)
    lo = preceding[-1].end() if preceding else 0
    hi = following.start() if following else len(text)
    clause = text[lo:hi]
    normalized = _normalize(clause)
    local_start = len(_normalize(text[lo:start]))
    local_end = len(_normalize(text[lo:end]))
    found: dict[str, str] = {}

    for kind, pattern in PATTERNS.items():
        for hit in pattern.finditer(normalized):
            distance = max(0, local_start - hit.end(), hit.start() - local_end)
            if distance > MAX_TRIGGER_DISTANCE:
                continue
            if _NEGATION_BEFORE.search(normalized[:hit.start()]):
                continue
            found.setdefault(kind, hit.group(0))

    outcome = "indeterminado"
    indicator = None
    basis = "no_unambiguous_indicator"
    if "desistencia_exclusao" in found:
        # Desistencia/exclusao frequently accompanies a reference to an earlier
        # nomeacao, e.g. "exclusao por desistência da nomeacao".
        outcome = "desistencia_exclusao"
        indicator = found[outcome]
        basis = "same_clause_exclusion_priority"
    elif len(found) == 1:
        outcome, indicator = next(iter(found.items()))
        basis = "same_clause_indicator"
    elif len(found) > 1:
        basis = "conflicting_indicators"

    return {
        "act_type": outcome,
        "act_indicator": indicator,
        "act_basis": basis,
        "requires_manual_review": True,
    }
