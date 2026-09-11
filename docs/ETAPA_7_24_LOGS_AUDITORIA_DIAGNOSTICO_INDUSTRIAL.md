# ETAPA 7.24 — Logs, auditoria e diagnóstico industrial

Objetivo: consolidar diagnóstico persistente do fluxo automático sem depender da tela que estava aberta no momento da ocorrência.

## Implementado
- Catálogo industrial de eventos com categoria e severidade.
- Reuso da tabela `audit_logs` para eventos de leitor, ciclo automático, ACK/NACK, timeout, comunicação, retry, duplicidade e simulador.
- Correlação de eventos com linha, OP e unidade quando disponíveis.
- Consulta das transações PLC pendentes em `plc_transactions` para diagnóstico/reconciliação.
- Endpoint autenticado `/api/v1/integrations/plc/industrial-diagnostics`.
- Painel temporário de validação na tela Operação, recolhido por padrão.
- Nenhuma conexão física Modbus é aberta nesta etapa.

## Política de retenção
A retenção definitiva não foi fixada em código. Ela permanece como parâmetro a definir/configurar antes da homologação, seguindo a regra do projeto de não congelar limites incertos.

## UI final
O painel da ETAPA 7.24 é temporário. Na reorganização visual, detalhes técnicos serão movidos para Diagnóstico/Manutenção e removidos da tela operacional normal.
