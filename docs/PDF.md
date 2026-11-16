# Análise de PDF — ConvocaLivre 0.2.1

## Escopo

O ConvocaLivre examina arquivos PDF locais com texto já incorporado, página por página, utilizando pypdf. Não baixa documentos, não executa OCR e não analisa imagens.

## Referências e evidências

Para cada ocorrência, o JSON registra:

- page_number: página física do PDF (começando em 1);
- excerpt: trecho textual extraído que inclui o nome;
- offset_start / offset_end: posições no TEXTO EXTRAÍDO da página, não coordenadas visuais;
- matched_terms: palavras relacionadas na janela próxima ao nome;
- signal: possible_related_act ou name_mentioned_only;
- extraction_mode: `plain` (extração padrão) ou `layout_fallback` (reconstrução por layout).

A partir da 0.2.1, se a extração padrão não localizar o nome completo em uma página, a aplicação tenta o modo layout. Candidatos cujo nome recuperado cruza linhas, tabulações ou oito ou mais espaços consecutivos são descartados para reduzir junções entre colunas. Esse critério conservador pode perder nomes legítimos e não elimina todas as ocorrências falsas. O relatório inclui `layout_fallback_pages` e avisos correspondentes. O modo layout pode ignorar texto rotacionado. A validação visual da página continua necessária.

O relatório fornece também document_sha256 dos bytes originais, total de páginas, páginas sem texto e avisos. Hash não comprova autenticidade ou nomeação.

## Como usar

    python -m pip install -e .
    convocalivre caminho/diario.pdf --name "Maria de Sousa" --output resultado.json

As opções --source-url e --date são metadados opcionais fornecidos pelo usuário; não são verificados. A opção --output salva o resultado JSON localmente.

## Limitações relevantes

1. Nome mencionado não é convocação. Palavra relevante perto do nome também não comprova que o ato diz respeito a essa pessoa.
2. Tabelas, colunas e quebras incomuns podem alterar a ordem do texto extraído e gerar falsos positivos ou negativos.
3. Páginas digitalizadas sem camada de texto são indicadas, mas OCR não é realizado.
4. Arquivos protegidos por senha não são suportados.
5. Há limites de tamanho, páginas e conteúdo por página; isso não impede todos os PDFs maliciosos. Analise arquivos não confiáveis em ambiente isolado.
6. A URL informada não prova que o PDF corresponde ao diário oficial. Sempre confira a publicação na fonte.

## Testes e próximos passos

A suíte inclui PDFs sintéticos para página exata, trecho, SHA-256, prevenção de associação entre páginas, páginas em branco, arquivos inválidos, limite de tamanho e compatibilidade TXT. Depois será necessário avaliar documentos reais cuja utilização seja permitida, medir precisão e documentar erros sem expor dados pessoais.

Biblioteca: https://pypdf.readthedocs.io/en/stable/user/extract-text.html
