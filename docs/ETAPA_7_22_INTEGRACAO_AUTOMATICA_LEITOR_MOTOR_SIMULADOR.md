# ETAPA 7.22 — Integração automática leitor → motor → CLP simulado

Objetivo: conectar o leitor HID/USB ao fluxo automático já modelado, sem clique em "Validar leitura" no fluxo normal.

## Fluxo offline
RECEBER_QR → VALIDAR_AUTOMATICAMENTE → CRIAR_UNIDADE → ENVIAR_AO_CLP_SIMULADO → AGUARDAR_CONFIRMACAO_SIMULADA → REGISTRAR_RESULTADO → LIBERAR_PROXIMO_QR.

## Segurança
- Não abre socket físico.
- Não acessa 192.168.0.2.
- QR inválido/rejeitado/duplicado não chega ao CLP simulado.
- Falha de comunicação mantém estado seguro.
- HID auto-validate fica ativo por padrão nesta etapa de homologação offline.
