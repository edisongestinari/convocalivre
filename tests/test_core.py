import unittest
from convocalivre.core import analyze, normalize_with_mapping


class GazetteAnalysisTests(unittest.TestCase):
    def test_accent_insensitive_full_name_and_keyword(self):
        text = "PORTARIA: Fica convocado JOÃO SILVA PEREIRA para apresentar documentação."
        data = analyze(text, "Joao Silva Pereira")
        self.assertEqual(data["result"], "possible_related_act")
        self.assertEqual(data["match_count"], 1)
        self.assertEqual(data["matches"][0]["excerpt"], text)

    def test_different_person_not_matched(self):
        data = analyze("Nomeado Joao Silva Pereirinha.", "João Silva Pereira")
        self.assertEqual(data["result"], "no_name_match")

    def test_context_without_related_term(self):
        data = analyze("Lista informativa: Ana Paula Silva.", "Ana Paula Silva")
        self.assertEqual(data["result"], "name_mentioned_only")

    def test_name_with_whitespace_variation(self):
        data = analyze("Edital: MARIA   DE\nSOUSA convocada", "Maria de Sousa")
        self.assertEqual(data["result"], "possible_related_act")

    def test_no_bare_name(self):
        with self.assertRaises(ValueError):
            analyze("João", "João")

    def test_index_mapping(self):
        norm, positions = normalize_with_mapping("Órgão")
        self.assertEqual(norm, "orgao")
        self.assertEqual(positions, [0, 1, 2, 3, 4])

    def test_repeat_with_no_name(self):
        data = analyze("Convocacao geral dos inscritos.", "João da Silva")
        self.assertEqual(data["match_count"], 0)

    def test_sha256_is_deterministic(self):
        a = analyze("João da Silva aparece.", "Joao da Silva")
        b = analyze("João da Silva aparece.", "Joao da Silva")
        self.assertEqual(a["document_sha256"], b["document_sha256"])


if __name__ == "__main__":
    unittest.main()
