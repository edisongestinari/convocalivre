"""No-network regression tests for public PDF-by-URL workflow."""

from io import BytesIO
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from convocalivre.remote_pdf import (
    RemotePDFError, download_and_analyze_public_pdf, validate_public_pdf_url,
    resolve_public_addresses, _download_pinned_https,
)


SOURCE = "https://publicacoes.example.org/diario/edicao_2026.pdf"
NAME = "ANA PAULA SILVA"


def pdf_bytes(text: str = "Fica convocada ANA PAULA SILVA para documentos.") -> bytes:
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    ref = writer._add_object(font)
    page = writer.add_blank_page(width=612, height=792)
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = DecodedStreamObject()
    stream.set_data(
        f"BT /F1 12 Tf 40 700 Td ({escaped}) Tj ET".encode("ascii")
    )
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): ref})
    })
    page[NameObject("/Contents")] = writer._add_object(stream)
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


class FakeResponse:
    def __init__(self, data: bytes, url: str = SOURCE):
        self.data = data
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.data[:limit]


class RemotePDFTests(unittest.TestCase):
    def test_gui_module_import_is_safe_without_display(self):
        # Tk widgets must only be created after the user opens the dialog.
        from convocalivre.remote_pdf_gui import open_remote_pdf_dialog
        self.assertTrue(callable(open_remote_pdf_dialog))


    def test_rejects_ip_literals_and_invalid_domains(self):
        for address in (
            "https://8.8.8.8/file.pdf",
            "https://[2606:4700:4700::1111]/file.pdf",
            "https://internal.local/file.pdf",
            "https://bad_domain.example/file.pdf",
        ):
            with self.subTest(address=address):
                with self.assertRaises(RemotePDFError):
                    validate_public_pdf_url(address)

    def test_dns_rejects_private_and_mixed_answer_sets(self):
        def answer(addresses):
            return lambda _host, _port, **_kwargs: [
                (2, 1, 6, "", (address, 443)) for address in addresses
            ]
        for items in (
            ["127.0.0.1"],
            ["169.254.169.254"],
            ["10.2.3.4"],
            ["8.8.8.8", "192.168.0.2"],
            ["::1"],
            ["fc00::1"],
        ):
            with self.subTest(items=items):
                with self.assertRaises(RemotePDFError):
                    resolve_public_addresses("public.example.org",
                                             resolver=answer(items))
        self.assertEqual(
            resolve_public_addresses(
                "public.example.org", resolver=answer(["8.8.8.8", "8.8.8.8"])
            ),
            ["8.8.8.8"],
        )

    def test_transport_pins_validated_address_and_never_redirects(self):
        events = []
        pdf = pdf_bytes()
        class FakeConnection:
            def __init__(self, host, address, timeout):
                events.append(("connect", host, address, timeout))
            def request(self, method, path, headers):
                events.append(("request", method, path, headers["Host"]))
            def getresponse(self):
                class Response:
                    status = 200
                    def getheader(self, _name, default=""):
                        return default
                    def read(self, size):
                        return pdf[:size]
                return Response()
            def close(self):
                events.append(("close",))
        with patch(
            "convocalivre.remote_pdf.resolve_public_addresses",
            return_value=["8.8.8.8"],
        ) as resolver, patch(
            "convocalivre.remote_pdf._PinnedHTTPSConnection", FakeConnection
        ):
            payload = _download_pinned_https(SOURCE)
        self.assertEqual(payload, pdf)
        self.assertEqual(events[0][1:3], ("publicacoes.example.org", "8.8.8.8"))
        self.assertEqual(events[1][1:4], ("GET", "/diario/edicao_2026.pdf",
                                          "publicacoes.example.org"))
        self.assertEqual(events[-1], ("close",))
        resolver.assert_called_once_with("publicacoes.example.org")

    def test_http_redirect_does_not_trigger_second_get(self):
        requests = []
        class RedirectConnection:
            def __init__(self, *args, **kwargs):
                pass
            def request(self, method, target, headers):
                requests.append(target)
            def getresponse(self):
                class Response:
                    status = 302
                return Response()
            def close(self):
                pass
        with patch(
            "convocalivre.remote_pdf.resolve_public_addresses",
            return_value=["8.8.8.8"],
        ), patch(
            "convocalivre.remote_pdf._PinnedHTTPSConnection", RedirectConnection
        ):
            with self.assertRaisesRegex(RemotePDFError, "redirecionou"):
                _download_pinned_https(SOURCE)
        self.assertEqual(requests, ["/diario/edicao_2026.pdf"])

    def test_valid_https_public_pdf_url(self):
        self.assertEqual(validate_public_pdf_url("  " + SOURCE + "  "), SOURCE)

    def test_rejects_private_local_malformed_and_http_urls(self):
        for url in (
            "http://publicacoes.example.org/pub.pdf",
            "https://localhost/pub.pdf",
            "https://service.local/pub.pdf",
            "https://127.0.0.1/pub.pdf",
            "https://192.168.0.1/pub.pdf",
            "https://[::1]/pub.pdf",
            "https://10.1.2.3/pub.pdf",
            "https://pub.example.org:8080/file.pdf",
            "https://user:secret@pub.example.org/file.pdf",
            "https://[invalid/pub.pdf",
            "https://publicacoes.example.org/ed.pdf#page=2",
            "file:///C:/dados.pdf",
        ):
            with self.subTest(url=url), self.assertRaises(RemotePDFError):
                validate_public_pdf_url(url)

    def test_one_download_and_offline_classification(self):
        calls = []
        data = pdf_bytes()

        def opener(request, timeout):
            calls.append((request.full_url, request.headers, timeout))
            return FakeResponse(data)

        result = download_and_analyze_public_pdf(SOURCE, NAME, opener=opener)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], SOURCE)
        self.assertLessEqual(calls[0][2], 20)
        self.assertNotIn(NAME, json.dumps(calls))
        self.assertEqual(result["source_url"], SOURCE)
        report = result["report"]
        self.assertEqual(report["match_count"], 1)
        self.assertEqual(report["matches"][0]["page_number"], 1)
        self.assertEqual(report["matches"][0]["act_type"], "convocacao")
        self.assertEqual(report["source_url_unverified"], SOURCE)

    def test_pdf_with_no_name_is_not_provider_failure(self):
        result = download_and_analyze_public_pdf(
            SOURCE, NAME,
            opener=lambda *_a, **_kw: FakeResponse(pdf_bytes("Edital sem nomes.")),
        )
        self.assertEqual(result["report"]["match_count"], 0)
        self.assertIn("Somente este PDF", result["notice"])

    def test_rejects_non_pdf_and_excess_size(self):
        for response in (
            b"<html>not a pdf</html>",
            b"%PDF-" + b"0" * (25 * 1024 * 1024 + 1),
        ):
            with self.subTest(size=len(response)):
                with self.assertRaises(RemotePDFError):
                    download_and_analyze_public_pdf(
                        SOURCE, NAME,
                        opener=lambda *_a, **_kw: FakeResponse(response),
                    )

    def test_redirect_rejected_not_followed(self):
        with self.assertRaisesRegex(RemotePDFError, "redirecionou"):
            download_and_analyze_public_pdf(
                SOURCE, NAME,
                opener=lambda *_a, **_kw: FakeResponse(
                    pdf_bytes(), "https://redirect.example.org/final.pdf"
                ),
            )
        def http_redirect(*_a, **_kw):
            raise HTTPError(SOURCE, 302, "moved", None, None)
        with self.assertRaisesRegex(RemotePDFError, "redirecionou"):
            download_and_analyze_public_pdf(SOURCE, NAME, opener=http_redirect)

    def test_not_found_and_access_denied_distinguished(self):
        for status, word in ((403, "permite"), (404, "404")):
            def error(*_a, **_kw):
                raise HTTPError(SOURCE, status, "failure", None, None)
            with self.subTest(code=status):
                with self.assertRaisesRegex(RemotePDFError, word):
                    download_and_analyze_public_pdf(SOURCE, NAME, opener=error)

    def test_network_exception_does_not_claim_absence(self):
        def fail(*_a, **_kw):
            raise URLError("unknown host")
        with self.assertRaisesRegex(RemotePDFError, "nao significa"):
            download_and_analyze_public_pdf(SOURCE, NAME, opener=fail)

    def test_pdf_invalid_structure_is_reported_not_a_false_negative(self):
        with self.assertRaises(RemotePDFError):
            download_and_analyze_public_pdf(
                SOURCE, NAME,
                opener=lambda *_a, **_kw: FakeResponse(b"%PDF-not a real PDF"),
            )

    def test_only_valid_name_triggers_network(self):
        calls = []
        with self.assertRaises(RemotePDFError):
            download_and_analyze_public_pdf(
                SOURCE, "PAULO",
                opener=lambda *_a, **_kw: calls.append("download"),
            )
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
