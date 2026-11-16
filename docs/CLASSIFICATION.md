# Classificação conservadora de atos — versão 0.3.0

## Objetivo e limites

A ferramenta **não determina status jurídico**. Em cada correspondência exata do nome,
ela procura indicadores de atos na **mesma linha ou frase**. O relatório apresenta
uma hipótese explicável, sujeita a revisão humana. A origem e a autenticidade do
documento continuam sem verificação automática.

Categorias de act_type:

- convocacao: indicador de convocação de candidato;
- nomeacao: indicador de nomeação;
- desistencia_exclusao: desistência, exclusão, revogação ou tornar sem efeito;
- resultado_homologacao: resultado, classificação, homologação ou aprovação;
- indeterminado: não há indicador único suficiente no contexto delimitado.

no_name_match não é uma categoria de ato; sinaliza apenas que o nome buscado não
apareceu no texto extraído. A interpretação de "não encontrou" depende da qualidade
da extração; especialmente em PDF, não comprova ausência do nome no arquivo visual.

## Critérios

1. O nome precisa corresponder por inteiro, tolerando acentos e espaços.
2. O classificador busca indicadores na **mesma cláusula** onde apareceu o nome,
   delimitada por pontuação ou quebra de linha. Indicadores a mais de 120
   caracteres da ocorrência são ignorados.
3. Negações simples como "não foi nomeado" não geram ato positivo.
4. Termos de exclusão/desistência prevalecem sobre referências incidentais
   à nomeação ("exclusão por desistência da nomeação").
5. Convocação e nomeação na mesma cláusula, sem critério inequívoco de ligação
   a uma única pessoa, causam **abstenção** (indeterminado).
6. Na versão 0.3.1, para PDFs em modo layout_fallback, há uma inferência
   **conservadora** do cabeçalho numerado do edital para linhas de tabela,
   somente se número de inscrição, coluna, cargo e duas linhas independentes
   de evidência estiverem alinhados. Sem isso, o resultado segue
   indeterminado. Consulte [TABLE_CONTEXT.md](TABLE_CONTEXT.md).

O sistema pode errar com frases longas, colunas desalinhadas, texto OCR, negações
complexas, atos com várias pessoas, verbos raros ou termos fora da mesma frase.
"Indeterminado" é preferível a atribuir um ato juridicamente incorreto.

## Campos do JSON

Dentro de cada objeto matches:

- act_type: categoria indicativa;
- act_indicator: palavra/expressão normalizada que acionou a categoria, ou null;
- act_basis: same_clause_indicator, same_clause_exclusion_priority,
  conflicting_indicators ou no_unambiguous_indicator;
- requires_manual_review: sempre true.

O campo act_type_counts resume ocorrências por classe; **conta menções, não atos
jurídicos**. signal e matched_terms são campos heurísticos legados e podem
diferir de act_type, pois procuram palavras na janela ampla ao redor do nome.

## Benchmark sintético reproduzível

A partir da raiz do repositório, com o pacote instalado:

    python -m convocalivre.benchmark tests/fixtures/act_cases.json

Salvar relatório:

    python -m convocalivre.benchmark tests/fixtures/act_cases.json --output metricas.json

O arquivo de avaliação tem **39 exemplos inteiramente fictícios**, com rótulos
atribuídos manualmente. Contém atos claros, menções neutras, nomes ausentes,
negações e frases com atos distintos atribuídos a pessoas diferentes. Nenhum
dado privado ou documento real é incluído.

### Definições matemáticas

- Por categoria, **TP** = rótulo correto e previsto; **FP** = previsto como
  essa categoria, mas o rótulo correto é outro; **FN** = deveria ser essa
  categoria, mas a previsão é outra.
- precision = TP/(TP+FP) e recall = TP/(TP+FN); denominador zero produz
  null, não uma estimativa arbitrária.
- Detecção de ato: as quatro categorias específicas contam como "ato";
  indeterminado e no_name_match contam como "não classificado".
  A confusão é calculada separadamente. Erros de **tipo de ato** são exibidos.
- accuracy é a fração de rótulos exatamente corretos em todos os casos.

**ATENÇÃO:** os resultados medem apenas o conjunto sintético e **não demonstram
precisão em diários oficiais reais**. O conjunto contém exemplos usados no próprio
desenvolvimento, então nem mesmo substitui validação independente. Não mede
cobertura de nomes em PDFs complexos, qualidade do texto extraído, nem ambiguidades
jurídicas reais.

## Próximo ciclo necessário

- Construir corpus independente de documentos públicos com procedência, licença
  e proteção de dados, além de exemplos adversariais inéditos.
- Definir protocolo de anotação humana com duplo revisor, desempate e métricas
  estratificadas por layout, município, categoria e fonte.
- Medir separadamente *encontrar o nome* e *tipificar o ato*.
- Só então comunicar resultados de generalização, com intervalos de incerteza.
