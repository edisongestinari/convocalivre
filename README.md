# ConvocaLivre 0.6.0 — MVP local + consulta online experimental

**Software cívico open source para pesquisar nomes em diários oficiais brasileiros e apresentar evidências de possíveis atos administrativos — sem confundir menção com nomeação confirmada.**

**Projeto em pré-alfa:** [impacto e evidências](docs/IMPACTO_E_EVIDENCIAS.md) · [demonstração reproduzível](docs/DEMONSTRACAO.md) · [roteiro de candidatura Codex for Open Source](docs/CANDIDATURA_CODEX_FOR_OSS.md) · [limitações](docs/ROADMAP.md)

> ⚠️ Protótipo inicial. Consultas locais continuam offline; a nova consulta à API do Querido Diário é opcional, realizada somente após consentimento e depende da disponibilidade do serviço. NÃO monitora sites automaticamente, NÃO envia alertas, NÃO comprova nomeação, nem substitui verificação humana. O arquivo de exemplo é inteiramente fictício. PDFs digitalizados sem texto ainda não são reconhecidos.

## Interface gráfica e pesquisa local (MVP)

A versão 0.4.0 permite ao usuário comum consultar uma pasta de PDFs e
TXT sem escrever código. **A busca por arquivos continua local; há uma pesquisa online opcional
em uma API pública, mas não existe serviço de alertas automáticos.**

### Abrir a interface no Windows

Em Windows, com Python 3.10 ou superior:

~~~powershell
python -m pip install --upgrade "https://github.com/edisongestinari/convocalivre/archive/refs/heads/main.zip"
python -m convocalivre gui
~~~

Para uma demonstração reproduzível com documentos fictícios, consulte
[DEMONSTRACAO.md](docs/DEMONSTRACAO.md).

Na janela, escolha o nome completo e os PDFs/TXT, clique em
**Buscar nome**. Enquanto a ferramenta pesquisa, a mensagem **Procurando...**
e uma barra animada indicam atividade; o arquivo corrente é exibido.
Ao concluir, veja as hipóteses na tabela e abra o PDF original
na página indicada. É possível exportar o resultado para JSON local.

### Buscar em uma pasta pelo PowerShell

~~~powershell
python -m convocalivre batch "$HOME\Downloads\Diarios" --name "MARIA DE SOUSA" --output "$HOME\resultado_lote.json"
~~~

### Diagnosticar PDFs não pesquisáveis

~~~powershell
python -m convocalivre diagnose "$HOME\Downloads\diario.pdf" --output "$HOME\diagnostico.json"
~~~

O diagnóstico contém estatísticas de extração, **não nomes nem trechos**.
Uma página sem texto extraível não prova que o PDF seja um scan.
Os relatórios de busca, por outro lado, podem conter dados pessoais:
não os publique indiscriminadamente.

[Guia de instalação e utilização no Windows](docs/GUIA_USUARIO.md).

## Alternativa quando a API não responde (0.5.1)

A API de busca do Querido Diário apresentou indisponibilidade de rede e
TLS em 17/11/2026. **Isso não significa que sua internet ou o programa
de busca local estejam com defeito.**

Na janela **Consultar diarios online (beta)**, use
**Analisar PDF por link (sem API)**. Cole o endereço HTTPS direto de uma
edição oficial, autorize o download temporário, e o ConvocaLivre
executará a busca e classificação no próprio computador.

Por exemplo, uma edição já utilizada em regressões do projeto:
https://www.umuaramailustrado.com.br/edicoes/2026/novembro_2026/digital_05_11_2026.pdf

Essa alternativa **não descobre automaticamente novos PDFs**, não
transmite o nome como parâmetro de pesquisa e não envia alertas;
ela somente consulta o arquivo informado. O servidor de origem pode
registrar o endereço IP de quem fizer o download. Links que redirecionam
ou respostas que não são PDFs são recusados por segurança.

Veja [o passo a passo](docs/PDF_POR_LINK.md).

## Nova consulta de diários online sob demanda (0.5.0, experimental)

Na janela, clique em **Consultar diarios online**, informe o código IBGE
do município e confirme a autorização. Somente então o programa envia
o nome completo à **API pública do Querido Diário** e apresenta até dez
possíveis menções, com trecho e link para a publicação original.

A função é **separada da busca local**; não salva cadastros nem monitora
publicações. A API de terceiros pode estar indisponível, e sua cobertura
não é completa. Encontrar um trecho não equivale à confirmação jurídica
de convocação ou nomeação. O serviço remoto pode registrar acessos,
conforme as próprias políticas.

