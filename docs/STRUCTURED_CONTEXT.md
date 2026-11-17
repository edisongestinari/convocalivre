# Reconstrução conservadora de contexto em PDFs — 0.3.3

A versão 0.3.3 complementa as regras de 0.3.2. **Não realiza
interpretação jurídica** e nunca dispensa a leitura do documento original.

## Motivo

A auditoria externa da versão 0.3.2 classificou como indeterminados quatro
atos cujos nomes estavam legíveis. Os formatos envolvidos foram:

- **Fernão/SP:** convocação com nome somente na linha da tabela.
- **Fernão/SP:** anexo de homologação do resultado final, com candidatos,
  posição, inscrição e nota, enquanto o ato principal está na primeira página.
- **Cajamar/SP:** uma portaria de nomeação cujo texto continua na primeira
  linha útil da página seguinte.

O relatório anterior está em
[PUBLIC_PDF_AUDIT_RESULTS_2026-11-16.md](PUBLIC_PDF_AUDIT_RESULTS_2026-11-16.md).
Esses documentos deram origem aos requisitos, então são **casos de
desenvolvimento**, não teste independente e cego.

## Regras estritas

### 1. Convocação com tabela na mesma página

A inferência exige (a) **EDITAL DE CONVOCAÇÃO numerado**, (b) comando
explícito "CONVOCAR o candidato abaixo relacionado", (c) cabeçalho
"NOME DO CANDIDATO ... CARGO" e (d) nome dentro de quatro linhas após
esse cabeçalho. Uma nova portaria ou edital entre o cabeçalho e a linha
do candidato bloqueia a inferência.

A menção a *desistência em caso de não comparecimento* não é tratada
automaticamente como exclusão efetiva.

### 2. Homologação / classificação em anexo

Exige **ANEXO I**, **RESULTADO FINAL ... PROCESSO SELETIVO**, cabeçalho
de tabela com POS., INSCRIÇÃO, NOME e NOTA FINAL e linha iniciada por
posição e número de inscrição. Sem esses indicadores não se presume
homologação ou convocação; "aprovado" por si só não é suficiente.

### 3. Portaria continuada na página seguinte

Exige cumulativamente: uma portaria numerada no fim da página anterior,
com "Fica nomeada" e final de texto ainda aberto; nome precedido
por expressão inequívoca "a senhora"/"o senhor" etc. na **primeira linha
útil** da página seguinte, depois do cabeçalho do diário; e confirmação
"A nomeação ao cargo" na sequência, antes de outra portaria.

Nomes em outro ato, depois de portaria nova, ou no meio da página
não recebem essa classificação.

## Campos

Quando a rotina reconhece um desses formatos:
- act_type: categoria indicativa;
- act_basis: motivo estrutural, por exemplo
  \`adjacent_page_unfinished_portaria_named_recipient\`;
- act_indicator: palavra do comando;
- act_context_lines: linhas usadas como apoio;
- act_heading_excerpt: cabeçalho, sem trecho contendo dados pessoais;
- requires_manual_review: sempre true;
- structured_context_pages: páginas do PDF que receberam a inferência.

O sinal legado \`result\` poderá continuar \`name_mentioned_only\`,
pois seu cálculo independente não foi alterado.

**Limitações:** nomes que não apareçam na camada de texto extraível,
PDFs com tabelas ou colunas atípicas, cabeçalhos diferentes, quebra
de página envolvendo atos sem destinatário explícito, anexos sem
inscrição/nota, documentos com vários atos sobrepostos e conflitos
jurídicos podem ficar \`indeterminado\`. Essa abstenção é intencional.

## Verificação

Testes sintéticos contendo casos positivos e adversariais:

    python -m unittest discover -s tests -v

Auditoria de fontes externas (depende de acesso público aos PDFs):

    python -m convocalivre.external_pdf_audit tests/fixtures/public_pdf_cases.json --output audit.json

Nenhum nome de candidato real é incorporado aos testes. Os resultados
de auditoria devem indicar cobertura e casos indisponíveis antes de
qualquer conclusão; comparar desempenho nos documentos que inspiraram
as regras **não estima acurácia de produção**.
