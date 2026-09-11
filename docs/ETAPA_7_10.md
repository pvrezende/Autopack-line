# ETAPA 7.10 — Retentativa controlada e recuperação operacional do CLP

## Objetivo
Evoluir a proteção de comunicação da ETAPA 7.9 para que timeouts transitórios possam ser recuperados de forma controlada, sem comprometer a rastreabilidade ou adicionar uma unidade ao palete antes de um ACK aceito.

## Regras implementadas
- `PLC_RETRY_MAX_ATTEMPTS` define o máximo de tentativas (padrão: 3).
- `PLC_RETRY_INTERVAL_SECONDS` define o intervalo entre tentativas (padrão: 1 s).
- `PLC_SIMULATOR_TIMEOUT_SECONDS` continua definindo o timeout nominal do simulador.
- Apenas `TIMEOUT` é repetido automaticamente. NACK, desconexão e erros de sequência não entram em loop automático.
- Sem ACK aceito, a unidade continua `SCANNED` no MySQL e nenhuma linha é criada em `pallet_items`.
- Ao esgotar o limite, o backend retorna `RETRIES_EXHAUSTED` / `PLC_RETRY_EXHAUSTED`.
- Uma nova tentativa manual pode ser feita sobre a mesma unidade, sem nova leitura.
- O resultado registra quantidade de tentativas, último erro e se o limite foi esgotado; esses dados também entram na auditoria do sinal.

## Simulações disponíveis
- **Simular 1 timeout + recuperação automática**: a primeira tentativa falha e a retentativa seguinte deve concluir o ACK.
- **Simular falha até esgotar retentativas**: todas as tentativas do ciclo falham, nenhuma paletização é gravada e a unidade continua aguardando CLP.
- **Restaurar comunicação**: limpa a simulação de falhas e a telemetria do último ciclo de retry.

## Segurança
A regra continua fail-safe: timeout, desconexão ou esgotamento de retentativas nunca equivalem a uma confirmação física. Somente um ACK efetivamente aceito chama a regra de paletização.

## Hardware real
Nenhum fabricante, protocolo, IP, porta ou tag de CLP foi presumido nesta etapa. O adaptador permanece `SIMULATOR_PLC_V1`.

## Testes sugeridos
1. Validar uma unidade nova e deixá-la em `AWAITING_PLC`.
2. Armar 1 timeout e enviar ACK: o mesmo clique deve retornar sucesso após 2/3 tentativas e paletizar uma única vez.
3. Em outra unidade nova, armar falha até esgotar e enviar ACK: deve retornar `RETRIES_EXHAUSTED`, mantendo a unidade sem palete.
4. Sem nova leitura, enviar ACK novamente: deve confirmar normalmente e paletizar uma única vez.
5. Repetir `Ctrl+F5` e confirmar que o estado produtivo continua reconstruído pelo MySQL.
