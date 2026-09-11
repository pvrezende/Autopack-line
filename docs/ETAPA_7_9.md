# ETAPA 7.9 — Timeout, reconexão e estado seguro da comunicação CLP

## Objetivo
Preparar a camada de integração para falhas de comunicação antes da conexão física real do CLP/robô, sem presumir fabricante, IP, protocolo ou tags.

## O que foi incluído
- Estado de comunicação do adaptador simulado: `ONLINE` ou `DISCONNECTED`.
- Estado seguro: quando a comunicação está indisponível, ACK/NACK não alteram palete nem unidade no MySQL.
- Simulação de desconexão e reconexão do CLP.
- Simulação de timeout no próximo ACK/NACK.
- Timeout configurável pela variável `PLC_SIMULATOR_TIMEOUT_SECONDS`.
- Após timeout, a unidade continua `AWAITING_PLC` e pode receber uma nova tentativa.
- Endpoint administrativo de teste `POST /api/v1/integrations/plc/simulator-control`.
- Auditoria das mudanças do simulador e das falhas de comunicação.
- Controles ficam dentro do accordion do CLP para preservar responsividade e evitar crescimento vertical da tela.

## Ações disponíveis no simulador
- `DISCONNECT`: simula perda de comunicação e entra em estado seguro.
- `RECONNECT`: restaura a comunicação.
- `TIMEOUT_NEXT`: o próximo ACK/NACK retorna timeout sem gravar paletização.
- `RESET`: restaura estado ONLINE e remove timeout armado.

## Teste principal
1. Gere uma nova leitura `VALID` e deixe a unidade em `AWAITING_PLC`.
2. Abra o painel CLP e clique em **Simular desconexão**.
3. O painel deve mostrar `DESCONECTADO · ESTADO SEGURO` e ACK/NACK ficam indisponíveis.
4. Clique em **Reconectar simulador** e confirme que volta para `ONLINE`.
5. Clique em **Simular timeout no próximo ACK/NACK**.
6. Envie ACK. Deve aparecer `TIMEOUT DE COMUNICAÇÃO`, sem paletizar a unidade.
7. O ciclo deve continuar `AWAITING_PLC`.
8. Envie ACK novamente. A segunda tentativa deve processar normalmente.

## Persistência e segurança
Nenhuma migration nova. Falhas simuladas de comunicação não modificam `production_units`, `pallet_items` ou `pallets`. A fonte de verdade do ciclo produtivo continua sendo o MySQL.
