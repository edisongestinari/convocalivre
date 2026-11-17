# Consulta online sob demanda — ConvocaLivre 0.5.0 (experimental)

A função **Consultar diários online** complementa, mas não substitui,
a consulta offline de PDFs/TXT do ConvocaLivre. Ela usa o endpoint público
de busca do projeto **Querido Diário**, mantido pela Open Knowledge Brasil.
Não há vínculo oficial, patrocínio ou afiliação do ConvocaLivre com esse
projeto. Documentação da API:
https://docs.queridodiario.ok.org.br/pt-br/latest/utilizando/api-publica.html

## Como usar na interface Windows

1. Abra normalmente o comando python -m convocalivre gui.
2. Informe um nome completo (no campo usado também pela pesquisa local).
3. Clique em **Consultar diarios online**.
4. Informe o **código IBGE de 7 dígitos do município**.
   Exemplo real: Cruzeiro do Oeste (PR) = **4106605**.
   Consulte outras cidades na tabela oficial do IBGE:
   https://www.ibge.gov.br/explica/codigos-dos-municipios.php
5. Clique em **Consultar agora**.
6. Antes de qualquer requisição, o programa solicitará **autorização
   explícita para transmitir o nome completo à API pública de terceiros**.
   Se responder Não, nenhum nome será enviado.
7. O programa mostra até dez edições retornadas, com data, município,
   número da edição, trecho (quando fornecido) e link HTTPS para
   publicação de origem. Use **Abrir publicação original** e confira o ato.

## Privacidade e consentimento

A pesquisa **local** em PDFs/TXT continua totalmente offline.
A pesquisa **online**, quando autorizada, envia o nome e o código
IBGE do município à API pública do Querido Diário. O provedor externo
pode registrar requisições conforme suas próprias políticas. O
ConvocaLivre não cria conta, salva cadastro, agenda pesquisa recorrente,
envia notificações ou envia automaticamente os seus PDFs à API.

Os resultados ficam apenas na janela durante esta consulta; não há
persistência automática de nomes pesquisados. O usuário deve considerar
a privacidade de pessoas pesquisadas antes de utilizar o serviço.

## Limitações técnicas e jurídicas

- **Uma requisição por clique** (máximo de dez edições), com prazo
  máximo de resposta e limite de tamanho; sem paginação e sem
  monitoramento contínuo.
- A API pode estar fora do ar, demorar ou rejeitar requisições. O programa
  informará erro de conexão; **não** interpretará isso como ausência do
  candidato em um diário.
- A cobertura do Querido Diário é parcial, variável por município e data.
  Não pressupor que o município solicitado esteja indexado, mesmo quando
  o código IBGE está correto.
- É uma busca lexical remota por expressão, não o classificador de atos
  do ConvocaLivre. **Não mostra confirmação de nomeação, convocação ou
  exclusão**: todos os resultados precisam ser confrontados com o PDF
  da fonte oficial. A API pode trazer trechos incompletos ou ruidosos.
- Se o link do documento não vier na resposta, a ferramenta informa
  que não há link; não fabrica URL.
- A interface nunca envia o nome sem confirmação. Um clique em
  **Consultar diários online** apenas abre a janela.
- Caso a API fique indisponível, ainda é possível consultar manualmente
  o site https://queridodiario.org.br/ e o diário oficial do município.

## Validação

Existem testes **totalmente simulados** para o formato da requisição,
normalização de trechos e URL, limites de resposta e casos de erro
HTTP/timeout. A autorização é verificada pelo fluxo de interface e
deverá ser confirmada em Windows real.

Esses testes não demonstram disponibilidade do servidor externo em
produção. Uma verificação manual com conexão à internet será necessária.
O ConvocaLivre continuará oferecendo as funções offline 0.4.1
mesmo que essa nova conexão não responda.
