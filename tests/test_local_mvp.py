"""Offline local-MVP integration and privacy tests."""

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from convocalivre.cli import main
from convocalivre.diagnostics import diagnose_pdf
from convocalivre.local_batch import (
    MAX_BATCH_FILES, analyze_local_files, collect_files,
)


def make_pdf(path: Path, pages: list[str | None]) -> None:
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    ref = writer._add_object(font)
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        if text is None:
            continue
        stream = DecodedStreamObject()
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream.set_data(
            ("BT /F1 12 Tf 40 700 Td (" + escaped + ") Tj ET").encode("ascii")
        )
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): ref})
        })
        page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as file:
        writer.write(file)


class LocalMVPTests(unittest.TestCase):
    def test_gui_module_import_does_not_require_display(self):
        # The GUI must not create a Tk root on package import.
        from convocalivre import gui
        self.assertTrue(callable(gui.launch))
        self.assertTrue(callable(gui.main))

    def test_diagnose_page_status_is_text_free(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "teste.pdf"
            make_pdf(pdf, ["Fica convocada ANA PAULA SILVA.", None])
            report = diagnose_pdf(pdf)
            self.assertEqual(report["page_count"], 2)
            self.assertEqual(report["pages_with_extractable_text"], 1)
            self.assertEqual(report["pages_without_extractable_text"], [2])
            self.assertEqual(report["diagnosis"], "partially_extractable_or_errors")
            self.assertEqual(report["pdf_sha256"], sha256(pdf.read_bytes()).hexdigest())
            rendered = json.dumps(report, ensure_ascii=False)
            self.assertNotIn("ANA PAULA", rendered)
            self.assertNotIn("Fica convocada", rendered)
            self.assertIn("plain_chars", rendered)

    def test_diagnose_all_blank_is_inconclusive_not_scanned(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "sem_texto.pdf"
            make_pdf(pdf, [None])
            report = diagnose_pdf(pdf)
            self.assertEqual(report["diagnosis"], "no_extractable_text")
            self.assertIn("nao prova", report["notice"].lower())

    def test_diagnose_malformed_file_rejected(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "fake.pdf"
            pdf.write_bytes(b"html body")
            with self.assertRaisesRegex(ValueError, "cabecalho PDF"):
                diagnose_pdf(pdf)

    def test_batch_collect_files_only_allowed_and_no_duplicates(self):
        with TemporaryDirectory() as folder:
            p = Path(folder)
            (p / "a.txt").write_text("ANA PAULA SILVA convocada", encoding="utf-8")
            (p / "ignore.exe").write_bytes(b"x")
            make_pdf(p / "b.PDF", ["Fica nomeada ANA PAULA SILVA"])
            files = collect_files([p, p / "a.txt"])
            self.assertEqual(len(files), 2)
            self.assertEqual({x.name for x in files}, {"a.txt", "b.PDF"})

    def test_batch_local_reports_and_isolated_failure(self):
        with TemporaryDirectory() as folder:
            p = Path(folder)
            (p / "a.txt").write_text("ANA PAULA SILVA convocada", encoding="utf-8")
            make_pdf(p / "b.pdf", [None])
            bad = p / "c.pdf"
            bad.write_text("<not a PDF>", encoding="utf-8")
            batch = analyze_local_files([p / "a.txt", p / "b.pdf", bad], "Ana Paula Silva")
            self.assertEqual(batch["files_total"], 3)
            self.assertEqual(batch["files_analyzed"], 2)
            self.assertEqual(batch["files_failed"], 1)
            self.assertEqual(batch["files_with_name"], 1)
            self.assertEqual(batch["mention_count"], 1)
            self.assertEqual(batch["documents"][2]["status"], "error")
            self.assertEqual(batch["documents"][2]["error_type"], "ValueError")

    def test_search_progress_events_for_success_and_error(self):
        # Progress is emitted around each document without blocking analysis.
        with TemporaryDirectory() as folder:
            p = Path(folder)
            good = p / "a.txt"
            bad = p / "b.pdf"
            good.write_text("ANA PAULA SILVA convocada", encoding="utf-8")
            bad.write_text("invalid PDF", encoding="utf-8")
            events = []
            report = analyze_local_files(
                [good, bad], "Ana Paula Silva",
                on_progress=lambda index, total, filename, phase:
                    events.append((index, total, filename, phase)),
            )
            self.assertEqual(events, [
                (1, 2, "a.txt", "start"),
                (1, 2, "a.txt", "done"),
                (2, 2, "b.pdf", "start"),
                (2, 2, "b.pdf", "done"),
            ])
            self.assertEqual(report["mention_count"], 1)
            self.assertEqual(report["files_failed"], 1)

    def test_search_progress_is_optional_and_report_unchanged(self):
        with TemporaryDirectory() as folder:
            p = Path(folder) / "edital.txt"
            p.write_text("Fica convocada ANA PAULA SILVA", encoding="utf-8")
            snapshots = []
            with_progress = analyze_local_files(
                [p], "Ana Paula Silva",
                on_progress=lambda *event: snapshots.append(event),
            )
            without_progress = analyze_local_files([p], "Ana Paula Silva")
            for key in ("files_total", "files_analyzed", "files_failed",
                        "files_with_name", "mention_count", "documents"):
                self.assertEqual(with_progress[key], without_progress[key])
            self.assertEqual(len(snapshots), 2)

    def test_max_batch_files_limit(self):
        with TemporaryDirectory() as folder:
            p = Path(folder)
            for i in range(MAX_BATCH_FILES + 1):
                (p / f"{i:03d}.txt").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Limite"):
                collect_files([p])

    def test_cli_diagnose_json_output_has_no_name(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "edital.pdf"
            make_pdf(pdf, ["ANA PAULA SILVA nomeada"])
            out = Path(folder) / "diag.json"
            code = main(["diagnose", str(pdf), "--output", str(out)])
            self.assertEqual(code, 0)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result["page_count"], 1)
            self.assertNotIn("ANA PAULA SILVA", out.read_text(encoding="utf-8"))

    def test_cli_batch_with_directory_and_legacy_command(self):
        with TemporaryDirectory() as folder:
            txt = Path(folder) / "lista.txt"
            txt.write_text("ANA PAULA SILVA nomeada", encoding="utf-8")
            out = Path(folder) / "resultado.json"
            self.assertEqual(
                main(["batch", folder, "--name", "Ana Paula Silva",
                      "--output", str(out)]),
                0,
            )
            doc = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(doc["files_total"], 1)
            self.assertEqual(doc["mention_count"], 1)
            with redirect_stdout(StringIO()) as capture:
                self.assertEqual(main([str(txt), "--name", "Ana Paula Silva"]), 0)
            self.assertEqual(json.loads(capture.getvalue())["match_count"], 1)


if __name__ == "__main__":
    unittest.main()
