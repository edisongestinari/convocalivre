# ConvocaLivre: impacto público e evidências verificáveis

**Situação em 17/11/2026:** versão 0.5.1, protótipo open source, não serviço de monitoramento automático.

## O problema

Pessoas aprovadas em concursos públicos brasileiros precisam acompanhar publicações
dispersas entre diários municipais, jornais e PDFs com diferentes formatos.
Um nome encontrado em uma página **não** significa que a pessoa foi nomeada:
pode ser lista de classificação, convocação, desistência, exclusão ou outra menção.
Uma interpretação errada pode causar falsas expectativas ou perda de prazo.

## A proposta

O ConvocaLivre é uma ferramenta em Python licenciada sob MIT que combina:

- Busca de nomes completos em TXT e PDFs com texto extraível, tolerante a acentos;
- Evidências vinculadas à página, trecho e indicador, com classificação
  deliberadamente conservadora e revisão humana obrigatória;
- Interface gráfica Tkinter validada no Windows e busca local de arquivos em lote;
- Diagnóstico de extração de PDF sem publicar nomes no relatório;
- Download pontual de um PDF público a partir de URL HTTPS autorizada;
- Integração *beta* com serviço de indexação externo, atualmente não validada
  em produção por indisponibilidade do endpoint.

A busca em documentos locais **não envia nomes ou PDFs a terceiros**.
A pesquisa por API externa é separada e exige confirmação para transmitir o nome.
O download por URL não transmite o nome como parâmetro, mas o provedor do PDF pode
registrar a conexão.

## Evidência de trabalho existente

| Item | Onde verificar |
|---|---|
| Código público e licença MIT | [Repositório](https://github.com/edisongestinari/convocalivre) |
| Instalação e uso local em Windows | [Guia](GUIA_USUARIO.md) |
| Protocolo de avaliação externa | [Auditoria](PUBLIC_PDF_AUDIT.md) |
| Resultado inicial e falhas encontradas | [Auditoria 16/11](PUBLIC_PDF_AUDIT_RESULTS_2026-11-16.md) |
| Reteste das correções | [Auditoria 17/11](PUBLIC_PDF_AUDIT_RETEST_2026-11-17.md) |
| Limitações e etapas abertas | [Roadmap](ROADMAP.md) |
| Testes automáticos | [GitHub Actions](https://github.com/edisongestinari/convocalivre/actions) |
| Como colaborar | [CONTRIBUTING](../CONTRIBUTING.md) |

O conjunto exploratório inicial contém 10 PDFs de 8 municípios e 19 casos
anotados. Na execução de 0.3.3, **somente 6 PDFs ficaram acessíveis e 8 casos
foram efetivamente avaliados**: 8 classificações coincidiram com o rótulo de
referência, mas esses exemplos **foram usados no desenvolvimento**. Portanto,
**não representam taxa de precisão em produção**, nem evidência independente
de adoção. Outros 11 casos não entraram na contagem.

Uma pessoa testou diretamente o fluxo de busca gráfica em Windows com um
documento real de Cruzeiro do Oeste, incluindo a barra de andamento e a
abertura do PDF na página encontrada. Essa validação de aceitação não equivale
a uma pesquisa de usuários externos ou uma implantação pública.

## O que ainda falta

1. Testes independentes e anotação cega de documentos novos para medir erros
   de classificação, falsos positivos e falhas de extração.
2. Resolver PDFs parcialmente ilegíveis e verificar OCR de forma segura.
3. Validar fontes online estáveis; a API do Querido Diário apresentou falhas
   de conexão, e o download direto não substitui descoberta automática.
4. Avaliar privacidade, ameaças de downloads remotos, manutenção de releases e
   suporte a outros usuários antes de oferecer um serviço público.
5. Se implementado, o monitoramento automático deverá ser opt-in, respeitar
   limites dos provedores e permitir cancelamento.

## Por que a manutenção open source pode importar

O valor esperado é oferecer um **componente cívico reutilizável e auditável**,
com evidências e abstenção explícita, para que cidadãos, pesquisadores e outras
ferramentas públicas possam verificar resultados — evitando depender de
classificações opacas ou de uma única fonte de diários oficiais.

Esse é um **objetivo**, não uma alegação de adoção já alcançada.
Não há vínculo oficial com a OpenAI, a Open Knowledge Brasil, o Querido Diário
nem administrações públicas.

## Como apoio de desenvolvimento seria usado

Tempo e ferramentas de manutenção seriam direcionados à revisão de PRs,
triagem de issues, geração de testes *sintéticos*, verificações de segurança,
regressões reprodutíveis e documentação. **Não enviaríamos nomes, CPFs nem
PDFs que contenham dados pessoais a APIs de modelos sem base legal, controles
adequados e revisão específica.** Classificações administrativas continuariam
sendo avaliadas e revisadas por humanos.
