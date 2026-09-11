# ETAPA 7.17 — Heartbeat, polling e supervisão da comunicação

## Objetivo
Preparar offline a supervisão automática do Modbus TCP real, sem abrir conexão física com o Delta AS228T-A.

## Regras implementadas
- Polling contínuo de D750-D763 a cada 250 ms.
- Heartbeat do PC em D701 a cada 1 s.
- Supervisão do heartbeat do CLP em D751.
- D751 sem alteração por 5 s coloca o sistema em estado seguro e bloqueia novas unidades.
- Timeout de transporte de 1 s, com no máximo 3 tentativas e intervalo de 1 s.
- Falha de transporte nunca cria nova REQUEST_SEQUENCE para a mesma unidade.
- Três falhas de transporte esgotadas bloqueiam produção e exigem reconciliação na volta.
- Após reconexão, reconciliar D752/D754/D757/D758/D760/D761 antes de qualquer escrita.
- Operação normal é autônoma e não depende de ação do operador.

## O que esta etapa NÃO faz
- Não abre socket Modbus TCP real.
- Não conecta em 192.168.0.2.
- Não presume que o ladder D700-D763 já foi implementado.
- Não valida offset físico ou byte order ASCII.

## Critério de conclusão
A máquina de supervisão deve distinguir inicialização, comunicação saudável, degradação, heartbeat stale, retry de transporte, estado seguro, perda de rede e reconexão, sempre bloqueando novas unidades quando a comunicação não for confiável.
