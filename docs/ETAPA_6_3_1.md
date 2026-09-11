# ETAPA 6.3.1 — Correção de fuso horário

- MySQL e backend continuam armazenando datas em UTC.
- O frontend interpreta timestamps sem sufixo como UTC.
- A exibição é convertida para o fuso operacional configurado por `VITE_TIME_ZONE`.
- Padrão atual: `America/Manaus` (UTC-4).
- A correção foi aplicada à auditoria, último acesso, dashboard e rastreabilidade.
- Nenhuma migration é necessária e nenhum dado existente é apagado.
