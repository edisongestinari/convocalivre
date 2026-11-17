"""Synthetic-only regression tests inspired by real public document *structures*.

All candidates and act contents here are fictional. No personal information
from published real PDFs is committed to the repository.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from convocalivre.structured_context import (
    infer_same_page_table, infer_previous_page_continuation,
)
from convocalivre.pdf import analyze_pdf


def locate(text: str, name: str = "ANA PAULA SILVA"):
    start = text.index(name)
    return start, start + len(name)


def write_lines_pdf(path: Path, pages: list[list[str]]) -> None:
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    font_ref = writer._add_object(font)
    for lines in pages:
        page = writer.add_blank_page(width=612, height=792)
        operations = [b"BT /F1 12 Tf 40 700 Td"]
        for row in lines:
            if not row.isascii():
                raise ValueError("Synthetic PDF fixture must be ASCII.")
            escaped = row.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            operations.append(f"({escaped}) Tj".encode("ascii"))
            operations.append(b"0 -16 Td")
        operations.append(b"ET")
        stream = DecodedStreamObject()
        stream.set_data(b"\n".join(operations))
        page[NameObject("/Contents")] = writer._add_object(stream)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
        })
    with path.open("wb") as out:
        writer.write(out)


CONVO = [
    "EDITAL DE CONVOCACAO No 14/2026 DE 14 DE OUTUBRO DE 2026.",
    "DISPOE SOBRE A CONVOCACAO DE CANDIDATO APROVADO",
    "PREFEITURA MUNICIPAL DE EXEMPLO",
    "RESOLVE:",
    "CONVOCAR o candidato abaixo relacionado, aprovado no processo seletivo",
    "O nao comparecimento implicara na desistencia da funcao.",
    "NOME DO CANDIDATO CARGO CLASSIFICACAO",
    "ANA PAULA SILVA MONITOR 10 LUGAR",
]

RESULTS = [
    "ANEXOI",
    "RESULTADO FINAL - PROCESSO SELETIVO - EDITAL No 001/2026",
    "LISTA GERAL - CANDIDATOS APROVADOS",
    "COZINHEIRO",
    "POS. INSCRICAO NOME DATA NASC LP MAT CG NOTA FINAL",
    "1 02 - 00124 ANA PAULA SILVA 01/01/2000 36,00 24,00 30,00 90,00",
    "2 02 - 00156 MARIA DE SOUSA 01/01/2000 30,00 25,00 30,00 85,00",
    "FISCAL TRIBUTARIO",
    "POS. INSCRICAO NOME DATA NASC LP MAT CG NOTA FINAL",
    "1 02 - 00106 JOAO LIMA ALVES 01/01/2000 40,00 27,00 30,00 97,00",
]

JOINVILLE_ANNEX = [
    "Pagina 1 de 30",
    "MUNICIPIO DE EXEMPLO",
    "ANEXO I - EDITAL DE HOMOLOGACAO DO RESULTADO FINAL E CLASSIFICACAO - Ampla Concorrencia",
    "CONCURSO PUBLICO No 004/2026",
    "0824 - PROFESSOR DE SERIES INICIAIS",
    "Nome Inscricao Matematica Didatica Nota Final Classificacao",
    "ANA PAULA SILVA 7290004535 20.00 10.00 4.00 79.00 1",
    "MARIA DE SOUSA 7290009645 20.00 7.00 4.00 76.50 2",
]

PREVIOUS = [
    "DIARIO OFICIAL",
    "PORTARIA No 2.211, DE 19 DE JUNHO DE 2026",
    "Fica instaurado processo disciplinar contra outro servidor.",
    "PORTARIA No 2.212, DE 19 DE JUNHO DE 2026",
    "Fica nomeada, a partir de 22/06/2026, para o cargo de",
    "provimento efetivo de ATENDENTE DE EDUCACAO INFANTIL",
    "referencia 4, Anexo I, da Lei Complementar no",
]

NEXT = [
    "DIARIO OFICIAL",
    "MUNICIPIO DE EXEMPLO - EDICAO No 1697",
    "Sexta-feira 19 de junho de 2026 Pagina 5",
    "DEPARTAMENTO DE COMUNICACAO SOCIAL",
    "232, de 20 de dezembro de 2023, a senhora ANA PAULA SILVA, portadora de documento.",
    "A nomeacao ao cargo efetivo especificado atende ao concurso publico.",
    "PORTARIA No 2.213, DE 19 DE JUNHO DE 2026",
    "Fica exonerado JOAO LIMA ALVES, a pedido.",
]


class StructuredContextTests(unittest.TestCase):
    def test_convocation_candidate_table(self):
        text = "\n".join(CONVO)
        result = infer_same_page_table(text, *locate(text))
        self.assertEqual(result["act_type"], "convocacao")
        self.assertEqual(result["act_indicator"], "convocar")
        self.assertEqual(result["act_context_lines"], [1, 5, 7])

    def test_convocation_does_not_mean_exclusion_on_conditional_withdrawal(self):
        text = "\n".join(CONVO)
        result = infer_same_page_table(text, *locate(text))
        self.assertEqual(result["act_type"], "convocacao")

    def test_unrelated_candidate_list_does_not_become_convocation(self):
        rows = CONVO.copy()
        rows[4] = "A prefeitura divulga candidatos abaixo relacionados"
        text = "\n".join(rows)
        self.assertIsNone(infer_same_page_table(text, *locate(text)))

    def test_second_act_heading_blocks_convocation(self):
        rows = CONVO.copy()
        rows.insert(6, "PORTARIA No 234/2026")
        text = "\n".join(rows)
        self.assertIsNone(infer_same_page_table(text, *locate(text)))

    def test_homologation_annex_with_ranked_candidate(self):
        text = "\n".join(RESULTS)
        for name in ("ANA PAULA SILVA", "MARIA DE SOUSA", "JOAO LIMA ALVES"):
            with self.subTest(name=name):
                result = infer_same_page_table(text, *locate(text, name))
                self.assertEqual(result["act_type"], "resultado_homologacao")
                self.assertEqual(result["act_indicator"], "resultado final")

    def test_homologation_annex_name_first_scores_table(self):
        text = "\n".join(JOINVILLE_ANNEX)
        for name in ("ANA PAULA SILVA", "MARIA DE SOUSA"):
            with self.subTest(name=name):
                result = infer_same_page_table(text, *locate(text, name))
                self.assertIsNotNone(result)
                self.assertEqual(result["act_type"], "resultado_homologacao")
                self.assertEqual(result["act_basis"],
                                 "annex_homologated_named_candidate_scores_table")

    def test_name_first_table_without_annex_header_abstains(self):
        text = "\n".join(JOINVILLE_ANNEX[4:])
        self.assertIsNone(infer_same_page_table(text, *locate(text)))

    def test_name_first_table_without_registration_abstains(self):
        rows = [
            line.replace("ANA PAULA SILVA 7290004535", "ANA PAULA SILVA")
            for line in JOINVILLE_ANNEX
        ]
        text = "\n".join(rows)
        self.assertIsNone(infer_same_page_table(text, *locate(text)))

    def test_ranked_list_without_results_header_abstains(self):
        text = "\n".join(RESULTS[2:])
        self.assertIsNone(infer_same_page_table(text, *locate(text)))

    def test_final_result_other_person_does_not_classify_neutral_line(self):
        text = "\n".join(RESULTS + ["REGISTRO: ANA PAULA SILVA"])
        result = infer_same_page_table(text, *locate(text, "ANA PAULA SILVA"))
        # The first occurrence is in the actual results; a stand-alone
        # neutral mention after the ranking is not evidence by itself.
        self.assertEqual(result["act_type"], "resultado_homologacao")

    def test_cross_page_portaria_named_recipient(self):
        previous, current = "\n".join(PREVIOUS), "\n".join(NEXT)
        result = infer_previous_page_continuation(previous, current, *locate(current))
        self.assertEqual(result["act_type"], "nomeacao")
        self.assertEqual(result["act_context_page_offset"], -1)
        self.assertEqual(
            result["act_basis"],
            "adjacent_page_unfinished_portaria_named_recipient",
        )

    def test_cross_page_prior_act_already_complete_abstains(self):
        previous, current = "\n".join(PREVIOUS) + ".", "\n".join(NEXT)
        self.assertIsNone(infer_previous_page_continuation(
            previous, current, *locate(current)
        ))

    def test_cross_page_new_portaria_between_action_and_boundary_abstains(self):
        previous = "\n".join(PREVIOUS + [
            "PORTARIA No 2.213, DE 19 DE JUNHO DE 2026"
        ])
        current = "\n".join(NEXT)
        self.assertIsNone(infer_previous_page_continuation(
            previous, current, *locate(current)
        ))

    def test_cross_page_other_person_not_recipient_abstains(self):
        current = "\n".join(
            line.replace("a senhora ANA PAULA SILVA", "o servidor JOAO LIMA ALVES e ANA PAULA SILVA")
            for line in NEXT
        )
        self.assertIsNone(infer_previous_page_continuation(
            "\n".join(PREVIOUS), current, *locate(current)
        ))

    def test_cross_page_other_body_text_before_name_abstains(self):
        current = "\n".join(NEXT[:4] + [
            "Publicacao de outras providencias.",
            *NEXT[4:],
        ])
        self.assertIsNone(infer_previous_page_continuation(
            "\n".join(PREVIOUS), current, *locate(current)
        ))

    def test_cross_page_followup_missing_abstains(self):
        current = "\n".join(
            line.replace("A nomeacao ao cargo", "A autorizacao ao cargo")
            for line in NEXT
        )
        self.assertIsNone(infer_previous_page_continuation(
            "\n".join(PREVIOUS), current, *locate(current)
        ))

    def test_pdf_adapter_classifies_three_structures(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "publicacao_sintetica.pdf"
            write_lines_pdf(pdf, [
                CONVO,
                RESULTS,
                JOINVILLE_ANNEX,
                PREVIOUS,
                NEXT,
            ])
            for name, page, expected in [
                ("ANA PAULA SILVA", 1, "convocacao"),
                ("MARIA DE SOUSA", 2, "resultado_homologacao"),
                ("ANA PAULA SILVA", 3, "resultado_homologacao"),
            ]:
                report = analyze_pdf(pdf, name)
                match = next(m for m in report["matches"] if m["page_number"] == page)
                self.assertEqual(match["act_type"], expected)
                self.assertIn(page, report["structured_context_pages"])
            report = analyze_pdf(pdf, "ANA PAULA SILVA")
            fifth = next(m for m in report["matches"] if m["page_number"] == 5)
            self.assertEqual(fifth["act_type"], "nomeacao")
            self.assertIn(5, report["structured_context_pages"])

    def test_pdf_adapter_does_not_turn_exoneration_into_nomination(self):
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "negative.pdf"
            write_lines_pdf(pdf, [PREVIOUS, NEXT])
            report = analyze_pdf(pdf, "JOAO LIMA ALVES")
            self.assertEqual(report["match_count"], 1)
            self.assertEqual(report["matches"][0]["act_type"], "indeterminado")


if __name__ == "__main__":
    unittest.main()
