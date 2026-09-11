# ETAPA 6.15 — Análise de perdas

A área **Indicadores** passa a ter duas visões:

- Histórico de OEE (mantém a ETAPA 6.13/6.14);
- Análise de perdas.

A análise de perdas usa somente dados já existentes no MySQL e não cria valores fixos nem nova tabela.

## Indicadores

- tempo total parado;
- tempo de parada planejada;
- tempo de parada não planejada;
- quantidade de ocorrências de leitura;
- REJECTED;
- DUPLICATE;
- Pareto de paradas não planejadas por motivo, ordenado por minutos;
- Pareto das ocorrências de rastreabilidade por mensagem/motivo.

## Filtros

- últimos 7, 14 ou 30 dias;
- linha;
- produto opcional.

Ao filtrar por produto, leituras `INVALID` sem EAN não são atribuídas ao produto, pois o sistema não possui evidência segura para esse vínculo.

## Banco

Nenhuma migration nova. A etapa consulta `downtime_events`, `production_orders`, `products` e `scan_events`.
