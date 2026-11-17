# Consultar um PDF público diretamente pelo link — 0.5.1

Esta alternativa foi acrescentada porque a API externa de busca de diários
do Querido Diário estava inacessível em testes de 17/11/2026. A falha
externa não é prova de problema com a internet do usuário.

## Procedimento no Windows

1. Abra a janela do ConvocaLivre e informe o nome completo.
2. Clique **Consultar diarios online (beta)**.
3. Clique **Analisar PDF por link (sem API)**, na parte inferior.
4. Copie o endereço HTTPS direto para um arquivo PDF público. Por exemplo,
   a edição utilizada para testes em Cruzeiro do Oeste:

   https://www.umuaramailustrado.com.br/edicoes/2026/novembro_2026/digital_05_11_2026.pdf

5. Clique **Baixar e analisar PDF**. O programa solicitará autorização
   para acessar o link; confirme se for o documento desejado.
6. Durante o download e a análise, uma barra animada mostra atividade.
7. A tabela exibe as páginas físicas onde o nome foi encontrado e, quando
   houver elementos suficientes, o tipo de ato INDICATIVO.
8. Clique **Abrir PDF original na página selecionada** e confira se
   o ato realmente se refere ao candidato. O navegador pode ignorar
   o marcador de página; nesse caso, avance manualmente.

## O que a alternativa faz e não faz

- Baixa **um PDF público informado**, com timeout de 20 segundos,
  até 25 MiB e extração limitada a 250 páginas.
- O documento é salvo apenas num diretório temporário para permitir
  análise pelo classificador local e removido em seguida.
- O nome não entra na URL enviada ao servidor e não faz parte de
  parâmetros de consulta. O site do arquivo pode registrar IP e
  metadados do acesso, conforme suas políticas.
- O endereço deve usar HTTPS, host público e porta padrão; URLs
  privadas, credenciais e redirecionamentos são rejeitados.
- Não faz busca por nome em dezenas de diários; não verifica outros
  documentos; não implementa cadastro, monitoramento ou alertas.
- A fonte pode retornar HTML, bloquear downloads, redirecionar ou
  ficar inacessível; o programa informa a falha sem afirmar que o nome
  está ausente.
- Quando o PDF não possui texto extraível, a busca pode falhar mesmo
  que o nome esteja visível em uma imagem. Não existe OCR nesta função.
- Atribuições de convocação, nomeação, exclusão e homologação continuam
  sendo hipóteses sujeitas à revisão humana.

## Privacidade e riscos

Nenhum nome é enviado como parâmetro de pesquisa ao site que hospeda
o PDF. O download em si é uma conexão externa consentida. O conteúdo
do documento é processado localmente, e o programa não o publica ou
envia a um servidor do ConvocaLivre. Não compartilhe relatórios que
contenham nomes, documentos de identificação ou outras informações.

O endereço da publicação é informado pelo usuário e **não é validado
como fonte oficial** pelo ConvocaLivre; confira a autenticidade no site
responsável antes de atribuir consequências jurídicas.

## Validação

Existem testes offline mockados de HTTPS e endereços privados, erro de
rede, 403/404, redirecionamento, conteúdo não PDF, limite de tamanho,
extração e classificação local. A leitura do PDF real no Windows do
usuário ainda requer teste de aceitação.

API de terceiros e consulta de PDF por URL são métodos distintos; a
falha da API não impede a análise do PDF obtido diretamente de outro
servidor.
