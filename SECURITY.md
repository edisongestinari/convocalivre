# Política de segurança — ConvocaLivre (pré-alfa)

O ConvocaLivre processa PDFs e nomes encontrados em documentos públicos.
Arquivos externos podem ser malformados, conter dados pessoais ou apresentar
conteúdo diferente do esperado. **Não é um serviço oficial de convocação.**

## Operação e superfícies de risco

- Busca local em PDFs e TXT: processamento no computador do usuário, sem
  envio automático do nome ou do arquivo para outro serviço.
- Pesquisa pelo Querido Diário (beta): **requer consentimento explícito** para
  transmitir o nome completo e o código do município à API de terceiros;
  a integração não tem disponibilidade garantida.
- Consulta por PDF público via URL: faz uma requisição HTTPS ao site da
  publicação, com autorização do usuário. Não insere o nome como parâmetro
  de pesquisa, mas o site pode registrar IP e outros metadados.
- Relatórios JSON podem conter nomes e trechos identificáveis. Não os
  publique indiscriminadamente nem os envie para issues públicas.

## Limites de segurança

A biblioteca usa limites de páginas, tamanho dos documentos, tempo de
download e verificações de links e tipos de arquivo. Esses mecanismos
**não garantem isolamento contra arquivos maliciosos**, ataques de
negação de serviço, redirecionamentos inesperados ou extração de dados
sensíveis por componentes externos. Não execute com privilégios de
administrador e use apenas fontes que você confie.

Na versão 0.5.2, a consulta direta de PDF bloqueia endereços IP literais,
verifica os endereços resolvidos pelo DNS e **fixa o IP público escolhido
na conexão TLS**, mantendo SNI e validação de certificado para o domínio
original. Redirecionamentos são bloqueados. Isso reduz riscos de acesso
a redes internas e DNS rebinding, mas **não garante segurança total**:
o parser de PDFs ainda processa documentos não confiáveis. Não execute
o aplicativo com privilégios elevados nem em servidores expostos.

## Como reportar

Não divulgue exploits, tokens, CPFs, documentos não públicos ou falhas
exploráveis em issues ou pull requests públicos. Se o GitHub mostrar a
opção **Report a vulnerability** na aba Security deste repositório,
prefira esse canal privado. Se não estiver disponível, solicite um canal
privado ao mantenedor por meio do perfil do projeto, sem publicar
detalhes exploráveis. Não há prazo formal de resposta ou suporte
profissional garantido nesta fase.

Para problemas comuns sem dados sensíveis, utilize issues com um exemplo
totalmente fictício. As correções devem incluir testes de regressão.
