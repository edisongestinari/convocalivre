# Demonstração reproduzível do ConvocaLivre (Windows)

Este roteiro foi preparado para avaliadores de código aberto. Ele não usa dados
pessoais reais nem faz consultas remotas.

## Pré-requisitos

- Windows com Python 3.10+ e Tkinter (presente na maioria das instalações).
- Acesso ao [repositório](https://github.com/edisongestinari/convocalivre).
- Nenhuma chave de API é necessária para a demonstração local.

## Rodar diretamente do repositório

~~~powershell
git clone https://github.com/edisongestinari/convocalivre.git
cd convocalivre
python -m pip install -e .
python -m unittest discover -s tests -v
python -m convocalivre examples/publicacao_ficticia.txt --name "MARIA DE SOUSA"
python -m convocalivre gui
~~~

Alternativa sem Git, instalando a versão principal:

~~~powershell
python -m pip install --upgrade "https://github.com/edisongestinari/convocalivre/archive/refs/heads/main.zip"
python -m convocalivre gui
~~~

Na janela, selecione `examples/publicacao_ficticia.txt` quando estiver usando
o repositório clonado e busque **MARIA DE SOUSA**. O arquivo é inteiramente
fictício. A interface deve mostrar a pesquisa em andamento e depois a ocorrência
localizada. **O rótulo do ato é uma hipótese**, não uma afirmação jurídica.

## Avaliação de PDFs reais

O projeto possui [protocolo](PUBLIC_PDF_AUDIT.md) e [relatórios]
(PUBLIC_PDF_AUDIT_RETEST_2026-11-17.md) de uma amostra exploratória.
Não confundir a amostra usada para desenvolver regras com teste
independente de desempenho. Links públicos podem expirar ou ficar indisponíveis.

Não publique capturas contendo nomes, CPFs ou outros identificadores reais;
se for demonstrar documentos públicos, oculte os campos pessoais.

## O que esta demonstração NÃO comprova

- Detecção de todas as publicações de um candidato.
- Cobertura de diários municipais em âmbito nacional.
- Confiabilidade universal, precisão estatística ou interpretação jurídica.
- Capacidade de extrair texto de PDFs escaneados por OCR.
- Disponibilidade da integração de API externa, ainda experimental.

O programa é um protótipo open source ativo e sujeito à revisão humana.
