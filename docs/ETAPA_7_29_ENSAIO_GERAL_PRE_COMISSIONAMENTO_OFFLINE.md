# ETAPA 7.29 — Ensaio geral pré-comissionamento offline

## Objetivo
Consolidar as etapas 7.23, 7.25, 7.26, 7.27 e 7.28 em um único ensaio de prontidão antes da ida à máquina, sem antecipar nenhuma ação física.

## Entrega
- Endpoint `GET /api/v1/integrations/plc/commissioning-rehearsal`.
- 7 checks consolidados: health-check, resiliência, gate offline, gate real, plano, manifesto de evidências e socket físico.
- Sequência dos passos de comissionamento preservada e classificada como `DRY_RUN_READY`, `WAIT_AUTOMATION`, `WAIT_FACTORY` ou `BLOCKED`.
- Regra explícita de STOP para qualquer divergência crítica.
- Handoff de fábrica pronto para orientar o comissionamento presencial.

## Segurança
A 7.29 é 100% offline. Não abre socket Modbus, não habilita o adaptador físico e não escreve D700-D749. O gate real permanece bloqueado enquanto as pendências da automação e do comissionamento não forem fechadas.

## Critério de aceite
`fail_count = 0`, `status = REHEARSAL_READY_OFFLINE` e `physical_socket_opened = false`.