O código IBGE de Cruzeiro do Oeste/PR é **4106605**. Para outros
municípios, consulte os códigos oficiais do IBGE. [Guia e aviso de
privacidade](docs/CONSULTA_ONLINE.md).

## Reproduza em minutos

Sem PDF real e sem enviar informações pessoais:

~~~powershell
git clone https://github.com/edisongestinari/convocalivre.git
cd convocalivre
python -m pip install -e .
python -m unittest discover -s tests -v
python -m convocalivre examples/publicacao_ficticia.txt --name "MARIA DE SOUSA"
~~~

A suíte usa amostras **fictícias**. O conjunto de PDFs públicos usado na
pesquisa é limitado e **não fornece uma estimativa de precisão**.
Leia [os resultados e limitações](docs/PUBLIC_PDF_AUDIT_RETEST_2026-11-17.md).

## Problema público

Pessoas aprovadas em concursos podem depender de publicações espalhadas por diferentes diários oficiais. Uma busca por palavra-chave pode gerar falsos positivos ou perder variações de acentuação. Queremos criar uma biblioteca reusável com proveniência, verificabilidade e proteção dos dados pessoais.

## Diferencial proposto

- Pesquisa exata por nome completo, tolerante a acentos e variação de espaços, em TXT UTF-8 ou PDF com texto pesquisável.
- Distinção entre **nome mencionado** e **possível ato relacionado**; nenhuma conclusão jurídica automática.
- Trecho de evidência, posições no documento e hash SHA-256 do texto analisado.
- Pesquisa **local e offline** em documentos já baixados; a **opção online beta**
  é separada e, quando autorizada, pode transmitir o nome à API de terceiros.
  O modo PDF por URL faz download do arquivo e executa a busca localmente.
- Saída JSON para integração futura com outras ferramentas cívicas. Em PDFs, retorna página física (iniciando em 1), trecho, posições no texto extraído, hash dos bytes originais e aviso para páginas sem texto.

## Instalação (Python 3.10+)

```bash
python -m pip install -e .
python -m convocalivre examples/publicacao_ficticia.txt --name "Maria de Sousa" --source-url "https://example.invalid/publicacao-ficticia" --date 2026-11-12
```

ou, depois da instalação:

```bash
convocalivre examples/publicacao_ficticia.txt --name "Maria de Sousa" --output resultado.json
```

O URL do exemplo é deliberadamente inválido, para não aparentar uma publicação real.

## PDF com texto pesquisável (0.2.1)

Após instalar, analise um arquivo PDF local:

    convocalivre meu_diario.pdf --name "Maria de Sousa" --source-url "https://example.invalid/diario.pdf" --date 2026-11-16 --output resultado.json

Quando a extração padrão não encontra o nome em uma página, o ConvocaLivre tenta reconstruir o texto pelo layout. O JSON informa o campo `extraction_mode` (`plain` ou `layout_fallback`) e `layout_fallback_pages`. A reconstrução por layout pode omitir texto rotacionado, juntar colunas ou gerar falsos positivos; verificações de espaçamento reduzem, mas não eliminam, esse risco. Sempre confira a página visualmente.

A URL e a data são fornecidas pelo usuário e **não são verificadas**. A página indicada é a posição física da página no PDF, não necessariamente a página impressa no rodapé do diário. PDF digitalizado sem camada de texto não é pesquisado; **não há OCR**. A associação entre nome e palavra próxima é um indício heurístico, nunca a confirmação de nomeação. O hash prova identidade dos bytes do arquivo, não autenticidade. Detalhes: [docs/PDF.md](docs/PDF.md).

## Novo: classificação experimental de atos (0.3)

Cada nome localizado recebe um campo act_type com uma destas hipóteses:
**convocacao**, **nomeacao**, **desistencia_exclusao**,
**resultado_homologacao** ou **indeterminado**.

Em TXT, o classificador usa indicadores na mesma frase/linha do nome. Em PDF
(0.3.1), pode associar uma linha de tabela ao **edital numerado na mesma
coluna**, se encontrar o cabeçalho, o cargo e duas evidências independentes.
Ausência desse vínculo mantém a classe indeterminada. Trata negações simples,
prioriza exclusões explícitas e se abstém quando há indicadores conflitantes.
Todas as ocorrências exigem revisão humana. Ele **não certifica atos jurídicos**
nem prova que a publicação é oficial. Campos antigos signal e matched_terms
continuam presentes e podem divergir da categoria mais conservadora.

