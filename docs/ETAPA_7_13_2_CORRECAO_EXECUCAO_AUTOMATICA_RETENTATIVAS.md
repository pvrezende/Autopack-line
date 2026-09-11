# ETAPA 7.13.2 — Correção da execução automática das retentativas

## Problema observado

O botão **Simular falha até esgotar retentativas** configurava `3 falha(s) armada(s)`, porém não iniciava o processamento do retorno do CLP. A unidade permanecia em `SCANNED / AGUARDANDO RETORNO DO CLP` indefinidamente até que outra ação fosse executada.

## Causa

A ação `TIMEOUT_RETRY_CYCLE` apenas chamava o endpoint de controle do simulador, que corretamente preparava três timeouts. Entretanto, o ciclo de retentativa é executado pelo endpoint de confirmação (`process_with_retry`) e não havia um disparo automático após o preparo das falhas.

## Correção

Na tela de Operação, ao executar `TIMEOUT_RETRY_CYCLE`, o frontend agora:

1. arma automaticamente o número máximo de timeouts configurado;
2. dispara a confirmação simulada do CLP imediatamente;
3. o backend executa `process_with_retry`;
4. consome as tentativas até o limite;
5. retorna `RETRIES_EXHAUSTED / PLC_RETRY_EXHAUSTED`;
6. não grava a unidade no palete e não aumenta o produzido confirmado.

O botão **Simular 1 timeout + recuperação automática** mantém o comportamento já validado anteriormente, permitindo o teste de recuperação controlada.

## Resultado esperado do teste

Após clicar uma única vez em **Simular falha até esgotar retentativas** com uma unidade `SCANNED` aguardando CLP:

- `Último ciclo` deve mostrar `3/3`;
- `Último erro` deve mostrar `PLC_TIMEOUT`;
- `Estado` deve mostrar `RETENTATIVAS ESGOTADAS`;
- deve aparecer `PLC_RETRY_EXHAUSTED` no feedback;
- `falha(s) armada(s)` deve voltar para zero;
- a unidade não deve ser paletizada;
- o contador de produzido confirmado não deve aumentar.
