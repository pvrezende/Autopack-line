# ETAPA 6.10 — Jornada de produção, turnos, pausas e paradas

Esta etapa cria a base temporal necessária para os indicadores industriais futuros sem ativar OEE antes da validação das regras da fábrica.

## Implementado

- cadastro de turnos por linha;
- turnos que atravessam meia-noite;
- cálculo automático da duração bruta da jornada;
- cadastro de pausas planejadas por turno: pausa, refeição, setup planejado e outros;
- cálculo do tempo planejado líquido: jornada menos pausas cadastradas;
- registro de paradas planejadas e não planejadas;
- vínculo opcional da parada com OP e turno;
- parada pode ser criada já encerrada ou ficar aberta e ser encerrada posteriormente;
- duração de parada calculada automaticamente;
- paginação separada para Turnos, Pausas e Paradas;
- auditoria das principais ações;
- Administrador configura turnos e pausas;
- Administrador e Supervisor registram/encerram paradas.

## Importante

Nesta etapa os novos dados **não alteram automaticamente** metas, ritmo, eficiência ou OEE. Eles serão a fonte das próximas regras, depois que os parâmetros operacionais forem validados.

## Migration

A migration `0006_work_schedules_and_downtime.py` cria:

- `work_shifts`
- `planned_breaks`
- `downtime_events`

Turnos e pausas podem ser editados pelo Administrador e também podem ser desativados sem apagar o histórico.
