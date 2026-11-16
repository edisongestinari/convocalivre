# ConvocaLivre (protótipo 0.3.0)

**Uma ferramenta aberta para encontrar indícios verificáveis de convocações e outros atos relacionados a nomes em textos e PDFs pesquisáveis de diários oficiais brasileiros.**

> ⚠️ Protótipo inicial. NÃO consulta automaticamente sites oficiais, NÃO envia alertas, NÃO comprova nomeação, nem substitui verificação humana. O arquivo de exemplo é inteiramente fictício. PDFs digitalizados sem texto ainda não são reconhecidos.

## Problema público

Pessoas aprovadas em concursos podem depender de publicações espalhadas por diferentes diários oficiais. Uma busca por palavra-chave pode gerar falsos positivos ou perder variações de acentuação. Queremos criar uma biblioteca reusável com proveniência, verificabilidade e proteção dos dados pessoais.

## Diferencial proposto

- Pesquisa exata por nome completo, tolerante a acentos e variação de espaços, em TXT UTF-8 ou PDF com texto pesquisável.
- Distinção entre **nome mencionado** e **possível ato relacionado**; nenhuma conclusão jurídica automática.
- Trecho de evidência, posições no documento e hash SHA-256 do texto analisado.
- Análise **offline**: nomes não são transmitidos a serviços externos.
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

O classificador exige indicador na mesma frase/linha, trata negações simples,
prioriza exclusões explícitas e se abstém quando há indicadores conflitantes.
Todas as ocorrências exigem revisão humana. Ele **não certifica atos jurídicos**
nem prova que a publicação é oficial. Campos antigos signal e matched_terms
continuam presentes e podem divergir da categoria mais conservadora.

O relatório inclui act_indicator, act_basis, requires_manual_review e
act_type_counts (contagem de menções, não de atos). As páginas do PDF e os
avisos de extração continuam disponíveis.

**Benchmark com documentos de teste sintéticos:** na pasta do repositório,
rode o comando abaixo. O resultado apresenta matriz de confusão, falsos
positivos e falsos negativos por categoria, além de exemplos com divergência.

    python -m convocalivre.benchmark tests/fixtures/act_cases.json

**As métricas são exclusivas dos 39 casos fictícios de desenvolvimento.
Não representam precisão em documentos reais.** Consulte os critérios e
limitações em [docs/CLASSIFICATION.md](docs/CLASSIFICATION.md).

## Testes

```bash
python -m unittest discover -s tests -v
```

## Segurança e privacidade

Não publique resultados que contenham nomes reais, nem cadastros, tokens, diários sensíveis ou dados privados. O resultado JSON pode incluir nome e trechos identificáveis: use-o localmente. Não faça scraping agressivo. Todo aviso é apenas um **indício**, e o documento oficial sempre deve ser consultado.

## Próximos passos

Veja [docs/ROADMAP.md](docs/ROADMAP.md). A intenção é estudar uma integração **respeitosa** com a API pública [Querido Diário](https://docs.queridodiario.ok.org.br/pt-br/latest/utilizando/api-publica.html), testar precisão em documentos consentidos e atender usuários reais antes de solicitar bolsas de manutenção.

## Contribuições

Veja [CONTRIBUTING.md](CONTRIBUTING.md). Projetos semelhantes existem: não pretendemos reivindicar pioneirismo nem afiliação à Open Knowledge Brasil, Querido Diário ou órgãos governamentais.

## Licença

MIT — [LICENSE](LICENSE).
