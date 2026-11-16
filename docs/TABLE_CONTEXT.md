# Leitura conservadora de tabelas em PDFs — 0.3.1

## Problema

No modo de extração por layout do pypdf, publicações com duas colunas
podem ter linhas mescladas horizontalmente. Uma pessoa pode estar em
tabela do edital à direita, enquanto a esquerda contém outro ato.
Buscar palavras próximas ao nome sem reconstruir blocos pode atribuir
a esse candidato um ato praticado por outro órgão.

## Como funciona

A correção só tenta herdar contexto **em correspondências encontradas pelo
fallback de layout** e com act_type inicialmente indeterminado. Para emitir
uma classificação, todas as condições abaixo devem ser verdadeiras:

1. A linha do nome possui número de inscrição de 2–8 dígitos antes dele,
   separado por pelo menos dois espaços.
2. Há um cabeçalho de **EDITAL numerado** no alinhamento da coluna do
   número de inscrição e no máximo 28 linhas antes.
3. Existe marcador de **CARGO** na mesma coluna, perto da linha da pessoa.
4. Há **duas linhas distintas** com indicadores da mesma categoria de ato
   dentro desse bloco e pelo menos um indicador explícito.
5. Nenhum outro edital/documento numerado intercepta o bloco.
6. Categorias positivas conflitantes impedem a atribuição. Em desistência/
   exclusão, é possível aparecer menção incidental a uma nomeação
   anterior; as evidências de exclusão precisam ser independentes.

Quando alguma condição falha, a classificação permanece indeterminada.
O sistema não deve procurar títulos de todo o PDF nem misturar
as colunas à esquerda e à direita.

## Evidência e compatibilidade

O objeto de cada correspondência continua mostrando page_number,
extraction_mode, excerpt e os campos da versão 0.3. Somente quando
a associação da tabela é considerada possível, aparecem:

- act_basis = table_same_column_numbered_edital_two_indicators
- act_context_excerpt = até dois trechos que sustentam o contexto
- act_context_lines = linhas **do texto extraído**, começando em 1
- act_heading_excerpt = cabeçalho do edital numerado

table_context_pages reúne páginas com essa inferência. Mesmo nesses
casos, requires_manual_review permanece true, pois o programa
**não confirma o efeito jurídico nem a autenticidade da publicação**.

O campo legado result, com valores como name_mentioned_only, não é
reinterpretado pela classificação de tabelas: ele depende de palavras
dentro do trecho local e pode diferir de act_type. Analise act_type
e o suporte textual antes de tirar qualquer conclusão.

## O que fica fora da cobertura

- Tabelas sem número de inscrição, cabeçalhos sem número do edital,
  cargo não identificado, ato em outra página ou colunas com
  desalinhamento maior que o tolerado;
- atos em páginas escaneadas (não existe OCR), texto rotacionado ou PDF
  com ordem visual não reconstruída corretamente;
- casos de quadro/grupo que exijam compreensão do vínculo semântico
  da pessoa à ação de outro parágrafo;
- validação real de falsos positivos e falsos negativos em uma amostra
  independente e representativa.

Os testes adicionados são **inteiramente sintéticos**, com documentos
paralelos, mudança de edital, texto vago, alinhamento e ambiguidades.
O diagnóstico fornecido pelo usuário a partir da edição pública
de 05/11/2026 motivou a alteração, mas **não é, por si, um
reteste da versão 0.3.1**. Não divulgar métricas deste conjunto como
precisão em diários oficiais reais.
