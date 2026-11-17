"""Offline tests for the live-source audit infrastructure (no network)."""

from io import BytesIO
import json
import unittest

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from convocalivre.external_pdf_audit import (
    _matrix_metrics,
    evaluate_public_pdfs, name_digest, recover_name_from_page
)


def make_pdf(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    font_ref = writer._add_object(font)
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = DecodedStreamObject()
    stream.set_data(
        ("BT /F1 12 Tf 40 700 Td (" + escaped + ") Tj ET").encode("ascii")
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
    })
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


class ExternalAuditTests(unittest.TestCase):
    def test_name_digest_accents_and_spacing(self):
        self.assertEqual(name_digest("João   da SILVA"), name_digest("JOAO DA SILVA"))

    def test_recover_real_pdf_text_transiently(self):
        sample = make_pdf("Fica nomeada ANA PAULA SILVA para cargo efetivo.")
        reader = __import__("pypdf").PdfReader(BytesIO(sample))
        name, method = recover_name_from_page(
            reader.pages[0], name_digest("Ana Paula Silva")
        )
        self.assertEqual(name, "ANA PAULA SILVA")
        self.assertEqual(method, "plain")

    def test_human_reference_and_cross_document_negative(self):
        names = {"a": "ANA PAULA SILVA", "b": "MARIA DE SOUSA"}
        blobs = {
            "https://example.invalid/a.pdf":
                make_pdf("Fica convocada ANA PAULA SILVA para documentos."),
            "https://example.invalid/b.pdf":
                make_pdf("MARIA DE SOUSA foi nomeada."),
        }
        manifest = {
            "dataset_kind": "human_annotated_public_pdfs",
            "sources": [
                {
                    "id": "a", "url": "https://example.invalid/a.pdf",
                    "cases": [{"id": "a1", "page_number": 1,
                               "name_sha256": name_digest(names["a"]),
                               "expected": "convocacao"}],
                },
                {
                    "id": "b", "url": "https://example.invalid/b.pdf",
                    "cases": [{"id": "b1", "page_number": 1,
                               "name_sha256": name_digest(names["b"]),
                               "expected": "nomeacao"}],
                },
            ],
            "negative_pairs": [
                {"id": "not-in-b", "target_case": "a1", "in_source": "b"},
            ],
        }
        result = evaluate_public_pdfs(manifest, lambda url: blobs[url])
        self.assertEqual(result["available_sources"], 2)
        self.assertEqual(result["name_presence"],
                         {"tp": 2, "fp": 0, "fn": 0, "tn": 1,
                          "note": result["name_presence"]["note"]})
        self.assertEqual(result["act_classification"]["n"], 2)
        self.assertEqual(result["act_classification"]["exact_matches"], 2)
        serialized = json.dumps(result)
        for secret_name in names.values():
            self.assertNotIn(secret_name, serialized)

    def test_unavailable_source_is_not_true_negative(self):
        manifest = {
            "dataset_kind": "human_annotated_public_pdfs",
            "sources": [{
                "id": "fail", "url": "https://example.invalid/fail.pdf",
                "cases": [{"id": "case1", "page_number": 1,
                           "name_sha256": "0" * 64, "expected": "convocacao"}],
            }],
        }
        def unavailable(_url):
            raise TimeoutError("source unavailable")

        result = evaluate_public_pdfs(manifest, unavailable)
        self.assertEqual(result["available_sources"], 0)
        self.assertEqual(result["name_presence"]["tn"], 0)
        self.assertEqual(result["act_classification"]["n"], 0)
        self.assertEqual(result["case_results"][0]["status"], "source_unavailable")
        self.assertNotIn("TimeoutError:", json.dumps(result))

    def test_unresolved_digest_is_not_counted_as_absent(self):
        manifest = {
            "dataset_kind": "human_annotated_public_pdfs",
            "sources": [{
                "id": "a", "url": "https://example.invalid/a.pdf",
                "cases": [{"id": "a1", "page_number": 1,
                           "name_sha256": "0" * 64, "expected": "nomeacao"}],
            }],
        }
        result = evaluate_public_pdfs(
            manifest, lambda _: make_pdf("ALICE MARIA SILVA.")
        )
        self.assertEqual(result["available_sources"], 1)
        self.assertEqual(result["unresolved_positive_cases"], 1)
        self.assertEqual(result["act_classification"]["n"], 0)
        self.assertEqual(result["name_presence"]["tn"], 0)

    def test_class_counts_and_zero_denominators(self):
        result = _matrix_metrics([
            ("convocacao", "indeterminado"),
            ("nomeacao", "nomeacao"),
        ])
        self.assertEqual(result["n"], 2)
        self.assertEqual(result["exact_matches"], 1)
        self.assertEqual(result["per_class"]["convocacao"]["fn"], 1)
        self.assertEqual(result["per_class"]["nomeacao"]["tp"], 1)
        self.assertIsNone(result["per_class"]["resultado_homologacao"]["precision"])


if __name__ == "__main__":
    unittest.main()
