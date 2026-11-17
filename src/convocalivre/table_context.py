"""Conservative association of layout-table rows with numbered edital headings.

Infers a candidate's possible act ONLY when the same visual column contains
a nearby numbered edital, a cargo header and two distinct supporting lines.
Does not establish legal status, appointment or authenticity of the source.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
import re
import unicodedata

from .acts import PATTERNS

MAX_HEADING_LOOKBACK = 28
MAX_COLUMN_DRIFT = 22
MAX_ROW_TO_HEADING_COLUMN = 48
MIN_EVIDENCE_LINES = 2

# A reference such as "Edital de Abertura nº 001/2024" is NOT a new
# edital heading. Require a heading at the start of its own column cell.
_HEADING = re.compile(
    r"^edital\s+n[.oº°]?\s*\d{1,4}/20\d{2}\b"
)
_SUMULA = re.compile(r"^sumula\s*:")

_REGISTRATION = re.compile(r"(?:^| {8,}) *(\d{2,8}) {2,}$")
_CARGO = re.compile(r"\bCARGO\b", re.I)
_OTHER_BLOCK = re.compile(
    r"\b(?:PORTARIA|DECRETO|EXTRATO|AVISO)\b.{0,25}?\b\d{1,5}/20\d{2}\b", re.I
)
_STRONG = {
    "convocacao": re.compile(r"\bconvoc(?:a|ou|acao|ad[oa]s?|ando|ar)\b"),
    "nomeacao": re.compile(r"\b(?:nomeacao|nomeia|nomeou|nomead[oa]s?|nomear)\b"),
    "desistencia_exclusao": re.compile(
        r"\b(?:exclui|exclusao|desistencia|desistiu|desistente|"
        r"eliminad[oa]s?|desclassificad[oa]s?|anulad[oa]s?)\b"
    ),
    "resultado_homologacao": re.compile(
        r"\b(?:homologa(?:cao|d[oa]s?|r)?|resultado\s+final|classificacao)\b"
    ),
}


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def _segments(line: str) -> list[tuple[int, str]]:
    """Find cells separated by wide horizontal gaps in pypdf layout text."""
    out: list[tuple[int, str]] = []
    start = 0
    for gap in re.finditer(r" {8,}", line):
        piece = line[start:gap.start()]
        if piece.strip():
            col = start + len(piece) - len(piece.lstrip(" "))
            out.append((col, piece.strip()))
        start = gap.end()
    piece = line[start:]
    if piece.strip():
        col = start + len(piece) - len(piece.lstrip(" "))
        out.append((col, piece.strip()))
    return out


def _aligned_segment(line: str, col: int) -> str | None:
    candidates = sorted(
        ((abs(start - col), cell) for start, cell in _segments(line)),
        key=lambda item: item[0],
    )
    if candidates and candidates[0][0] <= MAX_COLUMN_DRIFT:
        return candidates[0][1]
    return None


def infer_table_act(
    layout_text: str, offset_start: int, offset_end: int
) -> dict | None:
    """Infer from a registration row and 2 aligned edital indicator lines.

    Returns None (abstains) whenever boundaries or linkage are ambiguous.
    The returned evidence is textual and must be visually verified.
    """
    if not 0 <= offset_start < offset_end <= len(layout_text):
        return None

    rows = layout_text.splitlines(keepends=True)
    starts: list[int] = []
    offset = 0
    for row in rows:
        starts.append(offset)
        offset += len(row)
    if not starts:
        return None

    target_index = bisect_right(starts, offset_start) - 1
    target_row = rows[target_index].rstrip("\r\n")
    name_col = offset_start - starts[target_index]
    if (name_col < 0 or name_col > len(target_row)
            or offset_end > starts[target_index] + len(target_row)):
        return None

    # Require a registration identifier in the same row immediately before
    # the full name, separated by >=2 spaces. Other layouts must abstain.
    registration = _REGISTRATION.search(target_row[:name_col])
    if not registration:
        return None
    registration_col = registration.start(1)
    if not 0 < name_col - registration_col <= MAX_ROW_TO_HEADING_COLUMN:
        return None

    headings: list[tuple[int, int, str, bool]] = []
    for index in range(
        max(0, target_index - MAX_HEADING_LOOKBACK), target_index
    ):
        cell = _aligned_segment(rows[index].rstrip("\r\n"), registration_col)
        if cell is None:
            continue
        heading = _HEADING.match(_normalize(cell))
        if heading is None:
            continue
        # The initial numbered heading must be corroborated by a SUMULA in
        # the same column within the next three extracted lines. This keeps
        # incidental references to older editais from being used as heads.
        has_summary = any(
            _SUMULA.match(_normalize(_aligned_segment(
                rows[next_index].rstrip("\r\n"), registration_col
            ) or ""))
            for next_index in range(index + 1, min(index + 4, target_index))
        )
        headings.append((index, registration_col, cell[:100], has_summary))
    # Exactly one clear header may own the table. A second, even without
    # a summary, introduces an ambiguous document boundary: abstain.
    if len(headings) != 1 or not headings[0][3]:
        return None
    head_index, heading_col, heading_text, _ = headings[0]

    cargo_indices: list[int] = []
    evidence: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for index in range(head_index + 1, target_index):
        current = rows[index].rstrip("\r\n")
        cell = _aligned_segment(current, heading_col)
        if cell is None:
            continue
        # Reject only a new standalone act heading in the same column.
        # References inside a paragraph ("Edital de Convocacao nº 313/2026")
        # are not new document boundaries.
        if _HEADING.match(_normalize(cell)) or _OTHER_BLOCK.match(cell):
            return None
        normalized = _normalize(cell)
        if _CARGO.search(normalized):
            cargo_indices.append(index)
        for kind, pattern in PATTERNS.items():
            hit = pattern.search(normalized)
            if hit:
                evidence[kind].append((index, cell, hit.group(0)))
    if not cargo_indices or target_index - cargo_indices[-1] > 8:
        return None

    # Count separate lines, not repetitions of one keyword on a single line.
    confirmed = {
        kind: items for kind, items in evidence.items()
        if len({line_number for line_number, _, _ in items}) >= MIN_EVIDENCE_LINES
    }
    if not confirmed:
        return None
    if "desistencia_exclusao" in confirmed:
        # "aprovados" may appear in both the summary and the cancellation
        # clause without signalling a positive RESULTADO/HOMOLOGACAO act.
        # Only independent STRONG evidence of another act causes abstention.
        competing_strong = any(
            kind != "desistencia_exclusao"
            and any(
                _STRONG[kind].search(_normalize(cell))
                for _, cell, _ in items
            )
            for kind, items in confirmed.items()
        )
        if competing_strong:
            return None
        kind = "desistencia_exclusao"
    elif len(confirmed) == 1:
        kind = next(iter(confirmed))
    else:
        return None

    # Repeated weak words such as "aprovados" cannot by themselves establish
    # the act; require an explicit verb/strong action indicator too.
    if not any(
        _STRONG[kind].search(_normalize(cell))
        for _, cell, _ in confirmed[kind]
    ):
        return None

    selected: list[tuple[int, str, str]] = []
    for line_number, cell, indicator in confirmed[kind]:
        if len(selected) == MIN_EVIDENCE_LINES:
            break
        if line_number not in {item[0] for item in selected}:
            selected.append((line_number, cell[:220], indicator))
    return {
        "act_type": kind,
        "act_indicator": selected[0][2],
        "act_basis": "table_same_column_numbered_edital_two_indicators",
        "act_context_excerpt": " | ".join(cell for _, cell, _ in selected),
        "act_context_lines": [line_number + 1 for line_number, _, _ in selected],
        "act_heading_excerpt": heading_text,
        "requires_manual_review": True,
    }
