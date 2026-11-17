"""Analyze one public HTTPS PDF by direct URL, without the Querido Diario API.

The remote web server receives a GET request for the PDF URL, not the
person's searched name. PDF bytes are stored in a disposable directory and
removed after local processing. This is a user-initiated action only.
"""

from __future__ import annotations

import ipaddress
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from .pdf import analyze_pdf, MAX_PDF_BYTES


MAX_URL_CHARS = 2048
MAX_DOWNLOAD_BYTES = MAX_PDF_BYTES
REQUEST_TIMEOUT_SECONDS = 20
_ALLOWED_PORTS = {None, 443}


class RemotePDFError(ValueError):
    """User-visible network error without document text, searched name or URL."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_public_pdf_url(raw_url: str) -> str:
    if not isinstance(raw_url, str):
        raise RemotePDFError("Informe um link HTTPS para um PDF publico.")
    url = raw_url.strip()
    if len(url) > MAX_URL_CHARS or len(url) < 12:
        raise RemotePDFError("O link e muito longo ou nao foi informado.")
    if any(ord(char) <= 32 or ord(char) == 127 for char in url):
        raise RemotePDFError("O link contem caracteres invalidos.")
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        raise RemotePDFError("Link malformado. Informe uma URL HTTPS valida.") from None

    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in _ALLOWED_PORTS
        or parsed.fragment
    ):
        raise RemotePDFError(
            "Somente links HTTPS publicos, sem usuario, porta especial ou fragmento."
        )

    if (
        host == "localhost" or host.endswith(".localhost")
        or host.endswith((".local", ".internal", ".test", ".invalid"))
        or host.startswith("127.")
        or host == "0.0.0.0"
    ):
        raise RemotePDFError("O link nao pode apontar para rede privada.")

    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", host):
            raise RemotePDFError("O dominio do link nao e valido.") from None
    else:
        if not addr.is_global:
            raise RemotePDFError("O link nao pode apontar para rede privada.")
    return url


def download_and_analyze_public_pdf(
    pdf_url: str,
    name: str,
    *,
    opener=None,
) -> dict:
    """One bounded HTTPS download followed by the existing offline classifier.

    No redirects: this prevents a public URL from quietly leading to a private
    host or to an unrelated document. The caller must consent to the GET.
    """
    pdf_url = validate_public_pdf_url(pdf_url)
    if not isinstance(name, str) or len(name.strip().split()) < 2:
        raise RemotePDFError("Informe nome completo com duas ou mais partes.")

    if opener is None:
        opener = build_opener(_NoRedirect()).open
    request = Request(
        pdf_url,
        headers={
            "Accept": "application/pdf,application/octet-stream",
            "User-Agent": "ConvocaLivre/0.5.1 (on-demand public PDF analysis)",
        },
    )
    try:
        with opener(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.geturl() != pdf_url:
                raise RemotePDFError(
                    "O endereco do PDF redirecionou. Informe o link HTTPS final."
                )
            data = response.read(MAX_DOWNLOAD_BYTES + 1)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise RemotePDFError(
                "O site redirecionou o arquivo. Abra a pagina oficial e copie o link final."
            ) from None
        if exc.code in {401, 403}:
            raise RemotePDFError(
                "O site nao permite baixar o PDF automaticamente."
            ) from None
        if exc.code == 404:
            raise RemotePDFError("O link do PDF nao foi encontrado (404).") from None
        raise RemotePDFError(
            "O site nao conseguiu fornecer o PDF nesta consulta."
        ) from None
    except (TimeoutError, URLError, OSError):
        raise RemotePDFError(
            "Nao foi possivel baixar o PDF do site de origem. "
            "Isso nao significa que o nome esteja ausente."
        ) from None

    if not data or len(data) > MAX_DOWNLOAD_BYTES:
        raise RemotePDFError("O PDF esta vazio ou excede 25 MB.")
    if not data.startswith(b"%PDF-"):
        raise RemotePDFError(
            "O endereco nao retornou um PDF. Verifique o link direto."
        )

    try:
        with tempfile.TemporaryDirectory(prefix="convocalivre_pdf_") as dirname:
            file = Path(dirname) / "publicacao.pdf"
            file.write_bytes(data)
            report = analyze_pdf(file, name, source_url=pdf_url)
    except (ValueError, OSError) as exc:
        if isinstance(exc, ValueError):
            raise RemotePDFError(
                "O PDF foi recebido, mas nao pode ser analisado. "
                "Pode estar protegido, incompleto ou fora dos limites."
            ) from None
        raise RemotePDFError("Nao foi possivel processar o PDF recebido.") from None

    return {
        "source_url": pdf_url,
        "report": report,
        "privacy_notice": (
            "O site recebeu uma solicitacao do PDF, mas o nome procurado "
            "nao foi enviado como parametro da busca. A analise foi local."
        ),
        "notice": (
            "Somente este PDF foi consultado. O resultado nao prova a "
            "existencia ou ausencia de ato em outros documentos."
        ),
    }
