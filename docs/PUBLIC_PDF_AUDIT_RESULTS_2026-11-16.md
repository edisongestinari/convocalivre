# Resultado da auditoria exploratória — 16/11/2026

**Versão analisada:** ConvocaLivre 0.3.2, sem alterações no classificador nesta pesquisa.  
**Fonte do resultado:** [GitHub Actions — execução 44001901990](https://github.com/edisongestinari/convocalivre/actions/runs/44001901990).  
**Relatório reproduzível:** artifact `public-pdf-audit-summary`, arquivo `public_pdf_audit_result.json` (retenção limitada pelo GitHub Actions).  
**Protocolo:** [PUBLIC_PDF_AUDIT.md](PUBLIC_PDF_AUDIT.md).

## Cobertura da amostra

| Etapa | Resultado observado |
| --- | ---: |
| Arquivos PDF de referência selecionados | 10 |
| Municípios representados no plano | 8 |
| PDFs efetivamente baixados e analisáveis | **5 / 10** |
| Municípios com PDFs baixados | **3**: Cajamar/SP, Fernão/SP, Sabáudia/PR |
| Ocorrências positivas/controle anotadas | 19 |
| Casos de referência plenamente avaliados | **7 / 19** |
| Alvos com nome não recuperado do PDF | 2 (Sabáudia) |
| Casos de fonte não disponível | 9 |
| Caso com erro do localizador de nome | 1 (Cajamar, controle de licença) |
| Controles negativos cadastrados | 13 |
| Controles negativos efetivamente avaliados | **6 / 13** |

As cinco fontes indisponíveis nesta execução foram Arapoti/PR (URLError),
Joinville/SC (TimeoutError), Pinhalzinho/SP (ValueError), Itaí/SP (ValueError)
e a edição de Cruzeiro do Oeste/PR (URLError). `ValueError` significa
que a fonte foi rejeitada pelo avaliador, por exemplo por retorno não PDF
ou limite excedido; **não autoriza inferir que o conteúdo publicado é inválido**.
O exemplo de Cruzeiro do Oeste foi validado anteriormente em PDF baixado
pelo usuário, mas **não foi processado nesta auditoria remota**.

Arquivos baixados (SHA-256 dos bytes realmente analisados):

| Edição / município | Páginas | SHA-256 do PDF |
| --- | ---: | --- |
| Sabáudia/PR, 12/11/2026 | 14 | `294c40913ac4d63a898448d88469cbcea14afbf7ccd7e2d140d0d44cae401d40` |
| Cajamar/SP, 16/06/2026 | 12 | `7a145319278a4ad53e889acdb04fc5c07ee72a8656d4e665e095b4def51bf64d` |
| Fernão/SP, convocação 14/2026 | 1 | `746a9220830e2a577f0fafba765d25af10015543c5654ad3d8e72201d4334cad` |
| Fernão/SP, homologação | 4 | `4340cffd7716a38fad8d682bceedcb1af265ac44032634cfbb798e66faa64992` |
| Cajamar/SP, 19/06/2026 | 10 | `f51f991f63ba47ab5174a4f1349bd3803397c7e79f29cefc6e1b5a4a09583664` |

## Localização de nomes — avaliação condicional

**Somente entre os casos cujo nome foi recuperado previamente do texto do PDF
pelo localizador do benchmark:**

| Resultado | Contagem |
| --- | ---: |
| Verdadeiros positivos (TP) | 7 |
| Falsos negativos (FN) | 0 |
| Falsos positivos (FP), em sondagens negativas | 0 |
| Verdadeiros negativos (TN), em sondagens negativas | 6 |

Essas contagens **não provam que o ConvocaLivre encontra todos os nomes dos PDFs**.
O próprio benchmark precisa localizar previamente cada nome pela camada
de texto, usando um hash. Se essa etapa falhar, o caso fica inconclusivo e
não compõe os cálculos. Os controles negativos são selecionados
por conveniência entre fontes/páginas distintas, não por sorteio aleatório.

## Classificação do tipo de ato — avaliação condicional

**Casos plenamente avaliados: 7. Acertos: 3. Divergências: 4.**

| Tipo anotado | Acertos | Falsos negativos |
| --- | ---: | ---: |
| Convocação | 0 | 1 |
| Nomeação | 1 | 1 |
| Desistência/exclusão | 0 | 0 (nenhum caso processado) |
| Resultado/homologação | 0 | 2 |
| Indeterminado / outro ato (controles) | 2 | 0 |

As quatro divergências foram **abstenções indevidas**: o sistema achou
o nome, mas respondeu `indeterminado` para um ato com categoria de referência.
**Não houve classificação positiva incorreta observada nos sete casos**,
o que não permite concluir ausência de falsos positivos no uso geral.

| ID do caso | Referência esperada | Previsão |
| --- | --- | --- |
| `FERNAO-CONVOCACAO-14` | convocacao | indeterminado |
| `FERNAO-HOMOLOG-COZINHEIRO` | resultado_homologacao | indeterminado |
| `FERNAO-HOMOLOG-FISCAL` | resultado_homologacao | indeterminado |
| `CAJAMAR-NOMEACAO-PAGINA-SEGUINTE` | nomeacao | indeterminado |

Dois casos corretamente rotulados como indeterminados eram um
ato de licença funcional e um de exoneração, categorias ainda não
tratadas pelo classificador. Um terceiro caso de licença funcional
de Cajamar não pôde ser avaliado por erro do localizador de nome.

## Diagnóstico e ações rastreáveis

- [Issue #9 — Falsos negativos em tabelas, homologação e atos que cruzam páginas](https://github.com/edisongestinari/convocalivre/issues/9).
- [Issue #10 — Nomes não recuperados e erros de disponibilidade/extração](https://github.com/edisongestinari/convocalivre/issues/10).

**Prioridade técnica:** primeiro aumentar a cobertura de documentos e
investigar a extração; depois corrigir associação de editais a tabelas
sem número de inscrição, homologações e atos que cruzam páginas.
Preservar a abstenção onde a associação não for inequívoca.

## Validade e divulgação

Esta é uma **avaliação exploratória de conveniência**, com apenas sete
casos plenamente avaliados provenientes de dois municípios (Cajamar e
Fernão). Os demais PDFs não foram acessados ou não produziram um alvo
recuperável para a avaliação. As referências foram triadas manualmente,
mas não receberam dupla anotação independente e cega.

**Não apresentar 3/7 como estimativa de taxa real de erro no produto, nem
usar 7/7 como taxa de detecção universal.** A auditoria não cobre OCR,
qualidade jurídica de decisões, autenticidade de atos ou requisitos de
privacidade para implantação em produção. Registros de nomes em SHA-256
são pseudonimizados, não anonimizados.

Este relatório descreve um resultado efetivamente executado, não uma
promessa de desempenho futuro. Comando para reproduzir a auditoria:

```bash
python -m convocalivre.external_pdf_audit tests/fixtures/public_pdf_cases.json --output public_pdf_audit_result.json
```
