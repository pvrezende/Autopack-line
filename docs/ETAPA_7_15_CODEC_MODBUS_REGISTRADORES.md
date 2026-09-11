# ETAPA 7.15 — Codec Modbus dos registradores D700–D763

## Objetivo

Preparar integralmente, fora da fábrica, a codificação/decodificação dos dados definidos no contrato Modbus TCP do AUTOPACKLINE com o Delta AS228T-A.

## Implementado

- validação estrita de `UINT16` (0–65535);
- montagem lógica completa de D700–D749;
- `AP_PAYLOAD_FLAGS` em D705;
- comprimentos de serial, EAN, OP e modelo;
- codificação ASCII com 2 caracteres por registrador;
- suporte explícito aos dois byte orders possíveis (`HIGH_LOW` e `LOW_HIGH`);
- vetor de comissionamento `AB12` sem escolher antecipadamente qual ordem é a real;
- rejeição de texto não ASCII, sem transliteração silenciosa;
- interpretação de D750–D763;
- decodificação dos bits D755.0–D755.8;
- interpretação de `RESULT_CODE`, `COMPLETION_RESULT` e `PLACE_CONFIRM_SOURCE`;
- D754 e D756 mantidos numéricos enquanto suas tabelas oficiais estiverem pendentes;
- nenhuma suposição sobre o offset físico Modbus de D700–D763.

## Regra de escrita

O codec separa a ordem definida pela automação:

1. payload: D704–D749;
2. cabeçalho/disparo: D700–D703 por último.

## O que continua pendente apenas para fábrica/comissionamento

- confirmar byte order ASCII usando `AB12`;
- confirmar offset/endereço Modbus físico dos registradores Delta D;
- tabela D754 (`AP_MACHINE_STATE`);
- tabela D756 (`AP_ACTIVE_FAULT_CODE`);
- IDs oficiais de receita.

Nenhum desses itens impede o desenvolvimento e os testes offline das próximas etapas.
