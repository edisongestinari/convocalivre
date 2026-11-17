"""User-triggered municipal gazette search via Querido Diario's public API.

Unlike ConvocaLivre's local PDF search, this operation sends the person's
name to a third-party service. It must only be called following explicit
in-product consent. No background requests, OCR, or legal act inference.
"""

from __future__ import annotations

from datetime import date
from html import unescape
import ipaddress
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

API_ENDPOINT = "https://api.queridodiario.ok.org.br/gazettes"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_RESULTS = 10
MAX_EXCERPT = 500
USER_AGENT = "ConvocaLivre/0.5 (on-demand municipal gazette lookup)"
_NAME = re.compile(r"^[^\W\d_]+(?:[ '\u2019.-]+[^\W\d_]+)+$", re.UNICODE)
_IBGE = re.compile(r"^\d{7}$")
_TAGS = re.compile(r"<[^>]*>")
_WHITESPACE = re.compile(r"\s+")


class OnlineSearchError(Exception):
    """Sanitized error; never includes the queried person's name or URL."""


def _safe_text(value: object, limit: int = MAX_EXCERPT) -> str:
    if not isinstance(value, str):
        return ""
    return _WHITESPACE.sub(
        " ", unescape(_TAGS.sub(" ", value))
    ).strip()[:limit]


def _safe_https(value: object) -> str:
    if not isinstance(value, str) or len(value) > 2000:
        return ""
    try:
        url = urlparse(value)
        host = (url.hostname or "").lower()
        if not host or host == "localhost" or host.endswith(".local"):
            return ""
        try:
            if not ipaddress.ip_address(host).is_global:
                return ""
        except ValueError:
            pass  # Ordinary public DNS hostname.
        if (url.scheme == "https" and not url.username and not url.password
                and not any(ord(c) < 32 for c in value)):
            return value
    except ValueError:
        pass  # Malformed URL, including unclosed IPv6 bracket.
    return ""


def validate_search(name: str, territory_id: str) -> tuple[str, str]:
    name = _WHITESPACE.sub(" ", name.strip())
    territory_id = territory_id.strip()
    if not 5 <= len(name) <= 120 or not _NAME.fullmatch(name):
        raise ValueError(
            "Informe nome completo (duas ou mais partes, sem numeros ou aspas)."
        )
    if not _IBGE.fullmatch(territory_id):
        raise ValueError("Informe um codigo IBGE municipal de 7 digitos.")
    return name, territory_id


def _read_json(url: str, opener=urlopen) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        # Read at most 2 MiB. Never use infinite response bodies.
        with opener(request, timeout=15) as response:
            final_url = urlparse(response.geturl())
            if final_url.scheme != "https" or final_url.hostname not in {
                "api.queridodiario.ok.org.br", "queridodiario.ok.org.br",
                "api.queridodiario.org.br", "queridodiario.org.br"
            }:
                raise OnlineSearchError("Redirecionamento da API nao autorizado.")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 429:
            raise OnlineSearchError(
                "A API limitou as consultas. Tente novamente mais tarde."
            ) from None
        raise OnlineSearchError(
            "A API esta indisponivel ou recusou a consulta."
        ) from None
    except (URLError, TimeoutError, OSError):
        raise OnlineSearchError(
            "Servico do Querido Diario indisponivel ou falha de conexao segura. "
            "Isso nao significa que sua internet ou o ConvocaLivre falharam."
        ) from None
    if len(payload) > MAX_RESPONSE_BYTES:
        raise OnlineSearchError("Resposta da API acima do limite permitido.")
    try:
        result = json.loads(payload)
    except (ValueError, UnicodeError):
        raise OnlineSearchError("A API retornou uma resposta inesperada.") from None
    if not isinstance(result, dict) or not isinstance(result.get("gazettes"), list):
        raise OnlineSearchError("Formato de resposta da API nao reconhecido.")
    return result


def search_gazettes(
    name: str, territory_id: str, *, opener=urlopen
) -> dict:
    """Perform exactly one name query; return possible mentions, NOT acts."""
    name, territory_id = validate_search(name, territory_id)
    # Exact phrase limits unrelated token matches; a result is still NOT
    # reliable proof of identity because the remote index is not our parser.
    query = urlencode({
        "territory_ids": territory_id,
        "querystring": '"' + name + '"',
        "size": MAX_RESULTS,
        "excerpt_size": MAX_EXCERPT,
        "number_of_excerpts": 1,
        "sort_by": "descending_date",
    })
    response = _read_json(API_ENDPOINT + "?" + query, opener=opener)
    gazettes = response["gazettes"]
    if len(gazettes) > MAX_RESULTS:
        raise OnlineSearchError("A API retornou mais resultados que o limite.")
    rows = []
    for entry in gazettes:
        if not isinstance(entry, dict):
            continue
        source_city = str(entry.get("territory_id") or "")
        if source_city and source_city != territory_id:
            # Never display another municipality as a hit for the requested one.
            continue
        excerpts = entry.get("excerpts") or []
        if isinstance(excerpts, list) and excerpts:
            first = excerpts[0]
            excerpt = _safe_text(
                first if isinstance(first, str)
                else first.get("text", first.get("excerpt", ""))
                if isinstance(first, dict) else ""
            )
        else:
            excerpt = _safe_text(entry.get("excerpt", ""))
        published = entry.get("date", "")
        try:
            published = date.fromisoformat(published).isoformat()
        except (ValueError, TypeError):
            published = ""
        rows.append({
            "date": published,
            "municipality": _safe_text(
                entry.get("territory_name", "") or entry.get("city_name", ""),
                90,
            ),
            "edition": _safe_text(entry.get("edition_number", ""), 45),
            "excerpt": excerpt,
            "pdf_url": _safe_https(entry.get("url", "")),
        })
    total = response.get("total_gazettes")
    if type(total) is not int or total < 0:
        total = None
    return {
        "provider": "Querido Diario (Open Knowledge Brasil)",
        "territory_id": territory_id,
        "returned_count": len(rows),
        "total_reported": total,
        "results": rows,
        "notice": (
            "Trechos de indice remoto: possiveis mencoes, nao confirmacoes "
            "de convocacao ou nomeacao. Cobertura municipal pode ser parcial; "
            "ausencia de resultados nao prova ausencia de publicacao."
        ),
        "privacy_notice": (
            "O nome pesquisado foi enviado para a API do Querido Diario "
            "somente por solicitacao e consentimento do usuario."
        ),
    }
