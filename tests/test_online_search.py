"""Network-free tests for user-triggered Querido Diario lookups."""

from io import BytesIO
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
import unittest

from convocalivre.online_search import (
    OnlineSearchError, MAX_RESPONSE_BYTES,
    search_gazettes, validate_search,
)


class FakeResponse:
    def __init__(self, payload, url="https://api.queridodiario.ok.org.br/gazettes"):
        self.payload = payload
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self, amount):
        return self.payload[:amount]

    def geturl(self):
        return self.url


class OnlineSearchTests(unittest.TestCase):
    def test_validation_rejects_non_name_and_invalid_ibge_code(self):
        for name, code in (
            ("PAULO", "4106605"), ("ANA 12 SILVA", "4106605"),
            ("ANA PAULA", "410660"), ('"ANA PAULA"', "4106605"),
        ):
            with self.subTest(name=name, code=code):
                with self.assertRaises(ValueError):
                    validate_search(name, code)
        self.assertEqual(
            validate_search("  Joao   da  Silva ", " 4106605 "),
            ("Joao da Silva", "4106605"),
        )

    def test_one_request_exact_phrase_and_safe_result(self):
        calls = []
        payload = {
            "total_gazettes": 1,
            "gazettes": [{
                "date": "2026-11-12",
                "territory_id": "4106605",
                "territory_name": "Cruzeiro do Oeste",
                "edition_number": "314",
                "url": "https://files.example.org/gazeta.pdf",
                "excerpts": ["<em>ANA PAULA SILVA</em> convocada em edital."],
            }],
        }

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(json.dumps(payload).encode())

        result = search_gazettes("ANA PAULA SILVA", "4106605", opener=opener)
        self.assertEqual(len(calls), 1)
        self.assertLessEqual(calls[0][1], 15)
        q = parse_qs(urlparse(calls[0][0].full_url).query)
        self.assertEqual(q["territory_ids"], ["4106605"])
        self.assertEqual(q["querystring"], ['"ANA PAULA SILVA"'])
        self.assertEqual(q["size"], ["10"])
        self.assertEqual(result["returned_count"], 1)
        self.assertEqual(result["results"][0]["date"], "2026-11-12")
        self.assertEqual(result["results"][0]["excerpt"], "ANA PAULA SILVA convocada em edital.")
        self.assertEqual(result["results"][0]["pdf_url"], "https://files.example.org/gazeta.pdf")
        self.assertIn("possiveis mencoes", result["notice"].lower())
        self.assertNotIn("act_type", json.dumps(result))

    def test_invalid_urls_and_foreign_territory_are_not_presented(self):
        payload = {
            "gazettes": [
                {"territory_id": "4106605", "date": "2026-11-15",
                 "url": "file:///C:/segredo.pdf",
                 "excerpts": ["<script>alert(1)</script>Nome &amp; cargo"]},
                {"territory_id": "4106606", "date": "2026-11-14",
                 "url": "https://files.example.org/outro.pdf"},
                {"territory_id": "4106605", "date": "2026-11-13",
                 "url": "javascript:alert(1)"},
                {"territory_id": "4106605", "date": "2026-11-11",
                 "url": "https://127.0.0.1/private"},
                {"territory_id": "4106605", "date": "2026-11-10",
                 "url": "https://[invalid/private"},
            ],
        }
        r = search_gazettes(
            "ANA PAULA SILVA", "4106605",
            opener=lambda *_a, **_k: FakeResponse(json.dumps(payload).encode()),
        )
        self.assertEqual(r["returned_count"], 4)
        self.assertTrue(all(not x["pdf_url"] for x in r["results"]))
        self.assertNotIn("<script>", r["results"][0]["excerpt"])

    def test_unrecognized_payload_is_not_no_results(self):
        for payload in [b"not json", b"[]", b'{"items":[]}', b'{"gazettes":"bad"}']:
            with self.subTest(payload=payload):
                with self.assertRaises(OnlineSearchError):
                    search_gazettes(
                        "ANA PAULA", "4106605",
                        opener=lambda *_a, **_k: FakeResponse(payload),
                    )

    def test_api_http_and_timeout_are_sanitized(self):
        def deny(*_a, **_k):
            raise HTTPError("https://example.org/?name=PRIVATE", 403,
                            "PRIVATE", None, None)
        with self.assertRaises(OnlineSearchError) as caught:
            search_gazettes("ANA PAULA", "4106605", opener=deny)
        self.assertNotIn("ANA PAULA", str(caught.exception))
        self.assertNotIn("PRIVATE", str(caught.exception))

        def timeout(*_a, **_k):
            raise URLError("unavailable")
        with self.assertRaises(OnlineSearchError):
            search_gazettes("ANA PAULA", "4106605", opener=timeout)

    def test_redirect_and_large_response_rejected(self):
        with self.assertRaises(OnlineSearchError):
            search_gazettes(
                "ANA PAULA", "4106605",
                opener=lambda *_a, **_k: FakeResponse(
                    b'{"gazettes":[]}', "https://evil.example/search"
                ),
            )
        with self.assertRaises(OnlineSearchError):
            search_gazettes(
                "ANA PAULA", "4106605",
                opener=lambda *_a, **_k: FakeResponse(
                    b"x" * (MAX_RESPONSE_BYTES + 1)
                ),
            )

    def test_valid_zero_results_does_not_claim_name_absent(self):
        r = search_gazettes(
            "ANA PAULA", "4106605",
            opener=lambda *_a, **_k: FakeResponse(b'{"gazettes":[]}'),
        )
        self.assertEqual(r["returned_count"], 0)
        self.assertIn("prova", r["notice"])


if __name__ == "__main__":
    unittest.main()
