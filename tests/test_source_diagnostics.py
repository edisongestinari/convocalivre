"""No-network tests for sanitized source failure diagnostics."""

import socket
import unittest
from urllib.error import HTTPError, URLError

from convocalivre.source_diagnostics import (
    SourceDocumentError, sanitized_page_text_health, source_failure_code,
)


class SourceDiagnosticsTests(unittest.TestCase):
    def test_http_failure_codes_do_not_leak_request_text(self):
        cases = [(403, "http_access_denied"), (404, "http_not_found"),
                 (429, "http_rate_limited"), (503, "http_server_error")]
        for status, expected in cases:
            with self.subTest(status=status):
                error = HTTPError(
                    "https://example.invalid/private_name.pdf",
                    status, "private candidate string", None, None
                )
                self.assertEqual(source_failure_code(error), expected)
                self.assertNotIn("private", source_failure_code(error))

    def test_dns_timeout_and_explicit_errors(self):
        self.assertEqual(
            source_failure_code(URLError(socket.gaierror(-2, "lookup failed"))),
            "dns_error",
        )
        self.assertEqual(
            source_failure_code(URLError(TimeoutError("private text"))),
            "network_timeout",
        )
        self.assertEqual(source_failure_code(TimeoutError()), "network_timeout")
        self.assertEqual(
            source_failure_code(SourceDocumentError("non_pdf_response")),
            "non_pdf_response",
        )

    def test_page_quality_only_contains_counts(self):
        class FakePage:
            def extract_text(self, **kwargs):
                return "PESSOA FICTICIA" if not kwargs else ""
        result = sanitized_page_text_health(FakePage())
        self.assertEqual(result["plain_chars"], 15)
        self.assertEqual(result["layout_chars"], 0)
        self.assertTrue(result["text_available"])
        self.assertNotIn("FICTICIA", str(result))

    def test_all_failed_modes_are_unresolved_not_blank(self):
        class FakePage:
            def extract_text(self, **kwargs):
                raise NotImplementedError("private text")
        result = sanitized_page_text_health(FakePage())
        self.assertIsNone(result["plain_chars"])
        self.assertIsNone(result["layout_chars"])
        self.assertTrue(result["extraction_failed"])


if __name__ == "__main__":
    unittest.main()
