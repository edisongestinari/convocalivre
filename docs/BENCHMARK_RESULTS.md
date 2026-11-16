# Resultado reprodutível do benchmark sintético — ConvocaLivre 0.3.0

Execução registrada no GitHub Actions (Python 3.12):
https://github.com/edisongestinari/convocalivre/actions/runs/43976482591

Comando executado na raiz:

    python -m convocalivre.benchmark tests/fixtures/act_cases.json

## Métricas observadas

| Métrica | Valor |
| --- | ---: |
| Casos sintéticos rotulados | 39 |
| Classificações exatas corretas | 37 |
| Classificações incorretas | 2 |
| Acurácia de rótulos | 94,87% |
| Detecção binária de ato: TP | 24 |
| Detecção binária de ato: FP | 0 |
| Detecção binária de ato: FN | 2 |
| Detecção binária de ato: TN | 13 |
| Precisão binária de ato | 100% |
| Sensibilidade/recall binário de ato | 92,31% |
| Tipo de ato incorreto entre atos detectados | 0 |

A definição de "ato" binário inclui as quatro categorias específicas; "indeterminado"
e "no_name_match" não contam como evento detectado. Isso é apenas uma convenção
de mensuração, não um parecer jurídico.

## Por categoria

| Rótulo esperado | TP | FP | FN | Precisão | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| convocacao | 6 | 0 | 1 | 100% | 85,71% |
| nomeacao | 6 | 0 | 1 | 100% | 85,71% |
| desistencia_exclusao | 6 | 0 | 0 | 100% | 100% |
| resultado_homologacao | 6 | 0 | 0 | 100% | 100% |
| indeterminado | 8 | 2 | 0 | 80% | 100% |
| no_name_match | 5 | 0 | 0 | 100% | 100% |

## Dois erros mantidos no conjunto

- H01: esperado "convocacao"; predito "indeterminado" quando a frase atribui
  convocação a uma pessoa e nomeação a outra na mesma cláusula.
- H02: esperado "nomeacao"; predito "indeterminado" na situação inversa.

Esses erros foram **incluídos** no resultado; não foram descartados, corrigidos
na rotulagem ou apresentados como acertos. O algoritmo deliberadamente se abstém
se uma cláusula combina categorias potencialmente conflitantes.

## O que NÃO foi medido

1. Desempenho geral em diários oficiais reais (nenhuma amostra independente).
2. Qualidade da extração visual/textual de PDFs, OCR ou falhas de tabela/colunas.
3. Falsos negativos de nomes não extraídos de documentos originais.
4. Efeito jurídico dos atos, autenticidade e atualidade da fonte.
5. Variações de redação e normas de diferentes municípios.

**O conjunto foi desenvolvido junto às próprias regras e utiliza frases artificiais
simplificadas. Os indicadores podem estar fortemente superestimados e NÃO devem
ser usados como promessa de desempenho, nem como argumento de adoção comprovada.**

Próximo estudo recomendado: amostra independente anotada por pelo menos duas
pessoas, avaliação cega, estratificação por tipo de ato/fonte/layout, e análise
conjunta do pipeline PDF + localização do nome + classificação do ato.

Os números devem ser recalculados quando o código ou o corpus mudarem.
