# ETAPA 7.18 — Persistência, idempotência e reconciliação pós-restart

## Objetivo
Preparar o AUTOPACKLINE para sobreviver a queda de rede, reinício do backend/PC e reconexão com o CLP sem duplicar unidade, trocar `REQUEST_SEQUENCE` ou registrar uma mesma deposição duas vezes.

Esta etapa é **offline**: não abre conexão física com o Delta AS228T-A.

## Persistência MySQL
Foi criada a tabela `plc_transactions` (migração `0008`) para guardar, antes do primeiro write físico:

- linha, OP e unidade de produção;
- `REQUEST_SEQUENCE` estável (1..65535);
- comando;
- payload completo e `payload_hash` SHA-256;
- último ACK/resultados observados do CLP;
- sequência/resultados de conclusão;
- palete/quantidade observados;
- estado de reconciliação e erro.

A unidade possui uma única identidade Modbus persistida. Após restart/reconexão, não é permitido trocar `REQUEST_SEQUENCE` ou payload silenciosamente.

## Regra de reconexão
Antes de qualquer nova escrita, ler:

`D752 / D754 / D757 / D758 / D760 / D761`

Decisões principais:

1. `D760 == REQUEST_SEQUENCE` e `D761 == 1`: registrar `PALLETIZED` somente se ainda não estiver registrado.
2. `D752 == REQUEST_SEQUENCE` e `BUSY == 1`: continuar aguardando, sem reenviar.
3. ACK conhecido, mas sem conclusão: continuar aguardando/diagnosticar; não gerar nova sequência.
4. CLP não conhece a sequência: reenviar o mesmo pacote com a mesma `REQUEST_SEQUENCE`.
5. Conclusão rejeitada (`D761=2`): finalizar sem paletizar.
6. Conflito de sequência: bloquear escrita automática e exigir diagnóstico; nunca adivinhar o estado.

## Segurança/idempotência
- Persistir antes do write físico.
- `REQUEST_SEQUENCE=0` é proibida.
- A mesma unidade não recebe uma nova identidade após restart.
- Confirmação física só ocorre por `D760=SEQ` + `D761=1`.
- O registro no MySQL deve ser idempotente (no máximo uma vez).
- O adaptador físico ainda permanece desabilitado enquanto o ladder e itens de comissionamento não estiverem fechados.

## Resultado esperado
O AUTOPACKLINE pode reiniciar ou perder comunicação mantendo contexto suficiente para reconciliar a transação pendente com o CLP antes de liberar nova produção automática.
