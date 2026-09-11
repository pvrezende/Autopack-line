# ETAPA 6.9.1 — Meta × Produção real no Dashboard

## Objetivo
Usar as metas configuradas na ETAPA 6.8 como referência visual para acompanhar a produção real sem inventar regras de eficiência, turno ou OEE.

## Entregas
- Exibição compacta da meta aplicada no Dashboard quando uma linha é selecionada.
- Indicadores de Meta/hora, Meta diária, Takt e unidades produzidas no período.
- Atingimento da meta diária para os períodos Hoje e Ontem.
- Quantidade restante para a meta diária.
- Situação simples: Em andamento ou Meta atingida.
- Produção por hora exibindo realizado/meta e percentual de atingimento da referência horária.
- Metas específicas por produto continuam tendo prioridade sobre a meta geral da linha.

## Regra de cálculo
- Atingimento diário = unidades paletizadas no período / meta diária × 100.
- Restante = max(meta diária - unidades paletizadas, 0).
- Atingimento por hora = unidades paletizadas na hora / meta por hora × 100.

## Limites desta etapa
Não são calculados automaticamente OEE, eficiência de turno, disponibilidade, performance com desconto de parada, tempo produtivo líquido ou metas proporcionais ao tempo trabalhado. Essas regras dependem de validação operacional da fábrica.
