# Histórico de versões

## 0.5.2 — Proteção de conexões remotas

- Fixa um IP público validado pelo DNS ao abrir o socket TLS do PDF,
  evitando uma segunda resolução que permitiria DNS rebinding.
- Rejeita IP literal e conjuntos de respostas DNS que incluam redes
  privadas, reservadas ou locais.
- Mantém certificado TLS verificado para o domínio original e proíbe
  redirecionamentos automáticos.
- Inclui testes determinísticos de DNS privado, mistura de endereços
  e validação do destino efetivo da conexão.
- Mantém a classificação de atos inalterada. O parser PDF ainda exige
  cautela com documentos não confiáveis.

## 0.5.1 — Consulta de PDF público direto, sem API

- Inclui o botão **Analisar PDF por link (sem API)** na janela de
  consulta online como alternativa quando o Querido Diário não responde.
- Baixa somente o PDF informado pelo usuário, com consentimento,
  HTTPS obrigatório, sem redirecionamentos, até 25 MB e prazo limitado.
- Analisa temporariamente o PDF no computador e apresenta página,
  tipo de ato e indicador; preserva a revisão humana.
- Mostra erros diferenciados para 403, 404, redirecionamento,
  retorno que não é PDF e falhas de rede.
- Melhora a mensagem de erro da API para não atribuir automaticamente
  a falha à conexão de internet do usuário.
- Adiciona testes simulados sem rede e documentação de privacidade.

## 0.5.0 — Consulta online sob demanda (experimental)

- Adiciona **Consultar diarios online** em janela separada, com
  código IBGE obrigatório e confirmação expressa antes de transmitir
  o nome completo à API pública do Querido Diário.
- Mostra até dez edições com data, município, trecho e link HTTPS,
  sem inferir ato jurídico a partir de excertos remotos.
- Faz uma consulta por clique, com timeout, limite de resposta e
  rejeição de URLs de documentos não HTTPS.
- Mantém busca em PDFs/TXT totalmente local e não implementa
  monitoramento, notificações nem cadastro de nomes.
- Inclui testes mockados de requisição, respostas, validação e falhas
  de rede, além de documentação de privacidade e limites de cobertura.
- **A disponibilidade da API externa ainda exige validação manual.**

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
