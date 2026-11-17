"""Narrow, evidence-backed PDF context recovery for common official layouts.

This module deliberately abstains unless structure connects a *specific*
name to a command or results table. It is not a legal status determination.
"""

from __future__ import annotations

from bisect import bisect_right
import re
import unicodedata


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def _rows_and_index(text: str, start: int, end: int):
    if not (0 <= start < end <= len(text)):
        return None
    rows = text.splitlines(keepends=True)
    starts = []
    total = 0
    for row in rows:
        starts.append(total)
        total += len(row)
    if not starts:
        return None
    index = bisect_right(starts, start) - 1
    if end > starts[index] + len(rows[index].rstrip("\r\n")):
        return None
    return [row.rstrip("\r\n") for row in rows], index


def _type_result(kind: str, indicator: str, basis: str, lines: list[int], heading: str) -> dict:
    return {
        "act_type": kind,
        "act_indicator": indicator,
        "act_basis": basis,
        "act_context_lines": [line + 1 for line in lines],
        "act_heading_excerpt": heading[:180],
        # No full snippets containing names or personal fields are added here.
        "requires_manual_review": True,
    }


# Recognize a *standalone* act heading, not a citation to an older edital in prose.
_ACT_HEADING = re.compile(
    r"^\s*(?:edital\s+(?:de\s+(?:convocacao|homologacao|resultado)\s+)?"
    r"(?:n[.oº°]?\s*)?\d{1,5}/20\d{2}|"
    r"portaria\s+n[.oº°]?\s*[\d.]+(?:/20\d{2})?)\b"
)
_CONVO_HEADER = re.compile(r"^\s*edital\s+de\s+convocacao\s+n[.oº°]?\s*\d{1,5}/20\d{2}\b")
_CONVO_ACTION = re.compile(r"\bconvocar\s+o\s+candidato\b.{0,90}\babaixo\s+relacionad[oa]s?\b")
_CONVO_TABLE = re.compile(r"\bnome\s+d[oa]\s+candidat[oa]\b.*\bcargo\b")
_RESULT_HEADER = re.compile(r"\bresultado\s+final\b.*\bprocesso\s+seletivo\b")
_RESULT_TABLE = re.compile(r"\bpos\.?\b.*\binscricao\b.*\bnome\b.*\bnota\s+final\b")
_RANKED_ROW = re.compile(r"^\s*\d{1,4}\s+\d{1,2}\s*[-–]\s*\d{4,6}\s+")
# Annex-only public-exam results: the name precedes a long registration
# number, unlike selection-process tables that begin with rank+registration.
_RESULT_ANNEX_TITLE = re.compile(
    r"\banexo\s*i\b.*\bedital\s+de\s+homologacao\s+do\s+resultado\s+final\b"
)
_RESULT_ANNEX_COLUMNS = re.compile(
    r"\bnome\b.*\binscricao\b.*\bnota\s+final\b.*\bclassificacao\b"
)
_RESULT_ANNEX_REG = re.compile(r"^\s+\d{8,12}\b")

_PREV_PORTARIA = re.compile(r"^\s*portaria\s+n[.oº°]?\s*[\d.]+(?:/20\d{2})?\b")
_PREV_NOMEADA = re.compile(r"\bfica\s+nomead[oa]\b")
_CONTINUATION_NAME = re.compile(r"\b(?:a\s+senhora|o\s+senhor|a\s+servidora|o\s+servidor)\s*$")
_FOLLOWUP_NOMEACAO = re.compile(r"\ba\s+nomeacao\s+ao\s+cargo\b")
_MASTHEAD = re.compile(
    r"^(?:diario\s+oficial|municipio\s+de\b|"
    r"(?:segunda|terca|quarta|quinta|sexta|sabado|domingo)\b|"
    r"departamento\s+de\s+comunicacao\b|pagina\s*\|)"
)


