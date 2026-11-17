# Roadmap verificável

## Concluído até o protótipo 0.3.0
- [x] Núcleo de busca determinística offline em TXT UTF-8
- [x] Normalização de acentuação, correspondência de nome inteiro e trechos de contexto
- [x] Hash SHA-256 do texto analisado e saída JSON
- [x] Testes unitários e CI no GitHub Actions
- [x] Classificação heurística conservadora de convocação, nomeação, exclusão/desistência e resultado/homologação
- [x] Inferência conservadora de atos em linhas de tabela com cabeçalho de edital na mesma coluna, com casos sintéticos adversariais
- [ ] Retestar inferência de tabela 0.3.1 na publicação pública que motivou o diagnóstico
- [x] Corpus rotulado com 39 exemplos sintéticos e relatório reprodutível de FP/FN por classe

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
- [ ] Criar cliente resiliente para fontes oficiais autorizadas e API Querido Diário (respeitando referências de volume e termos)
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
