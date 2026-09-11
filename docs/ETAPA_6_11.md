# ETAPA 6.11 — Tempo planejado, tempo disponível e eficiência operacional

A Dashboard passa a usar os dados validados na ETAPA 6.10.

## Fórmulas

- Jornada bruta: soma das janelas dos turnos ativos que interceptam o período filtrado.
- Pausas planejadas: intervalos ativos cadastrados no turno.
- Paradas planejadas: eventos `PLANNED` dentro do tempo produtivo.
- Tempo planejado: jornada bruta - pausas planejadas - paradas planejadas.
- Paradas não planejadas: eventos `UNPLANNED` que interceptam o tempo planejado.
- Tempo disponível: tempo planejado - paradas não planejadas.
- Eficiência operacional: tempo disponível / tempo planejado × 100.

Os intervalos são unidos e recortados antes da soma, evitando dupla contagem quando eventos se sobrepõem. Turnos que atravessam meia-noite são suportados. Os horários de turno e pausa são interpretados em `America/Manaus`; timestamps de eventos continuam armazenados em UTC.

## Escopo

Nesta etapa o indicador é calculado para **Linha + Período**. Produto e OP continuam filtrando os KPIs produtivos, mas não alteram a jornada da linha. OEE completo ainda não é calculado.
