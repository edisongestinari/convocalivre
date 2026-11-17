# Auditoria exploratória com PDFs reais de municípios — novembro de 2026

## Objetivo e princípio de evidência

Complementar o benchmark de 39 frases **sintéticas** com um conjunto
externo de publicações oficiais selecionadas por um revisor humano.
O objetivo é identificar falhas reais de extração de nomes e de
classificação de atos, sem supor que os resultados se generalizam.

Este é um corpus **intencional, pequeno e não aleatório**. Os documentos não
são copiados para o repositório; os links apontam para os publicadores
originais (ou para a edição de jornal usada em validação anterior).
Não há nomes de candidatos em claro no código, no manifesto nem nos logs
da auditoria; o manifesto conserva hashes SHA-256 dos nomes normalizados.
**Hash não significa anonimização**: trata-se de pseudonimização, sujeita
a risco de reidentificação. Não publique arquivos PDF ou relatórios
individuais com CPF, data de nascimento ou outros dados pessoais.

## Fontes e rótulos anotados

A relação foi construída por verificação das publicações em 16/11/2026.
A coluna página é a **página física do PDF**, iniciando em 1.

| Município | Fonte | Página(s) | Tipo de avaliação |
| --- | --- | --- | --- |
| Arapoti/PR | [Diário oficial 2176, 13/11/2026](https://diario.arapoti.pr.gov.br/uploads/diario_oficial/62493/X27aXt2wF2PM_D_Ay9EnAHj1Xz6QQ1Ee.pdf) | 4 | Convocação para exame admissional, tabela |
| Sabáudia/PR | [Diário oficial 3008, 12/11/2026](https://www.sabaudia.pr.gov.br/public/admin/globalarq/diario-oficial/3dee14ef9356bea2a8daf127717c436d.pdf) | 1, 2 | Nomeação em tabela e controle negativo de licença-maternidade |
| Joinville/SC | [Anexo de homologação e classificação](https://www.joinville.sc.gov.br/public/portaladm/pdf/jornal/9e87f8599a57c01f318d3228f80cffa4.pdf) | 1 | Resultado final em tabela de notas |
| Cajamar/SP | [Diário oficial 1694, 16/06/2026](https://cajamar.sp.gov.br/diariooficial/wp-content/uploads/sites/3/edicao-no-1694-2.pdf) | 2, 3 | Nomeação por portaria e controle negativo de licença-prêmio |
| Pinhalzinho/SP | [Diário oficial 1449, 06/11/2026](https://www.pinhalzinho.sp.gov.br/public/admin/globalarq/diario-eletronico/diario/a3xsTARAcwZ2A232.pdf) | 3 | Nomeação por portaria em tabela |
| Itaí/SP | [Diário oficial 1548, 13/11/2026](https://www.itai.sp.gov.br/public/admin/globalarq/diario-eletronico/diario/32Tx22AwRc3aAsZA.pdf) | 3 | Cinco nomeações próximas, na mesma página |
| Cruzeiro do Oeste/PR | [Jornal de 05/11/2026](https://www.umuaramailustrado.com.br/edicoes/2026/novembro_2026/digital_05_11_2026.pdf) | 13 | Exclusão/desistência em duas colunas — caso de regressão já usado no desenvolvimento |

**Composição:** 7 fontes, 13 ocorrências positivas (que incluem
dois casos de "indeterminado" porque licenças não fazem parte das quatro
categorias), além de 4 sondagens negativas cruzadas entre documentos.

O caso de Cruzeiro do Oeste é um **caso de desenvolvimento já conhecido**,
portanto não é independente e deve ser destacado ao interpretar os totais.
Os demais foram selecionados externamente, mas não tiveram dupla
anotação humana cega. Os rótulos são de triagem e não pareceres jurídicos.

## Como executar

Na raiz do repositório, com Python 3.10+ e o pacote instalado:

    python -m convocalivre.external_pdf_audit tests/fixtures/public_pdf_cases.json --output auditoria_publica.json

O comando tenta baixar **uma vez** cada PDF por HTTPS, com tempo e tamanho
limitados, somente para processamento local temporário. Não usa OCR.
Pode ocorrer bloqueio por site, expiração de link ou falha de rede.
Nenhuma fonte indisponível vira automaticamente verdadeiro negativo.

Há também uma execução automática **apenas na PR que altera o código da
auditoria ou o manifesto**, com resultados agregados em artifact de curta
retenção. A auditoria não é monitoramento contínuo dos sites.

## Como interpretar

**Detecção do nome**, avaliada separadamente:

- TP: nome publicado no documento e localizado na página de referência;
- FN: nome recuperado do PDF para a avaliação, mas o ConvocaLivre
  não o encontrou na página esperada;
- TN: nome recuperado de uma fonte e corretamente ausente de outra
  publicação independente (sondagem cruzada);
- FP: nome dessa sondagem aparece indevidamente na publicação cruzada.

**Classificação do ato:** matriz de confusão das quatro categorias
(convocacao, nomeacao, desistencia_exclusao, resultado_homologacao),
indeterminado e no_name_match, com TP/FP/FN por classe. A classe
indeterminado também cobre **atos administrativos não contemplados pelo
protótipo**, como concessão de licença funcional.

### Limitações críticas

1. O identificador de cada candidato é um hash do nome normalizado.
   Para testá-lo, o programa **precisa reconstruir o nome do próprio PDF**;
   se isso falhar, o caso é "target_unresolved" e **não entra nas métricas**.
   Isso gera viés de seleção e impede interpretar o resultado como
   sensibilidade total de extração.
2. A amostra é pequena e selecionada por conveniência. Alguns documentos
   têm vários nomes no mesmo trecho, sem anotação cega dupla.
3. Pode existir divergência entre a leitura visual do PDF e o texto
   reconstruído pelo pypdf. O relatório conserva o hash do PDF
   efetivamente baixado para comparação de versões.
4. Publicações indisponíveis, bloqueios por site, divergência de paginação
   ou falhas de conexão são **inconclusivas**, nunca TN.
5. Por questões de privacidade, a saída omite nomes e trechos pessoais;
   porém, hashes ligados a fontes oficiais ainda podem ser dados pessoais
   pseudonimizados. Não usar o conjunto para identificar ou rastrear pessoas.
6. O classificador não certifica autenticidade, nomeação ou status jurídico.

### Critério para declarar a avaliação concluída

Só comunicar métricas de casos com status **evaluated** e informar
explicitamente o número de fontes disponíveis, casos não resolvidos
e negativos realmente processados. Se nenhum documento puder ser
baixado, a avaliação é *inconclusiva*, não 100% correta.

Este teste é **exploratório**, não uma alegação de desempenho em produção.
