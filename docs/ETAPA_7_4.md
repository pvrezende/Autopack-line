# ETAPA 7.4 — Camada de integração do CLP / confirmação de paletização

Objetivo: separar a confirmação de paletização da interface e criar um contrato único para o futuro CLP/robô, sem inventar protocolo ou hardware.

## Implementado

- `GET /api/v1/integrations/plc/status` informa prontidão da camada, adaptador e sinais suportados.
- `POST /api/v1/integrations/plc/confirm` recebe a confirmação `PALLETIZE_CONFIRMED`.
- O adaptador atual é `SIMULATOR_PLC_V1`.
- A confirmação usa a mesma regra de negócio já validada de paletização, quantidade configurável, abertura/fechamento de palete e bloqueio de unidade duplicada.
- Auditoria registra `PLC_PALLETIZE_CONFIRMED`.
- Origem `PHYSICAL` permanece bloqueada até fabricante/modelo, protocolo, endereço e tags reais serem definidos.
- A tela Operação mostra o estado do CLP em seção recolhível para preservar a regra de interface compacta.

Não há migration nesta etapa.
