"""Sanitized status categories for public-PDF research sources."""

from __future__ import annotations

import socket
import ssl
from urllib.error import HTTPError, URLError

from pypdf.errors import PdfReadError


class SourceDocumentError(ValueError):
    """An expected public-source failure with a non-sensitive reason code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def source_failure_code(exc: Exception) -> str:
    """Return diagnostic category only; NEVER return exception detail or URL."""
    if isinstance(exc, SourceDocumentError):
        return exc.code
    if isinstance(exc, HTTPError):
        if exc.code in (401, 403):
            return "http_access_denied"
        if exc.code == 404:
            return "http_not_found"
        if exc.code == 429:
            return "http_rate_limited"
        if 500 <= exc.code < 600:
            return "http_server_error"
        return "http_other_error"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "network_timeout"
    if isinstance(exc, URLError):
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "network_timeout"
        if isinstance(reason, socket.gaierror):
            return "dns_error"
        if isinstance(reason, ssl.SSLError):
            return "tls_error"
        return "network_error"
    if isinstance(exc, PdfReadError):
        return "invalid_pdf_structure"
    if isinstance(exc, (ValueError, TypeError)):
        return "invalid_document"
    return "unexpected_source_error"


def sanitized_page_text_health(page) -> dict:
    """Measure extractable characters without revealing text or identities."""
    counts = {}
    for label, kwargs in (
        ("plain", {}),
        ("layout", {"extraction_mode": "layout"}),
    ):
        try:
            data = page.extract_text(**kwargs) or ""
            counts[label + "_chars"] = len(data.strip())
        except (ValueError, NotImplementedError, PdfReadError, TypeError, KeyError):
            counts[label + "_chars"] = None
    valid = [n for n in counts.values() if n is not None]
    counts["text_available"] = any(n > 0 for n in valid)
    counts["extraction_failed"] = not valid
    return counts
