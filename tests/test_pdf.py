"""Synthetic-only PDF fixtures: never publish candidate names or real gazettes."""

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from contextlib import redirect_stdout
from io import StringIO

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from convocalivre.pdf import analyze_pdf
from convocalivre.cli import main


def make_pdf(path: Path, pages: list[str | None]) -> None:
    """Build lightweight real PDFs with ordinary Latin text and blank pages."""
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    font_ref = writer._add_object(font)  # Private test-only PDF fixture helper.
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        if text is None:
            continue
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 40 700 Td ({escaped}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
        })
    with path.open("wb") as handle:
        writer.write(handle)


class PDFAnalysisTests(unittest.TestCase):
    def test_page_number_excerpt_and_document_hash(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "edital.pdf"
            make_pdf(pdf, ["Primeira pagina: texto comum.",
                           "EDITAL: fica convocado JOAO SILVA PEREIRA para documentos."])
            report = analyze_pdf(pdf, "Joao Silva Pereira",
                                 source_url="https://example.invalid/documento")
            self.assertEqual(report["match_count"], 1)
            self.assertEqual(report["result"], "possible_related_act")
            self.assertEqual(report["matches"][0]["page_number"], 2)
            self.assertIn("JOAO SILVA PEREIRA", report["matches"][0]["excerpt"])
            self.assertEqual(report["document_sha256"], sha256(pdf.read_bytes()).hexdigest())
            self.assertEqual(report["page_count"], 2)
            self.assertEqual(report["source_url_unverified"], "https://example.invalid/documento")

    def test_terms_do_not_spill_across_pages(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "text.pdf"
            make_pdf(pdf, ["Fica convocado outro candidato.", "Lista: ANA PAULA LIMA."])
            report = analyze_pdf(pdf, "Ana Paula Lima")
            self.assertEqual(report["result"], "name_mentioned_only")

    def test_scanned_or_blank_page_warning(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "sem-texto.pdf"
            make_pdf(pdf, [None, None])
            report = analyze_pdf(pdf, "Ana Paula Lima")
            self.assertEqual(report["result"], "no_extractable_text")
            self.assertEqual(report["pages_without_text"], [1, 2])
            self.assertEqual(report["matches"], [])
            self.assertIn("OCR", " ".join(report["warnings"]))

    def test_invalid_file_and_size_limit(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "broken.pdf"
            pdf.write_bytes(b"not a PDF")
            with self.assertRaisesRegex(ValueError, "cabecalho PDF"):
                analyze_pdf(pdf, "Ana Paula Lima")
            make_pdf(pdf, ["ANA PAULA LIMA convocada"])
            with self.assertRaisesRegex(ValueError, "acima do limite"):
                analyze_pdf(pdf, "Ana Paula Lima", max_pdf_bytes=5)

    def test_cli_pdf_json_output(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "sample.pdf"
            make_pdf(pdf, ["ANA PAULA LIMA convocada"])
            buffer = StringIO()
            with redirect_stdout(buffer):
                code = main([str(pdf), "--name", "Ana Paula Lima"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(buffer.getvalue())["matches"][0]["page_number"], 1)

    def test_cli_txt_is_still_supported(self):
        with TemporaryDirectory() as folder:
            txt = Path(folder) / "sample.txt"
            txt.write_text("ANA PAULA LIMA convocada", encoding="utf-8")
            buffer = StringIO()
            with redirect_stdout(buffer):
                code = main([str(txt), "--name", "Ana Paula Lima"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(buffer.getvalue())["match_count"], 1)


if __name__ == "__main__":
    unittest.main()