O relatório inclui act_indicator, act_basis, requires_manual_review e
act_type_counts (contagem de menções, não de atos). No modo layout_fallback,
a nova vinculação opcional de tabela registra evidências de coluna e
cabeçalho (veja [docs/TABLE_CONTEXT.md](docs/TABLE_CONTEXT.md)). As páginas do PDF e os
avisos de extração continuam disponíveis.

**Benchmark com documentos de teste sintéticos:** na pasta do repositório,
rode o comando abaixo. O resultado apresenta matriz de confusão, falsos
positivos e falsos negativos por categoria, além de exemplos com divergência.

    python -m convocalivre.benchmark tests/fixtures/act_cases.json

**As métricas são exclusivas dos 39 casos fictícios de desenvolvimento.
Não representam precisão em documentos reais.** Consulte os critérios em [docs/CLASSIFICATION.md](docs/CLASSIFICATION.md)
e as métricas observadas em [docs/BENCHMARK_RESULTS.md](docs/BENCHMARK_RESULTS.md).

## Auditoria exploratória em publicações oficiais

Há um avaliador separado para documentos externos de **dez arquivos de oito municípios** e **19 ocorrências de referência**, com treze verificações negativas (cruzadas e por página). A seleção é manual e não aleatória. Os nomes não aparecem em claro no repositório nem nos relatórios; hashes são apenas pseudonimização, não anonimização.

O comando abaixo baixa os documentos publicamente acessíveis apenas durante a execução e produz contagens agregadas de TP/FP/FN por tipo, além de distinguir falhas de conexão de nomes não encontrados:

    python -m convocalivre.external_pdf_audit tests/fixtures/public_pdf_cases.json --output auditoria_publica.json

**Não compare os números com os 39 casos sintéticos como se fossem estimativas populacionais.** Consulte [o protocolo, as fontes e os limites](docs/PUBLIC_PDF_AUDIT.md).

A [primeira auditoria executada em fontes reais](docs/PUBLIC_PDF_AUDIT_RESULTS_2026-11-16.md) registrou 5/10 PDFs acessíveis, 7/19 casos de referência avaliados e 4 falsos negativos de classificação de ato; leia a análise de viés e limitações antes de interpretar os números.

## Contexto estruturado adicional em PDFs (0.3.3)

Quando a correspondência do nome não possui um verbo diretamente associado,
o modo de PDF pode utilizar **três estruturas estritamente reconhecidas**:
convocação com comando explícito e cabeçalho de candidatos na mesma página;
anexo de resultado final com classificação, inscrição e pontuação; e uma
portaria de nomeação interrompida no fim de uma página que continua com
destinatário inequívoco no início da página seguinte. Na ausência dos
marcadores, retorna `indeterminado`.

A evidência traz `act_basis` e linhas contextuais; nenhuma inferência
confirma nomeação ou substitui conferência da publicação original.
Veja [docs/STRUCTURED_CONTEXT.md](docs/STRUCTURED_CONTEXT.md).

## Testes

```bash
python -m unittest discover -s tests -v
```

## Segurança e privacidade

Não publique resultados que contenham nomes reais, nem cadastros, tokens, diários sensíveis ou dados privados. O resultado JSON pode incluir nome e trechos identificáveis: use-o localmente. Não faça scraping agressivo. Todo aviso é apenas um **indício**, e o documento oficial sempre deve ser consultado.

## Próximos passos

O [reteste exploratório de 0.3.3](docs/PUBLIC_PDF_AUDIT_RETEST_2026-11-17.md) mostra 8/8 classificações corretas **apenas nos casos efetivamente avaliados** (8/19 do manifesto). Os exemplos motivaram as regras; esse resultado não mede a acurácia real do produto. 

Veja [docs/ROADMAP.md](docs/ROADMAP.md). Já existe uma integração **experimental e sob demanda** com a API pública [Querido Diário](https://docs.queridodiario.ok.org.br/pt-br/latest/utilizando/api-publica.html), mas ela esteve indisponível nos testes de conexão. Ainda faltam validação independente, estabilidade de fontes e avaliação com usuários externos. O projeto pode solicitar apoio à manutenção open source nesta fase, sem alegar maturidade, escala ou adoção que ainda não foram demonstradas.

## Contribuições

Veja [CONTRIBUTING.md](CONTRIBUTING.md). Projetos semelhantes existem: não pretendemos reivindicar pioneirismo nem afiliação à Open Knowledge Brasil, Querido Diário ou órgãos governamentais.

## Licença

MIT — [LICENSE](LICENSE).
