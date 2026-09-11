# ETAPA 7.16 — Máquina de estados do handshake Modbus real

## Objetivo
Transformar o contrato D700–D763 em uma máquina de estados determinística, testável offline e preparada para operação automática sem operador.

## Regras implementadas
- Nova unidade só pode ser preparada quando a comunicação está disponível e a máquina está READY=1, BUSY=0, FAULT=0 e fora de manutenção.
- D704–D749 são escritos antes de D700–D703.
- D753=1 representa aceite do pedido, não paletização.
- Uma unidade só pode ser marcada PALLETIZED quando D760 corresponde à REQUEST_SEQUENCE e D761=1.
- Falha de transporte pode repetir a operação usando a mesma REQUEST_SEQUENCE.
- Timeout do ciclo físico nunca autoriza reenvio automático da unidade.
- Queda de comunicação bloqueia novas unidades.
- Reconexão exige leitura/reconciliação antes de qualquer nova escrita.
- BUSY=1 bloqueia uma nova unidade.

## Fora do escopo desta etapa
Não há socket Modbus real nem conexão com a máquina. Offset físico, byte order ASCII, D754, D756, receitas e revisão do ladder continuam pendentes conforme etapas anteriores.

## Operação automática
A máquina de estados foi desenhada para futura execução autônoma: o operador não faz parte do handshake normal. Controles manuais permanecem apenas para diagnóstico enquanto o adaptador físico não está comissionado.
