"""Offline analysis of text-based PDFs; never verifies legal appointment status."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .core import analyze
from .acts import count_act_types

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PAGES = 250
MAX_PAGE_STREAM_BYTES = 10 * 1024 * 1024
MAX_PAGE_TEXT_CHARS = 1_000_000


def analyze_pdf(
    file: str | Path,
    name: str,
    *,
    source_url: str = "",
    publication_date: str = "",
    context_chars: int = 400,
    max_pdf_bytes: int = MAX_PDF_BYTES,
) -> dict:
    """Match a name independently on each PDF page, keeping 1-based page numbers.

    Only locally extractable text is supported; there is no OCR or network access.
    The source URL and publication date are user-provided and unverified.
    """
    path = Path(file)
    if path.suffix.lower() != ".pdf":
        raise ValueError("Informe um arquivo com extensao .pdf.")
    if not name or len(name.strip().split()) < 2:
        raise ValueError("Informe nome completo com pelo menos duas partes.")
    if not 50 <= context_chars <= 2000:
        raise ValueError("context_chars deve estar entre 50 e 2000.")
    if max_pdf_bytes <= 0:
        raise ValueError("max_pdf_bytes deve ser positivo.")
    size = path.stat().st_size
    if size == 0 or size > max_pdf_bytes:
        raise ValueError("PDF vazio ou acima do limite de tamanho permitido.")
    document_bytes = path.read_bytes()
    if not document_bytes.startswith(b"%PDF-"):
        raise ValueError("Arquivo sem cabecalho PDF valido.")

    try:
        reader = PdfReader(BytesIO(document_bytes), strict=False)
        if reader.is_encrypted:
            raise ValueError("PDF protegido por senha nao e suportado.")
        page_count = len(reader.pages)
        if not 1 <= page_count <= MAX_PAGES:
            raise ValueError(f"PDF deve conter entre 1 e {MAX_PAGES} paginas.")
        matches: list[dict] = []
        pages_without_text: list[int] = []
        layout_fallback_pages: set[int] = set()
        layout_rejected_pages: set[int] = set()
        layout_error_pages: set[int] = set()
        for page_number, page in enumerate(reader.pages, start=1):
            stream = page.get_contents()
            if stream is not None and len(stream.get_data()) > MAX_PAGE_STREAM_BYTES:
                raise ValueError(f"Pagina {page_number}: conteudo acima do limite seguro.")
            text = page.extract_text() or ""
            if len(text) > MAX_PAGE_TEXT_CHARS:
                raise ValueError(f"Pagina {page_number}: texto extraido acima do limite seguro.")

            # O modo padrao pode embaralhar a ordem dos nomes em tabelas/colunas.
            # Use layout como alternativa APENAS se nao houver ocorrencia na pagina.
            plain_matches = []
            if text.strip():
                page_report = analyze(
                    text, name, source_url=source_url,
                    publication_date=publication_date, context_chars=context_chars,
                )
                plain_matches = page_report["matches"]
            if plain_matches:
                for match in plain_matches:
                    matches.append({
                        "page_number": page_number,
                        "extraction_mode": "plain",
                        **match,
                    })
                continue

            try:
                layout_text = page.extract_text(extraction_mode="layout") or ""
            except (ValueError, NotImplementedError):
                layout_error_pages.add(page_number)
                if not text.strip():
                    pages_without_text.append(page_number)
                continue

            if len(layout_text) > MAX_PAGE_TEXT_CHARS:
                raise ValueError(f"Pagina {page_number}: texto extraido acima do limite seguro.")
            if not text.strip() and not layout_text.strip():
                pages_without_text.append(page_number)
                continue
            if not layout_text.strip():
                continue

            layout_report = analyze(
                layout_text, name, source_url=source_url,
                publication_date=publication_date, context_chars=context_chars,
            )
            for match in layout_report["matches"]:
                # Rejeitar nomes reconstruidos ENTRE linhas ou colunas distantes.
                # Limite conservador: nao unificar tokens separados por >=8 espacos.
                raw_name = layout_text[match["offset_start"]:match["offset_end"]]
                if re.search(r"[\r\n\t]| {8,}", raw_name):
                    layout_rejected_pages.add(page_number)
                    continue
                matches.append({
                    "page_number": page_number,
                    "extraction_mode": "layout_fallback",
                    **match,
                })
                layout_fallback_pages.add(page_number)
    except PdfReadError as exc:
        raise ValueError("Nao foi possivel interpretar o PDF.") from exc

    signal = (
        "possible_related_act" if any(m["matched_terms"] for m in matches)
        else "name_mentioned_only" if matches
        else "no_extractable_text" if len(pages_without_text) == page_count
        else "no_name_match"
    )
    warnings = [
        "A deteccao de palavras proximas ao nome nao comprova nomeacao ou convocacao.",
        "URL e data sao informados pelo usuario e NAO foram verificados.",
    ]
    if layout_fallback_pages:
        warnings.append(
            "Correspondencias encontradas por reconstrucao do layout nas paginas "
            + ", ".join(map(str, sorted(layout_fallback_pages)))
            + ". Verifique visualmente: o layout pode omitir texto rotacionado e "
            "misturar elementos de colunas ou tabelas."
        )
    if layout_rejected_pages:
        warnings.append(
            "Candidatos a correspondencia descartados por separacao excessiva "
            "entre palavras nas paginas "
            + ", ".join(map(str, sorted(layout_rejected_pages))) + "."
        )
    if layout_error_pages:
        warnings.append(
            "Falha de extracao alternativa em paginas "
            + ", ".join(map(str, sorted(layout_error_pages))) + "."
        )
    if pages_without_text:
        warnings.append(
            "Paginas sem texto extraivel: " + ", ".join(map(str, pages_without_text)) + ". "
            "PDFs digitalizados podem exigir OCR, que nao e executado."
        )
    return {
        "schema_version": "0.3",
        "tool": "ConvocaLivre",
        "input_type": "pdf",
        "extraction_method": "pypdf_plain_with_layout_fallback",
        "layout_fallback_pages": sorted(layout_fallback_pages),
        "requested_name": name.strip(),
        "source_url_unverified": source_url,
        "publication_date_user_supplied": publication_date,
        "document_sha256": sha256(document_bytes).hexdigest(),
        "document_hash_basis": "original_pdf_bytes",
        "document_size_bytes": len(document_bytes),
        "page_count": page_count,
        "pages_with_text": page_count - len(pages_without_text),
        "pages_without_text": pages_without_text,
        "match_count": len(matches),
        "result": signal,
        "matches": matches,
        "act_type_counts": count_act_types(matches),
        "warnings": warnings,
        "important_notice": (
            "act_type e apenas um indicador heuristico, nao comprovacao de ato. "
            "Consulte a pagina indicada e confirme contexto, autenticidade e "
            "efeito juridico na fonte original."
        ),
    }
