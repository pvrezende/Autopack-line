# ETAPA 7.23 — Testes de falhas, timeout, reconexão, restart e duplicidade

## Objetivo
Consolidar uma matriz determinística de cenários de resiliência usando as camadas já implementadas nas etapas 7.16–7.22, sem abrir conexão com o CLP físico.

## Cenários validados
- perda total de comunicação;
- timeout com retentativa de transporte;
- esgotamento das 3 tentativas;
- heartbeat do CLP parado por 5 s;
- reconexão obrigando reconciliação antes de nova escrita;
- restart com unidade já concluída pelo CLP;
- CLP sem conhecimento da sequência pendente, exigindo reenvio da mesma REQUEST_SEQUENCE;
- conflito de sequência;
- resposta de sequência duplicada;
- ciclo abortado sem contabilização de paletização.

## Invariantes de segurança
1. Comunicação não confiável bloqueia novas unidades.
2. Retentativa de transporte nunca cria nova REQUEST_SEQUENCE.
3. Timeout físico não autoriza reenvio automático de uma nova identidade.
4. Reconexão/restart sempre reconcilia antes de escrever.
5. D760/D761 é autoritativo para impedir dupla contabilização.
6. Duplicidade/conflito nunca é considerado paletização válida.
7. Aborto nunca incrementa produção confirmada.

## Conexão física
Não utilizada. `192.168.0.2:502` permanece sem tentativa de socket nesta etapa.
