# Reteste exploratório de classificação — versão 0.3.3

**Data:** 17/11/2026.  
**Código:** ConvocaLivre 0.3.3, PR #11.  
**Auditoria executada:** [GitHub Actions #44129203232](https://github.com/edisongestinari/convocalivre/actions/runs/44129203232), com artifact público de curta retenção contendo apenas IDs e contagens.  
**Teste unitário:** [GitHub Actions #44129203097](https://github.com/edisongestinari/convocalivre/actions/runs/44129203097), Python 3.10/3.12.

## O que foi corrigido

A auditoria exploratória de 0.3.2 encontrou quatro casos em que o nome foi
localizado, mas o ato ficou indevidamente indeterminado. A implementação
agora reconhece **formas muito específicas e verificáveis** de:

- convocação de candidato em tabela de edital;
- homologação com candidatos em anexo de classificação (duas disposições
  diferentes de nome/inscrição);
- portaria de nomeação iniciada em uma página, com destinatário identificado
  no começo da seguinte.

Os quatro casos anteriormente classificados como indeterminados passaram
a receber a categoria de referência. A edição de Joinville/SC, que se
tornou acessível na rodada seguinte e contém uma terceira disposição de
tabela, também foi reconhecida após um ajuste específico.

## Resultado efetivamente observado

| Métrica | Resultado 0.3.3 |
| --- | ---: |
| PDFs de referência no manifesto | 10 |
| PDFs acessíveis na execução | **6/10** |
| Casos positivos e neutros anotados | 19 |
| Casos completamente avaliados | **8/19** |
| Alvos não recuperados na extração | 2 |
| Casos com falha do localizador | 1 |
| Classificações exatas corretas | **8/8** |
| Classificações exatas incorretas | **0/8** |
| Localização de nome: TP / FN | **8 / 0**, condicionado à recuperação prévia do nome |
| Controles negativos de ausência: TN / FP | **8 / 0**, de sondagens não aleatórias |

Os seis atos positivos avaliados foram: **uma convocação, duas nomeações,
três homologações/resultados**. Os dois outros casos foram controles
neutros: licença funcional e exoneração, corretamente mantidos como
indeterminados. **Nenhum caso de desistência/exclusão foi processado
nessa rodada:** o PDF de Cruzeiro do Oeste permaneceu indisponível no
ambiente de auditoria, embora o documento tenha sido testado localmente
pelo usuário na versão 0.3.2.

Quatro PDFs não estavam disponíveis no momento: Arapoti/PR,
Pinhalzinho/SP, Itaí/SP e Cruzeiro do Oeste/PR. Dois alvos em
Sabáudia/PR continuaram irresolúveis pela camada de texto.
Os casos ausentes ou com falha de extração **não foram contados como
acertos nem como verdadeiros negativos**.

### Comparação com 0.3.2

No subconjunto de **sete mesmos casos completamente avaliados** nas
duas versões, os acertos de classificação passaram de **3/7 para 7/7**.
O oitavo caso, de Joinville, não havia sido avaliado no baseline por
indisponibilidade da fonte; foi incluído no reteste 0.3.3 e acertou.

| Caso rotulado | 0.3.2 | 0.3.3 |
| --- | --- | --- |
| FERNAO-CONVOCACAO-14 | indeterminado | convocacao |
| FERNAO-HOMOLOG-COZINHEIRO | indeterminado | resultado_homologacao |
| FERNAO-HOMOLOG-FISCAL | indeterminado | resultado_homologacao |
| CAJAMAR-NOMEACAO-PAGINA-SEGUINTE | indeterminado | nomeacao |
| JOINVILLE-HOMOLOGACAO-TABELA | não avaliado | resultado_homologacao |

Os três casos já classificados corretamente em 0.3.2 permaneceram
corretos em 0.3.3. As oito sondagens negativas avaliadas não produziram
ocorrências espúrias de nome.

## Interpretação obrigatória

**8/8 NÃO é estimativa da acurácia do produto no Brasil.**
Os exemplos foram selecionados por conveniência, motivaram diretamente
as mudanças de código e incluem somente casos cujos nomes o próprio
avaliador já conseguiu reconstruir do PDF. O denominador é muito
pequeno e não é independente, aleatório nem cego. Não estima cobertura
de extração, precisão fora desses layouts, risco jurídico nem qualidade
em PDFs digitalizados sem OCR.

A inferência foi mantida estrita; é preferível retornar
\`indeterminado\` em layouts não reconhecidos a informar nomeação
ou convocação sem sustentação. Esses rótulos continuam sendo hipóteses
para revisão humana, não confirmação oficial.

## Próximo trabalho

- Resolver a [issue #10](https://github.com/edisongestinari/convocalivre/issues/10):
  diagnosticar PDFs inacessíveis e nomes não recuperados sem atribuir
  erro jurídico ou acerto de busca a falha de origem/extração.
- Construir corpus independente, anotado por pelo menos duas pessoas,
  com amostragem por município, tipo de ato, fonte e layout.
- Medir falsos positivos **de classificação** com casos adversariais
  que apresentem múltiplos atos e pessoas, além das oito sondagens
  de ausência de nome já observadas.
- Manter regressões da edição multicoluna de Cruzeiro do Oeste, validada
  localmente em 0.3.2; retestar em 0.3.3 quando o PDF puder ser
  obtido por fonte independente ou fornecido novamente.
