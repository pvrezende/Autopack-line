# ETAPA 6.13 — Histórico e comparação de OEE

## Objetivo
Permitir que Supervisor e Administrador acompanhem a evolução diária dos indicadores consolidados já validados na Dashboard.

## Entregas
- novo menu **Indicadores**;
- histórico de OEE dos últimos 7, 14 ou 30 dias;
- filtros por linha e produto;
- médias de Disponibilidade, Performance, Qualidade e OEE;
- Qualidade acumulada do período;
- produção total do período;
- tabela diária paginada (7 dias por página);
- responsividade para monitor, tablet e celular;
- nenhuma nova tabela ou migration: todos os números são calculados a partir dos dados existentes no MySQL.

## Regra
Cada dia reutiliza exatamente as mesmas fórmulas das etapas 6.11 e 6.12, preservando consistência entre a Dashboard do dia e o histórico.
