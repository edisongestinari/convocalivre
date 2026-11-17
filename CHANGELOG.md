# Histórico de versões

## 0.4.1 — Indicador de pesquisa na interface

- Mostra **Procurando...** e uma barra animada assim que a pesquisa começa.
- Atualiza o texto de atividade ao iniciar/concluir cada PDF/TXT, sem
  inventar porcentagem para a leitura de páginas.
- Mantém a janela responsiva por execução em thread, sem manipular widgets
  fora da thread principal.
- Desabilita entrada de nome, seleção e execução repetida durante a busca;
  restaura os controles ao terminar ou ocorrer erro.
- O classificador e o conteúdo dos relatórios permanecem inalterados.


## 0.4.0 — MVP local com interface (em validação)

- **Interface gráfica opcional** usando Tkinter, sem envio de documentos
  ou nomes a servidores; seleção de PDFs/TXT, busca, tabela por página,
  abertura do arquivo original e exportação local de JSON.
- **Busca em lote** de até 100 documentos de uma pasta, com tratamento
  independente de falhas e opção de subpastas.
- **Diagnóstico de texto extraível** em PDFs, com contagem por página,
  hash do documento e sem revelar nomes, CPF ou trechos.
- **Auditoria de fontes externas** com motivos sanitizados para
  erros HTTP, DNS, TLS, tempo limite, retorno não PDF, tamanho excedido,
  além de indicadores de texto disponível em alvos não recuperados.
- Testes unitários adicionais, preservando os comandos existentes.

Limites: a ferramenta **não monitora** sites oficiais, não envia alertas,
não tem OCR e não confirma atos jurídicos. O classificador de atos
permanece conservador, com revisão humana obrigatória.

## 0.3.3 — Reconhecimento conservador de estruturas

- Regras restritas para convocação em tabela, homologação em anexos de
  classificação e portaria de nomeação continuada na página seguinte.
- Auditoria exploratória em documentos públicos e testes adversariais.

## 0.3.2 — Cabeçalho ativo versus referência histórica

- Não trata menções a editais anteriores como abertura de novo ato.
- Preserva a associação correta de exclusão em tabela multicoluna.

## 0.3.1 — Associação de edital e tabela

- Inferência restrita de tabela por coluna, cargo e duas evidências.

## 0.3.0 — Classificação de atos

- Categorias indicativas, justificativa de evidência e benchmark sintético.

## 0.2.1 — Recuperação pelo layout

- Alternativa de extração de texto de PDFs quando a ordem do texto
  simples não encontra o nome em uma página.

As métricas de desenvolvimento não são estimativas de desempenho real.
