"""User-triggered analysis of one public HTTPS PDF, without an index API.

The user supplies the PDF URL and explicitly agrees to one download.
The searched name is NOT placed in an HTTP request. This module pins
the validated public DNS address used by the TLS connection to prevent
DNS-rebinding/TOCTOU attacks during a direct PDF download.

This is not a sandbox for malicious PDFs; maintainers must continue
to consider the PDF parser and the user's local network trust boundary.
"""

from __future__ import annotations

import http.client
import ipaddress
from pathlib import Path
import re
import socket
import ssl
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request

from .pdf import analyze_pdf, MAX_PDF_BYTES

MAX_URL_CHARS = 2048
MAX_DOWNLOAD_BYTES = MAX_PDF_BYTES
REQUEST_TIMEOUT_SECONDS = 20
_ALLOWED_PORTS = {None, 443}


class RemotePDFError(ValueError):
    """A user-visible network error with no name or PDF content."""


def validate_public_pdf_url(raw_url: str) -> str:
    if not isinstance(raw_url, str):
        raise RemotePDFError("Informe um link HTTPS para um PDF publico.")
    url = raw_url.strip()
    if len(url) > MAX_URL_CHARS or len(url) < 12:
        raise RemotePDFError("O link e muito longo ou nao foi informado.")
    if any(ord(ch) <= 32 or ord(ch) == 127 for ch in url):
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
        or parsed.netloc.endswith(".")
    ):
        raise RemotePDFError(
            "Somente links HTTPS publicos, sem usuario, porta especial ou fragmento."
        )

    # Do not allow IP literals: this feature fetches documents from public DNS
    # hostnames, not internal servers or cloud instance metadata endpoints.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise RemotePDFError("Informe um dominio publico, nao um endereco IP.")
    if (
        host == "localhost"
        or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid"))
        or not re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
            r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+",
            host,
        )
    ):
        raise RemotePDFError("O dominio do link nao e publico ou valido.")
    return url


def resolve_public_addresses(host: str, *, resolver=None) -> list[str]:
    """Reject ALL DNS answers if ANY points to a non-global address.

    The checked address is subsequently used directly for TCP, while the
    hostname remains in the Host header and TLS SNI/hostname validation.
    This avoids checking DNS at one moment then resolving it again on connect.
    """
    if resolver is None:
        resolver = socket.getaddrinfo
    try:
        answers = resolver(host, 443, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError):
        raise RemotePDFError(
            "Nao foi possivel resolver o dominio do PDF. "
            "Isso nao significa que o nome esteja ausente."
        ) from None
    addresses = []
    for answer in answers:
        try:
            ip = ipaddress.ip_address(answer[4][0])
        except (IndexError, KeyError, ValueError, TypeError):
            raise RemotePDFError("DNS retornou um endereco invalido.") from None
        # Python is_global excludes RFC1918, loopback, link-local, metadata,
        # reserved and non-routable allocations for IPv4/IPv6.
        if not ip.is_global:
            raise RemotePDFError(
                "O dominio resolve para uma rede privada ou reservada. "
                "Download bloqueado por seguranca."
            )
        address = str(ip)
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise RemotePDFError("O dominio nao possui enderecos publicos validos.")
    return addresses


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS with public-IP pinning and genuine TLS verification for host."""

    def __init__(self, host: str, address: str, *, timeout: int):
        super().__init__(
            host=host, port=443, timeout=timeout, context=ssl.create_default_context()
        )
        self._pinned_address = address

    def connect(self):
        # Never call super().connect(): that would resolve the hostname again.
        sock = socket.create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def _download_pinned_https(url: str) -> bytes:
    """Only one GET, no redirect, only an already-validated public address."""
    parsed = urlsplit(url)
    host = parsed.hostname
    addresses = resolve_public_addresses(host)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    conn = _PinnedHTTPSConnection(host, addresses[0], timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        conn.request(
            "GET",
            target,
            headers={
                "Host": host,
                "Accept": "application/pdf,application/octet-stream",
                "User-Agent": "ConvocaLivre/0.5.2 (consented public PDF)",
                "Connection": "close",
            },
        )
        response = conn.getresponse()
        if 300 <= response.status < 400:
            raise RemotePDFError(
                "O site redirecionou o arquivo. Abra o link HTTPS final no site oficial."
            )
        if response.status in (401, 403):
            raise RemotePDFError(
                "O site nao permite baixar o PDF automaticamente."
            )
        if response.status == 404:
            raise RemotePDFError("O link do PDF nao foi encontrado (404).")
        if response.status != 200:
            raise RemotePDFError(
                "O site nao conseguiu fornecer o PDF nesta consulta."
            )
        declared = response.getheader("Content-Length", "")
        if declared and declared.isdecimal() and int(declared) > MAX_DOWNLOAD_BYTES:
            raise RemotePDFError("O PDF excede o limite de tamanho.")
        return response.read(MAX_DOWNLOAD_BYTES + 1)
    except RemotePDFError:
        raise
    except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException):
        raise RemotePDFError(
            "Nao foi possivel baixar o PDF do site de origem. "
            "Isso nao significa que o nome esteja ausente."
        ) from None
    finally:
        conn.close()


def download_and_analyze_public_pdf(
    pdf_url: str,
    name: str,
    *,
    opener=None,
) -> dict:
    """Download and analyze one HTTPS PDF; transport injection is test-only.

    Default transport pins the public resolved IP, checks the original host's
    TLS certificate and does not follow redirects. The legacy opener seam is
    for deterministic synthetic tests, not for untrusted production plugins.
    """
    pdf_url = validate_public_pdf_url(pdf_url)
    if not isinstance(name, str) or len(name.strip().split()) < 2:
        raise RemotePDFError("Informe nome completo com duas ou mais partes.")

    if opener is None:
        data = _download_pinned_https(pdf_url)
    else:
        request = Request(
            pdf_url,
            headers={
                "Accept": "application/pdf,application/octet-stream",
                "User-Agent": "ConvocaLivre/0.5.2 (on-demand public PDF)",
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
            if exc.code in (401, 403):
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
    except (ValueError, OSError):
        raise RemotePDFError(
            "O PDF foi recebido, mas nao pode ser analisado. "
            "Pode estar protegido, incompleto ou fora dos limites."
        ) from None
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
