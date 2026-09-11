# ETAPA 6.3.5 — Correção de paginação da rastreabilidade

- Corrigido HTTP 422 em Leituras e Paletes quando `page_size=8`.
- Backend agora aceita paginação a partir de 8 registros por página.
- Melhorado tratamento de erros da API no frontend para não exibir `[object Object]`.
- Mantidas todas as funcionalidades e dados das versões 6.3.x anteriores.
