# ETAPA 6.5.4 — Filtros de data

Objetivo: permitir consultar produção e auditoria de dias anteriores sem perder o padrão operacional de exibir o dia atual.

## Dashboard
- Hoje
- Ontem
- Últimas 24 horas
- Últimos 7 dias
- Este mês
- Data / período personalizado
- Todo período

## Rastreabilidade
O mesmo conjunto de períodos está disponível separadamente para Leituras e Paletes. Exportação CSV e impressão respeitam o período filtrado.

## Auditoria
A tela de Usuários passa a filtrar a auditoria por data mantendo a paginação de 4 eventos por página.

## Fuso horário
O banco e o backend continuam em UTC. Os limites escolhidos na interface são convertidos antes da consulta e os horários exibidos continuam no fuso operacional configurado.
