# ETAPA 7.21 — Motor de produção automática sem operador

## Objetivo
Modelar e testar offline o motor de decisões que permitirá ao AUTOPACKLINE operar sem operador no fluxo normal.

## Fluxo-alvo
AGUARDAR_QR → VALIDAR_AUTOMATICAMENTE → VERIFICAR_READY_BUSY_FAULT → CRIAR_REQUEST_SEQUENCE → PERSISTIR_TRANSACAO → D704-D749 → D700-D703 COMMAND=1 → AGUARDAR_D752_D753 → AGUARDAR_D760_D761 → REGISTRAR_RESULTADO → D703=0 → LIBERAR_PROXIMO_QR.

## Regras de segurança
- Uma única unidade pendente por linha.
- BUSY=1 bloqueia nova unidade.
- Falha/manutenção bloqueiam o fluxo automático.
- Comunicação não confiável bloqueia novas leituras.
- ACK não incrementa produção.
- PALLETIZED somente com D760=REQUEST_SEQUENCE e D761=1.
- Timeout físico não autoriza reenvio automático.
- O dashboard nunca comanda motores, válvulas ou robô.

## Escopo desta etapa
A lógica é exercitada offline e não abre conexão com 192.168.0.2. A ligação automática do ReaderGateway/HID ao motor fica para a ETAPA 7.22.