def infer_same_page_table(
    page_text: str, start: int, end: int
) -> dict | None:
    """Classify only supported, single-block table shapes in plain extraction."""
    indexed = _rows_and_index(page_text, start, end)
    if not indexed:
        return None
    rows, index = indexed
    normalized = [_norm(row) for row in rows]
    current = normalized[index]
    original_row = rows[index]

    # Fernão-type summons: numbered edital, positive action, heading and
    # candidate row. References to later *conditional* withdrawal are ignored.
    headers = [
        i for i in range(max(0, index - 36), index)
        if _CONVO_HEADER.match(normalized[i])
    ]
    if headers:
        heading = headers[-1]
        if not any(_ACT_HEADING.match(normalized[i]) for i in range(heading + 1, index)):
            actions = [
                i for i in range(heading + 1, index)
                if _CONVO_ACTION.search(normalized[i])
            ]
            tables = [
                i for i in range(heading + 1, index)
                if _CONVO_TABLE.search(normalized[i])
            ]
            if (len(headers) == 1 and actions and tables
                    and actions[-1] < tables[-1] < index
                    and index - tables[-1] <= 4
                    and current.strip() and not re.match(r"^\s*portaria\b", current)):
                return _type_result(
                    "convocacao", "convocar",
                    "table_numbered_convocation_and_candidate_header",
                    [heading, actions[-1], tables[-1]], rows[heading],
                )

    # Joinville-type annex: unlike rank-first tables, each row starts
    # with NAME followed immediately by a long registration number.
    # Explicitly require the homologation title and scoring column names.
    annex_titles = [
        i for i in range(max(0, index - 22), index)
        if _RESULT_ANNEX_TITLE.search(normalized[i])
    ]
    annex_tables = [
        i for i in range(max(0, index - 22), index)
        if _RESULT_ANNEX_COLUMNS.search(normalized[i])
    ]
    line_start = page_text.rfind("\n", 0, start) + 1
    name_col = start - line_start
    right_of_name = _norm(page_text[end:page_text.find("\n", end)
                                    if "\n" in page_text[end:] else len(page_text)])
    if (annex_titles and annex_tables
            and annex_titles[-1] < annex_tables[-1] < index
            and index - annex_tables[-1] <= 18
            and not normalized[index][:name_col].strip()
            and _RESULT_ANNEX_REG.match(right_of_name)
            and not any(_ACT_HEADING.match(normalized[i])
                        for i in range(annex_tables[-1] + 1, index))):
        return _type_result(
            "resultado_homologacao", "edital de homologacao do resultado final",
            "annex_homologated_named_candidate_scores_table",
            [annex_titles[-1], annex_tables[-1]], rows[annex_titles[-1]],
        )

    # Fernão-type classification annex: candidate belongs to a ranked row
    # beneath a column heading, with FINAL RESULTS on this same page.
    first = normalized[:min(12, len(rows))]
    annex = any(re.match(r"^\s*anexo\s*i\b", line.replace(" ", " ")) for line in first)
    # pypdf sometimes extracts "ANEXOI" without the separating space.
    annex = annex or any(re.match(r"^\s*anexoi\b", line) for line in first)
    result_heads = [
        i for i in range(min(index, 15))
        if _RESULT_HEADER.search(normalized[i])
    ]
    table_heads = [
        i for i in range(max(0, index - 45), index)
        if _RESULT_TABLE.search(normalized[i])
    ]
    if annex and result_heads and table_heads and _RANKED_ROW.match(current):
        table = table_heads[-1]
        if result_heads[-1] < table < index and not any(
            _ACT_HEADING.match(normalized[i])
            for i in range(table + 1, index)
        ):
            return _type_result(
                "resultado_homologacao", "resultado final",
                "annex_results_ranked_candidate_table",
                [result_heads[-1], table], rows[result_heads[-1]],
            )
    return None


def infer_previous_page_continuation(
    previous_page_text: str, page_text: str, start: int, end: int
) -> dict | None:
    """Infer a *single* nomination split across adjacent PDF pages.

    Requires an unfinished last PORTARIA in previous page, the named
    recipient in the first substantive line of the next page and same-act
    follow-up nominal wording before any new act heading.
    """
    indexed = _rows_and_index(page_text, start, end)
    if not indexed:
        return None
    rows, index = indexed
    normalized = [_norm(row) for row in rows]
    before = [i for i in range(index) if normalized[i].strip()]
    if len(before) > 4 or any(
        not _MASTHEAD.match(normalized[i].strip()) for i in before
    ):
        return None

    # Candidate must be the explicit grammatical recipient of the split act.
    prefix = _norm(rows[index][:start - sum(len(row) + 1 for row in rows[:index])])
    if not _CONTINUATION_NAME.search(prefix):
        return None

    prev_rows = [row.strip() for row in previous_page_text.splitlines() if row.strip()]
    if not prev_rows or len(prev_rows) < 2:
        return None
    prev_normalized = [_norm(row) for row in prev_rows]
    heads = [
        i for i in range(max(0, len(prev_rows) - 14), len(prev_rows))
        if _PREV_PORTARIA.match(prev_normalized[i])
    ]
    if not heads:
        return None
    heading = heads[-1]
    # Require exactly one act heading in the remainder of the prior page.
    if any(_ACT_HEADING.match(prev_normalized[i]) for i in range(heading + 1, len(prev_rows))):
        return None
    actions = [
        i for i in range(heading + 1, len(prev_rows))
        if _PREV_NOMEADA.search(prev_normalized[i])
    ]
    if len(actions) != 1 or len(prev_rows) - actions[0] > 4:
        return None
    if prev_normalized[-1].endswith((".", ";", ":", "!", "?")):
        return None

    followup = [
        i for i in range(index, min(len(rows), index + 4))
        if _FOLLOWUP_NOMEACAO.search(normalized[i])
    ]
    if not followup or any(
        _ACT_HEADING.match(normalized[i])
        for i in range(index + 1, followup[0] + 1)
    ):
        return None
    return _type_result(
        "nomeacao", "fica nomeada",
        "adjacent_page_unfinished_portaria_named_recipient",
        [heading, actions[0]], prev_rows[heading],
    )
