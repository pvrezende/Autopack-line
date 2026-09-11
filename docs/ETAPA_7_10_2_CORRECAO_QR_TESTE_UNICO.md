# ETAPA 7.10.2 — Correção do QR de teste único

## Objetivo
Corrigir o botão **Usar QR de teste**, que reutilizava o serial fixo `ARC062600106197` e inevitavelmente passava a retornar `DUPLICATE` depois da primeira utilização.

## Alteração
- O frontend não possui mais um QR/serial de teste fixo.
- O backend gera um QR de homologação a partir da **OP ativa selecionada**.
- SKU, EAN, modelo e número da OP vêm do cadastro atual do MySQL.
- O serial é gerado no formato `ARC` + 12 dígitos e conferido contra as unidades já existentes antes de ser entregue à tela.
- Gerar o QR **não grava** leitura, unidade, palete ou auditoria; somente o clique em **Validar leitura** executa o fluxo produtivo.

## Resultado esperado
Cada clique em **Usar QR de teste** produz um novo serial para a OP selecionada, evitando que o próprio simulador provoque duplicidade artificial. A regra real de bloqueio de serial duplicado permanece inalterada.
