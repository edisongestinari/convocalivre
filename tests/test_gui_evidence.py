"""Evidence UI summaries are conservative and fully offline."""

import unittest

from convocalivre.gui_evidence import summarize_match, summarize_empty_report


class EvidenceSummaryTests(unittest.TestCase):
    def test_edital_exclusao_shows_support_without_legal_claim(self):
        match = {
            "page_number": 13,
            "act_type": "desistencia_exclusao",
            "act_indicator": "exclui",
            "act_basis": "table_same_column_numbered_edital_two_indicators",
            "act_context_lines": [189, 196],
            "act_heading_excerpt": "EDITAL 314/2026",
            "extraction_mode": "layout_fallback",
            "excerpt": "EXCLUI ANA PAULA SILVA",
        }
        report = {"pages_without_text": [7]}
        text = summarize_match(match, report)
        self.assertIn("Possível exclusão/desistência", text)
        self.assertIn("189, 196", text)
        self.assertIn("EDITAL 314/2026", text)
        self.assertIn("layout", text)
        self.assertIn("1 página(s) sem texto extraível", text)
        self.assertIn("NÃO É CONFIRMAÇÃO", text)
        self.assertIn("REVISAO OBRIGATORIA", text)

    def test_cross_page_evidence_points_to_previous_physical_page(self):
        match = {
            "page_number": 5, "act_type": "nomeacao",
            "act_basis": "adjacent_page_unfinished_portaria_named_recipient",
            "act_context_lines": [22, 23], "act_context_page_offset": -1,
        }
        result = summarize_match(match, {"pages_without_text": []})
        self.assertIn("página física anterior", result)
        self.assertIn("Página física da ocorrência: 5", result)

    def test_indeterminate_does_not_invent_admin_act(self):
        text = summarize_match(
            {"page_number": 3, "act_type": "indeterminado",
             "act_basis": "no_unambiguous_indicator"},
            {},
        )
        self.assertIn("Ato indeterminado", text)
        self.assertIn("Não foi possível", text)
        self.assertNotIn("Indicador textual:", text)
        self.assertNotIn("Cabeçalho identificado:", text)

    def test_no_matches_with_unreadable_pages_is_not_negative_proof(self):
        result = summarize_empty_report(
            {"page_count": 40, "pages_without_text": [2, 15, 17]},
            "analyzed",
        )
        self.assertIn("3 de 40", result)
        self.assertIn("inconclusiva", result)
        self.assertNotIn("Nome não encontrado", result)

    def test_failed_pdf_never_claims_absence(self):
        self.assertIn(
            "não prova", summarize_empty_report({}, "error")
        )


if __name__ == "__main__":
    unittest.main()
