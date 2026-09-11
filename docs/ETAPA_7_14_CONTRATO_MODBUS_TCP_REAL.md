# ETAPA 7.14 — Contrato Modbus TCP real AUTOPACKLINE ↔ Delta AS228T-A

## Objetivo
Formalizar no código o contrato técnico proposto pela automação para futura integração física, sem depender da máquina presente e sem habilitar comunicação real antes do ladder estar implementado.

## Status da automação
**PROPOSTA — AINDA NÃO IMPLEMENTADA NO LADDER.**

## Rede proposta
- CLP: Delta AS228T-A
- Protocolo: Modbus TCP
- CLP: servidor
- AUTOPACKLINE: cliente
- Porta: 502
- IP CLP: 192.168.0.2
- IP PC: 192.168.0.10
- Máscara: 255.255.255.0
- Gateway: vazio em rede isolada

## Mapa
- PC → CLP: D700-D749
- CLP → PC: D750-D763

O mapa completo é disponibilizado pelo backend em `GET /api/v1/integrations/plc/modbus-contract`.

## Regras já formalizadas
- heartbeat PC 1 s;
- polling CLP 250 ms;
- timeout de transporte 1 s;
- 3 tentativas de transporte com intervalo de 1 s;
- timeout de ACK 2 s;
- timeout físico inicial 120 s;
- timeout físico **não** autoriza reenvio automático da unidade;
- nova unidade bloqueada quando BUSY=1;
- paletização somente com D760 igual à REQUEST_SEQUENCE e D761=1;
- em reconexão, reconciliar estado antes de qualquer escrita;
- ao reenviar unidade desconhecida pelo CLP, reutilizar a mesma REQUEST_SEQUENCE.

## A DEFINIR COM AUTOMAÇÃO
- tabela numérica D754 AP_MACHINE_STATE;
- tabela código/texto D756 AP_ACTIVE_FAULT_CODE;
- relação dos IDs de receitas D704/D763;
- revisão do ladder quando D700-D763 estiver implementado.

## SOMENTE NO COMISSIONAMENTO
- byte order ASCII, validado com `AB12`;
- offset/endereço Modbus efetivo para os registradores D;
- comunicação real com porta 502 e sinais físicos.

## Importante
Esta etapa não conecta o software ao CLP físico. Ela cria uma única fonte de verdade para as próximas etapas 7.15+ e impede que parâmetros ainda não confirmados sejam inventados no código.
