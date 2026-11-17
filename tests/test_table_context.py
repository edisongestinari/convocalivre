"""Synthetic-only regressions for mixed two-column official gazette pages."""

import unittest

from convocalivre.table_context import infer_table_act


def make_layout(right: list[str], left: list[str] | None = None) -> str:
    """Create fixed-width layout lines similar to pypdf layout extraction."""
    left = left or []
    return "".join(
        (left[i] if i < len(left) else "").ljust(115) + line + "\n"
        for i, line in enumerate(right)
    )


def infer_for(text: str, name: str = "ANA PAULA SILVA") -> dict | None:
    start = text.index(name)
    return infer_table_act(text, start, start + len(name))


class TableContextTests(unittest.TestCase):
    def test_related_edital_in_right_column_over_left_convocation(self):
        right = [
            "EDITAL Nº 314/2026 DE 04 DE NOVEMBRO",
            "SUMULA: Exclui o candidato aprovado em concurso",
            "CONSIDERANDO a desistencia da vaga",
            "EXCLUI o candidato abaixo relacionado da lista dos aprovados",
            "por motivo particular, desistindo da nomeacao.",
            "CARGO: MOTORISTA - 40H",
            "3520         ANA PAULA SILVA                      [CPF]",
        ]
        left = [
            "CONVOCA outro servidor", "AVISO DE CONVOCACAO", "Texto municipal",
            "CONVOCA outro servidor", "texto do outro municipio", "texto", "texto",
        ]
        result = infer_for(make_layout(right, left))
        self.assertIsNotNone(result)
        self.assertEqual(result["act_type"], "desistencia_exclusao")
        self.assertEqual(result["act_indicator"], "exclui")
        self.assertIn("EDITAL", result["act_heading_excerpt"])
        self.assertEqual(result["act_context_lines"], [2, 3])
        self.assertTrue(result["requires_manual_review"])

    def test_references_to_prior_edital_do_not_override_active_exclusion(self):
        # Regression from a real *layout pattern*, using fictional candidate.
        # A reference to "Edital de Convocacao 313/2026" does not mean the
        # current numbered exclusion edital is itself a convocation.
        right = [
            "EDITAL Nº 314/2026 DE 04 DE NOVEMBRO",
            "SUMULA: Exclui o candidato aprovado em CONCURSO PUBLICO",
            "Edital de Abertura nº 001/2024.",
            "O PREFEITO MUNICIPAL, no uso de suas atribuicoes:",
            "EXCLUI o candidato abaixo relacionado da lista dos aprovados,",
            "referente ao CONCURSO PUBLICO - Edital nº 001/2024 e",
            "Edital de Convocacao nº 313/2026, publicado anteriormente,",
            "motivo particular, desistindo da nomeacao.",
            "CARGO: MOTORISTA - 40H",
            "3520         ANA PAULA SILVA                     [CPF]",
        ]
        left = [
            "PORTARIA 44/2026", "CONVOCA outro servidor", "Texto externo",
            "Texto externo", "Texto externo", "Texto externo",
            "AVISO DE LICITACAO Nº 99/2026", "Texto externo",
            "Texto externo", "Texto externo",
        ]
        result = infer_for(make_layout(right, left))
        self.assertIsNotNone(result)
        self.assertEqual(result["act_type"], "desistencia_exclusao")
        self.assertEqual(result["act_context_lines"], [2, 5])
        self.assertTrue(result["requires_manual_review"])

    def test_standalone_second_edital_still_abstains(self):
        right = [
            "EDITAL Nº 314/2026",
            "SUMULA: EXCLUI candidato da lista",
            "EXCLUI o candidato aprovado",
            "EDITAL Nº 315/2026",
            "CARGO: MOTORISTA",
            "3520         ANA PAULA SILVA",
        ]
        self.assertIsNone(infer_for(make_layout(right)))

    def test_does_not_borrow_exclusion_from_other_column(self):
        right = [
            "EDITAL Nº 314/2026", "LISTA DE CANDIDATOS", "SEM ALTERACOES",
            "CARGO: MOTORISTA", "3520         ANA PAULA SILVA",
        ]
        left = ["EDITAL Nº 101/2026", "SUMULA: EXCLUI", "EXCLUI candidato",
                "CARGO: MOTORISTA", "1234         NOME ESQUERDO"]
        self.assertIsNone(infer_for(make_layout(right, left)))

    def test_new_edital_invalidates_old_context(self):
        right = [
            "EDITAL Nº 314/2026", "SUMULA: EXCLUI", "EXCLUI candidato",
            "CARGO: MOTORISTA", "EDITAL Nº 315/2026", "LISTA INFORMATIVA",
            "CARGO: MOTORISTA", "3520         ANA PAULA SILVA",
        ]
        self.assertIsNone(infer_for(make_layout(right)))

    def test_missing_registration_abstains(self):
        right = [
            "EDITAL Nº 314/2026", "SUMULA: EXCLUI", "EXCLUI candidato",
            "CARGO: MOTORISTA", "ANA PAULA SILVA",
        ]
        self.assertIsNone(infer_for(make_layout(right)))

    def test_missing_cargo_abstains(self):
        right = ["EDITAL Nº 314/2026", "SUMULA: EXCLUI", "EXCLUI candidato",
                 "3520         ANA PAULA SILVA"]
        self.assertIsNone(infer_for(make_layout(right)))

    def test_weak_classification_words_alone_abstain(self):
        right = ["EDITAL Nº 314/2026", "Lista de aprovados", "Os aprovados",
                 "CARGO: MOTORISTA", "3520         ANA PAULA SILVA"]
        self.assertIsNone(infer_for(make_layout(right)))

    def test_conflicting_explicit_acts_abstain(self):
        right = [
            "EDITAL Nº 314/2026", "SUMULA: CONVOCA", "CONVOCA candidato",
            "NOMEIA candidato", "NOMEIA servidor", "CARGO: MOTORISTA",
            "3520         ANA PAULA SILVA",
        ]
        self.assertIsNone(infer_for(make_layout(right)))

    def test_far_heading_abstains(self):
        right = ["EDITAL Nº 314/2026", "SUMULA: EXCLUI", "EXCLUI candidato"]
        right += ["texto tecnico"] * 30
        right += ["CARGO: MOTORISTA", "3520         ANA PAULA SILVA"]
        self.assertIsNone(infer_for(make_layout(right)))

    def test_two_parallel_edital_blocks_stay_separate(self):
        right = ["EDITAL Nº 314/2026", "SUMULA: EXCLUI",
                 "EXCLUI da lista o candidato", "CARGO: MOTORISTA",
                 "3520         ANA PAULA SILVA"]
        left = ["EDITAL Nº 100/2026", "SUMULA: CONVOCA",
                "CONVOCA para documentos", "CARGO: TECNICO",
                "1234         JOAO LIMA ALVES"]
        layout = make_layout(right, left)
        self.assertEqual(infer_for(layout)["act_type"], "desistencia_exclusao")
        self.assertEqual(infer_for(layout, "JOAO LIMA ALVES")["act_type"], "convocacao")


if __name__ == "__main__":
    unittest.main()
