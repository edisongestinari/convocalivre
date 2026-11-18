"""Readable, conservative evidence summaries for the local desktop GUI.

This text may include a name or a document excerpt. Do not send it to
telemetry, public issue trackers or an online service.
"""

from __future__ import annotations


BASIS = {
    "no_unambiguous_indicator": (
        "Não foi possível vincular um ato específico ao nome com segurança."
    ),
    "table_same_column_numbered_edital_two_indicators": (
        "O nome foi associado a um edital numerado por alinhamento de coluna "
        "e indicadores compatíveis. A associação exige conferência visual."
    ),
    "table_numbered_convocation_and_candidate_header": (
        "Um edital de convocação, seu comando e a tabela de candidatos foram "
        "vinculados estruturalmente. Confira se o nome pertence ao bloco."
    ),
    "annex_results_ranked_candidate_table": (
        "O nome aparece em anexo de resultados, com posição e inscrição. "
        "Resultado ou homologação não equivalem a nomeação."
    ),
    "annex_homologated_named_candidate_scores_table": (
        "O anexo apresenta resultado final, nome, inscrição e classificação. "
        "Verifique o edital original."
    ),
    "adjacent_page_unfinished_portaria_named_recipient": (
        "A portaria começa na página física anterior e continua com um "
        "destinatário identificado na página seguinte. Revise as duas páginas."
    ),
}


def summarize_match(match: dict, report: dict) -> str:
    """Return only evidence actually recorded by the classifier."""
    category = str(match.get("act_type") or "indeterminado")
    labels = {
        "convocacao": "Possível convocação",
        "nomeacao": "Possível nomeação",
        "desistencia_exclusao": "Possível exclusão/desistência",
        "resultado_homologacao": "Possível resultado/homologação",
        "indeterminado": "Ato indeterminado",
    }
    lines = [
        "RESULTADO INDICATIVO — NÃO É CONFIRMAÇÃO DE ATO ADMINISTRATIVO",
        f"Classificação: {labels.get(category, 'Ato indeterminado')}",
        f"Página física da ocorrência: {match.get('page_number') or 'não informada'}",
    ]
    indicator = match.get("act_indicator")
    if indicator:
        lines.append(f"Indicador textual: {indicator}")
    basis = match.get("act_basis")
    if basis:
        lines.append("Fundamentação da heurística: " + BASIS.get(
            basis, "Regra técnica: " + str(basis)
        ))
    context_lines = match.get("act_context_lines") or []
    if isinstance(context_lines, (list, tuple)) and context_lines:
        offset = match.get("act_context_page_offset", 0)
        if offset == -1:
            location = "na página física anterior"
        elif offset == 0:
            location = "na página da ocorrência"
        else:
            location = "em página de referência não especificada"
        lines.append(
            "Linhas de evidência " + location + ": "
            + ", ".join(str(v) for v in context_lines)
        )
    heading = match.get("act_heading_excerpt")
    if heading:
        lines.append("Cabeçalho identificado: " + " ".join(str(heading).split())[:220])
    excerpt = match.get("excerpt")
    if excerpt:
        lines.append(
            "Trecho extraído (pode misturar colunas ou conter dados pessoais): "
            + " ".join(str(excerpt).split())[:600]
        )
    pages_without = report.get("pages_without_text") or []
    if pages_without:
        lines.append(
            f"ATENÇÃO: {len(pages_without)} página(s) sem texto extraível; "
            "a busca nesse PDF pode estar incompleta."
        )
    if match.get("extraction_mode") == "layout_fallback":
        lines.append(
            "ATENÇÃO: correspondência recuperada pelo layout; "
            "texto rotacionado ou colunas podem estar incompletos."
        )
    lines.append(
        "REVISAO OBRIGATORIA: abra a publicação original, confira o nome, "
        "órgão responsável, número do ato, conteúdo e eventual prazo."
    )
    return "\n\n".join(lines)


def summarize_empty_report(report: dict, status: str) -> str:
    """Avoid incorrectly saying a document proves absence of the person."""
    if status != "analyzed":
        return (
            "O arquivo não pôde ser analisado. Isso não prova "
            "ausência do nome no documento."
        )
    missing = report.get("pages_without_text") or []
    all_pages = report.get("page_count")
    if missing:
        return (
            f"Sem correspondência no texto extraível. {len(missing)} "
            f"de {all_pages or '?'} página(s) sem texto extraível. "
            "Faça conferência visual; a ausência de resultado é inconclusiva."
        )
    return (
        "Nenhuma correspondência localizada no texto extraível deste documento. "
        "Isso não comprova que o nome não exista na publicação original."
    )
