# ETAPA 6.17 — Central de alertas operacionais

A área **Indicadores** passa a possuir uma terceira aba: **Alertas operacionais**.

A central usa os limites configuráveis da etapa 6.16 e os indicadores calculados no MySQL para:

- separar indicadores em OK, ATENÇÃO, CRÍTICO e SEM DADOS;
- priorizar automaticamente os indicadores fora da meta;
- mostrar os limites de Atenção e Crítico aplicados;
- indicar se a origem dos limites é específica do produto ou geral da linha;
- apresentar recomendações de investigação sem alterar automaticamente metas ou parâmetros;
- exibir contexto operacional do dia: leituras, ocorrências, unidades paletizadas e paradas não planejadas.

Nenhum limite foi fixado no código. Nenhuma nova tabela ou migration é necessária nesta etapa.
