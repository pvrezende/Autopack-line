# ETAPA 6.20 — Fechamento e validação do núcleo funcional

Esta etapa fecha o ciclo funcional da Etapa 6 com uma nova aba em **Indicadores → Validação do núcleo**.

A tela executa um checklist somente leitura para confirmar, antes das integrações físicas, que o backend e o MySQL estão acessíveis e que a combinação de linha/produto possui os parâmetros operacionais necessários: linha e produto ativos, meta de produção, quantidade por palete e limites dos indicadores.

A validação respeita a prioridade já usada no sistema: configurações específicas do produto têm precedência e, quando aplicável, a configuração geral da linha é aceita como fallback. Nenhum valor operacional foi fixado no código e nenhuma migration/tabela nova foi criada.

## Teste
1. Suba o projeto com `docker compose down` e `docker compose up --build -d`.
2. Acesse **Indicadores → Validação do núcleo**.
3. Selecione `L01 - Linha 1` e `HJFE12C2CG`.
4. Clique em **Executar validação**.
5. Confirme os estados de Backend, Banco, Linha, Produto, Meta, Quantidade por palete e Limites.
6. Se todos estiverem OK, a tela deve informar **Núcleo funcional pronto para avançar**.
