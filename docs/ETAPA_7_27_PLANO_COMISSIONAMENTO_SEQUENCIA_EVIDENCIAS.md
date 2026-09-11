# ETAPA 7.27 — Plano de comissionamento, sequência e evidências

## Objetivo
Transformar o gate 7.26 em um roteiro ordenado de comissionamento, separando o que pode ser preparado offline, o que depende da automação e o que só pode ser executado com acesso físico à máquina.

## Segurança
- Nenhum socket Modbus físico é aberto pela 7.27.
- A execução real continua bloqueada enquanto o gate 7.26 possuir pendências.
- O roteiro inicia por baseline/health-check, depois contrato da automação, rede, offset/byte-order, leitura somente e somente então handshake controlado.
- ACK não contabiliza produção; a confirmação física continua condicionada a D760 = REQUEST_SEQUENCE e D761 = 1.
- Divergência de sequência, heartbeat, offset, byte order ou estado da máquina é condição de STOP.

## Entrega
O endpoint `/api/v1/integrations/plc/commissioning-plan` devolve 12 passos ordenados com fase, status e evidência esperada. A tela Operação mostra o plano em accordion técnico fechado por padrão.
