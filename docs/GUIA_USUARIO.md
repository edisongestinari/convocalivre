# Guia de uso — ConvocaLivre 0.4.1 (MVP local)

O ConvocaLivre busca menções exatas a nomes completos em PDFs pesquisáveis
e arquivos TXT **no próprio computador**, sem enviar nomes, documentos ou
resultados a um servidor do ConvocaLivre.

**O que ele faz hoje:** abre PDF/TXT local, busca um nome, associa alguns
atos administrativos por critérios conservadores, informa a página física,
mostra a hipótese e permite guardar um relatório JSON no computador.

**O que ainda NÃO faz:** consultar automaticamente todos os diários oficiais,
monitorar sites, disparar alertas, reconhecer por OCR qualquer PDF escaneado,
provar que alguém foi nomeado ou interpretar definitivamente efeitos jurídicos.

## 1. Instalação no Windows

Requer **Python 3.10 ou superior**. No PowerShell:

~~~powershell
python -m pip install --upgrade "https://github.com/edisongestinari/convocalivre/archive/refs/heads/main.zip"
python -m pip show convocalivre
~~~

O segundo comando deve mostrar **Version: 0.4.1** depois da atualização.
Se aparecer aviso de que a pasta Scripts não está no PATH, use sempre
a forma **python -m convocalivre** — ela não depende do PATH.

## 2. Abrir a janela gráfica

~~~powershell
python -m convocalivre gui
~~~

1. Informe seu **nome completo** (ao menos duas partes).
2. Clique em **Adicionar PDFs/TXT** e escolha até 100 arquivos, ou em
   **Adicionar pasta** para varrer os documentos da pasta selecionada.
3. Clique em **Buscar nome**. Um aviso **Procurando...** com barra animada
   aparecerá imediatamente; para vários documentos, a janela informa qual
   arquivo está sendo pesquisado. A animação indica atividade, **não um
   percentual estimado**. A análise é local e pode demorar em PDFs extensos.
   O aviso desaparece ao terminar ou ocorrer uma falha.
4. Leia a tabela de ocorrências: nome do arquivo, página física,
   **hipótese** de ato e termo indicador.
5. Selecione uma ocorrência e clique em **Abrir PDF selecionado** para
   verificar a publicação original. O navegador pode ignorar o marcador
   #page; nesse caso, navegue manualmente à página exibida.
6. Se desejar, clique em **Salvar relatório JSON**. Esse arquivo pode
   conter nomes, trechos da publicação e caminhos do computador:
   **não compartilhe sem revisar**.

A janela requer o componente **Tkinter** do Python. Se não estiver
disponível, a ferramenta de linha de comando continua funcionando.

## 3. Buscar em uma pasta sem abrir a janela

~~~powershell
python -m convocalivre batch "$HOME\Downloads\Diarios" --name "MARIA DE SOUSA" --output "$HOME\resultado_lote.json"
~~~

Para incluir também as subpastas:

~~~powershell
python -m convocalivre batch "$HOME\Downloads\Diarios" --recursive --name "MARIA DE SOUSA" --output "$HOME\resultado_lote.json"
~~~

O limite padrão é de **100 documentos por lote**. Apenas arquivos .pdf
e .txt são pesquisados. Outros formatos são ignorados, assim como
links simbólicos. A saída informa erros por documento, sem interromper
toda a consulta quando apenas um arquivo apresenta falha.

## 4. Verificar a qualidade de um PDF

Se o nome não foi encontrado ou aparecerem avisos de extração:

~~~powershell
python -m convocalivre diagnose "$HOME\Downloads\diario.pdf" --output "$HOME\diagnostico_pdf.json"
~~~

O diagnóstico informa quantas páginas possuem texto extraível,
quantas não possuem e quais apresentaram falhas de extração.
**Não inclui nomes nem trechos do texto**, mas contém um hash dos
bytes do documento.

> Páginas sem texto extraível **não são automaticamente scans**: podem
> conter camadas mal codificadas ou recursos incompatíveis com pypdf.
> O ConvocaLivre ainda não tem OCR. Não trate uma busca sem resultado como
> prova de que o nome não existe no documento visual.

## 5. Buscar em um documento isolado (compatível com versões antigas)

~~~powershell
python -m convocalivre "$HOME\Downloads\diario.pdf" --name "MARIA DE SOUSA" --output "$HOME\resultado.json"
~~~

As categorias atuais são convocacao, nomeacao,
desistencia_exclusao, resultado_homologacao e indeterminado.
Elas são **indícios heurísticos**. Todos os resultados exigem revisão
humana do órgão, do ato, da data e do conteúdo jurídico no documento
original.

## 6. Limitações e segurança

- **Sem rede:** os comandos de consulta, lote, diagnóstico e GUI não
  acessam sites. A ferramenta experimental external_pdf_audit é
  separada, destinada a desenvolvimento, e baixa os links listados
  explicitamente no manifesto.
- **Sem alertas automáticos:** as consultas só executam quando iniciadas
  pelo usuário. O programa ainda não monitora novas publicações.
- **Sem rastreamento:** não existe serviço de cadastro de CPF/nome e
  não há telemetria no MVP local.
- **Cuidado com PDFs:** arquivos grandes ou malformados podem consumir
  recursos. Existem limites de tamanho, páginas e quantidade de arquivos.
- **Cuidado com relatórios:** arquivos JSON de resultados contêm dados
  pessoais. Guarde-os em pasta privada e não publique-os em GitHub.
- **Homonímia e legalidade:** correspondência por nome inteiro não
  individualiza uma pessoa de modo absoluto nem comprova convocação
  ou nomeação legal.

## 7. Próxima etapa para um serviço público online

Antes de oferecer alertas reais de publicações, serão necessários:
autorização/licença das fontes, coleta resiliente, deduplicação,
monitoramento com consentimento explícito, segurança, documentação
de privacidade e uma avaliação independente maior. O MVP local não
deve ser anunciado como sistema automático de acompanhamento de concursos.
