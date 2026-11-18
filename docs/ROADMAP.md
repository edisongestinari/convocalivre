# Roadmap verificável

## Concluído até o protótipo 0.3.0
- [x] Núcleo de busca determinística offline em TXT UTF-8
- [x] Normalização de acentuação, correspondência de nome inteiro e trechos de contexto
- [x] Hash SHA-256 do texto analisado e saída JSON
- [x] Testes unitários e CI no GitHub Actions
- [x] Classificação heurística conservadora de convocação, nomeação, exclusão/desistência e resultado/homologação
- [x] Inferência conservadora de atos em linhas de tabela com cabeçalho de edital na mesma coluna, com casos sintéticos adversariais
- [x] Retestar associação de tabela nas versões 0.3.2 e 0.3.3 com o PDF real de Cruzeiro do Oeste
- [x] Corpus rotulado com 39 exemplos sintéticos e relatório reprodutível de FP/FN por classe

## MVP local — versão 0.4.0
- [x] Interface gráfica de uso local para Windows/Python (Tkinter)
- [x] Consulta em lote de até 100 PDFs/TXT e tratamento por arquivo
- [x] Diagnóstico sanitizado da qualidade da camada textual de cada PDF
- [x] Códigos de erro sanitizados para fontes públicas na auditoria
- [x] Guia em português para instalação, pesquisa e interpretação cautelosa
- [x] Validar abertura, pesquisa local, indicador de atividade e PDF em Windows real de usuário
- [ ] Resolver nomes não recuperados do PDF de Sabáudia, sem publicar informações pessoais
- [ ] Implantar busca em fontes oficiais e alertas opcionais com consentimento e limites de acesso

## Consulta remota experimental — versão 0.5.0
- [x] Adicionar pesquisa sob demanda via API pública de terceiros
- [x] Solicitar consentimento explícito antes de transmitir o nome
- [x] Exigir código IBGE e limitar consultas/quantidade de resultados
- [x] Separar possíveis menções online da classificação local de atos
- [x] Tratar a falha real da API como indisponibilidade externa e melhorar o aviso
- [x] Criar consulta manual de um único PDF público por URL HTTPS, sem API
- [ ] Validar leitura direta de PDF por link no Windows do usuário
- [ ] Confirmar funcionamento real da API no Windows do usuário
- [ ] Avaliar outras fontes, intervalos de datas, cobertura e deduplicação
- [ ] Criar monitoramento periódico apenas com consentimento e controles

## Instalador Windows — versão 0.6.1
- [x] Gerar workflow PyInstaller + Inno Setup, permissões de usuário e SHA-256
- [x] Acrescentar smoke test sem interface e instruções de download
- [ ] Confirmar execução bem-sucedida do build Windows e artefato no GitHub
- [ ] Testar instalação, abertura, busca e desinstalação em Windows real
- [ ] Assinatura de código antes de distribuição pública ampla

## Antes de buscar usuários
- [ ] Fazer avaliação independente com publicações públicas e casos inéditos, sem expor dados privados
- [x] Medir FP/FN em exemplos sintéticos de desenvolvimento, documentando limitações
- [x] Criar auditoria exploratória reprodutível em múltiplas fontes públicas, sem nomes em claro no repositório
- [x] Corrigir falsos negativos conhecidos em convocação, homologação e portaria que atravessa página, com regressões e reteste exploratório 0.3.3
- [ ] Medir FP/FN em conjunto independente de documentos reais e layouts variados (amostra externa de desenvolvimento não substitui revisão independente)
- [x] Adicionar análise offline de PDFs com texto extraível, páginas numeradas e SHA-256 dos bytes originais
- [x] Criar testes sintéticos para PDF, páginas vazias e compatibilidade com TXT
- [ ] Rever segurança, privacidade e licenças de todas as fontes
- [ ] Adicionar guia acessível para usuários sem experiência técnica

## Integrações e manutenção pública (não implementadas)
- [x] Criar cliente básico sob demanda para API Querido Diário, com requisição limitada
- [ ] Melhorar resiliência, cobertura e fontes autorizadas após validação real
- [ ] Conciliação de publicações repetidas com identificadores oficiais
- [ ] Alertas opcionais configurados pelo próprio usuário sem expor nomes em logs
- [ ] Localização PT-BR / EN e documentação de integração
- [ ] Releases, CHANGELOG, triagem de issues e registros de incidentes
- [ ] Colaboradores externos, pilotos públicos e métricas de adoção verificáveis

## Para uma candidatura crível ao Codex for Open Source
- [ ] Demonstrar utilidade pública com relatórios reais e consentidos
- [ ] Apresentar atividade contínua de manutenção e releases
- [ ] Apresentar usuários, contribuições externas e/ou adoção verificável
- [ ] Descrever casos específicos para revisão de PR, testes e releases com Codex
- [ ] Informar exclusivamente números reais; jamais declarar popularidade inexistente
