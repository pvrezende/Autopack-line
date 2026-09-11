# ETAPA 7.28 — Pacote de evidências e checklist de comissionamento

## Objetivo
Transformar os 12 passos ordenados da ETAPA 7.27 em um manifesto de evidências verificável, sem antecipar testes que dependem da automação ou da máquina física.

## Entrega
- Endpoint `GET /api/v1/integrations/plc/commissioning-evidence`.
- Snapshot das etapas 7.23, 7.25, 7.26 e 7.27.
- Um item de evidência para cada passo do plano 7.27.
- Campos mínimos definidos para execução futura: data/hora, responsável, PASS/FAIL, observação e referência da evidência.
- Estados separados em `PREPARED`, `WAIT_AUTOMATION`, `WAIT_FACTORY` e `BLOCKED`.

## Segurança
A ETAPA 7.28 é 100% offline. Ela não abre socket Modbus, não habilita `PLC_PHYSICAL_ENABLED`, não executa escrita D700-D749 e não transforma evidência esperada em evidência concluída. Qualquer FAIL/divergência durante o comissionamento aplica a regra de STOP da 7.27.

## Interface
O painel técnico é apresentado em accordion fechado por padrão. Ele é temporário durante desenvolvimento/comissionamento e poderá ser movido para Diagnóstico/Manutenção na reorganização final da UI.
