"""Offline PDF diagnostics without returning names or document excerpts.

The analyzer intentionally does not use OCR or claim to know whether a PDF
contains visible text that pypdf failed to extract.
"""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .pdf import MAX_PDF_BYTES, MAX_PAGES, MAX_PAGE_STREAM_BYTES, MAX_PAGE_TEXT_CHARS


def diagnose_pdf(file: str | Path, *, max_pdf_bytes: int = MAX_PDF_BYTES) -> dict:
    """Return page-level extraction health; no names, text or personal fields."""
    path = Path(file)
    if path.suffix.lower() != ".pdf":
        raise ValueError("O diagnostico aceita apenas arquivos .pdf.")
    if max_pdf_bytes <= 0:
        raise ValueError("Limite de tamanho invalido.")
    size = path.stat().st_size
    if size == 0 or size > max_pdf_bytes:
        raise ValueError("PDF vazio ou acima do limite permitido.")
    raw = path.read_bytes()
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Arquivo sem cabecalho PDF valido.")
    try:
        reader = PdfReader(BytesIO(raw), strict=False)
        if reader.is_encrypted:
            raise ValueError("PDF protegido por senha.")
        count = len(reader.pages)
        if not 1 <= count <= MAX_PAGES:
            raise ValueError("PDF excede o numero de paginas permitido.")
        rows = []
        with_text = 0
        layout_helped = 0
        error_count = 0
        for i, page in enumerate(reader.pages, start=1):
            stream = page.get_contents()
            if stream is not None and len(stream.get_data()) > MAX_PAGE_STREAM_BYTES:
                rows.append({
                    "page_number": i, "status": "page_stream_too_large",
                    "plain_chars": None, "layout_chars": None,
                })
                error_count += 1
                continue
            chars = [None, None]
            errors = []
            for j, kwargs in enumerate(({}, {"extraction_mode": "layout"})):
                try:
                    extracted = page.extract_text(**kwargs) or ""
                    if len(extracted) > MAX_PAGE_TEXT_CHARS:
                        errors.append("text_limit_exceeded")
                    else:
                        chars[j] = len(extracted.strip())
                except (ValueError, NotImplementedError, PdfReadError, KeyError,
                        TypeError) as exc:
                    # Do not echo exception content; it can reveal PDF text.
                    errors.append(type(exc).__name__)
            if errors:
                error_count += 1
            has_text = any(value is not None and value > 0 for value in chars)
            if has_text:
                with_text += 1
            status = (
                "extraction_error" if chars == [None, None]
                else "text_available" if has_text
                else "no_extractable_text"
            )
            if chars[1] is not None and (chars[0] or 0) == 0 and chars[1] > 0:
                layout_helped += 1
            rows.append({
                "page_number": i, "status": status,
                "plain_chars": chars[0], "layout_chars": chars[1],
                "extract_errors": sorted(set(errors)),
            })
    except PdfReadError as exc:
        raise ValueError("Nao foi possivel interpretar o PDF.") from exc

    pages_without_text = [
        row["page_number"] for row in rows
        if row["status"] == "no_extractable_text"
    ]
    if with_text == count and not error_count:
        diagnosis = "searchable_text_detected"
    elif with_text == 0 and not error_count:
        diagnosis = "no_extractable_text"
    else:
        diagnosis = "partially_extractable_or_errors"
    return {
        "tool": "ConvocaLivre",
        "diagnosis_kind": "offline_pdf_text_layer",
        "pdf_sha256": sha256(raw).hexdigest(),
        "size_bytes": size,
        "page_count": count,
        "pages_with_extractable_text": with_text,
        "pages_without_extractable_text": pages_without_text,
        "pages_with_extraction_errors": error_count,
        "pages_where_layout_recovers_text": layout_helped,
        "diagnosis": diagnosis,
        "pages": rows,
        "privacy": "Nao inclui texto, nomes, CPFs ou trechos do PDF.",
        "notice": (
            "Texto extraivel nao comprova busca completa; ausencia de texto "
            "nao prova que o PDF seja digitalizado. Pode exigir OCR manual."
        ),
    }
