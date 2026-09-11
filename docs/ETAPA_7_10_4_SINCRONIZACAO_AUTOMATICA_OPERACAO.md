# ETAPA 7.10.4 — Sincronização automática da Operação

## Objetivo
Eliminar a necessidade de F5 ou ação manual para que a tela Operação reflita resultados já confirmados no backend/MySQL.

## Alterações
- A lista de OPs ativas é sincronizada automaticamente a cada 2 segundos enquanto a tela Operação está aberta.
- O contador **produzido confirmado** continua vindo do backend e considera apenas unidades `PALLETIZED`.
- Após ACK aceito, a tela faz uma atualização imediata e duas novas consultas curtas (0,5 s e 1,5 s).
- Quando existe uma unidade de ciclo conhecida, o estado do ciclo CLP também é consultado automaticamente.
- Falhas transitórias de atualização não apagam o último estado válido e são tentadas novamente no próximo ciclo.

## Regra preservada
O frontend não incrementa contadores manualmente. O MySQL/backend permanece como fonte da verdade.

## Resultado esperado
`SCANNED` aumenta leituras válidas sem aumentar produção confirmada. Após ACK e transição para `PALLETIZED`, a tela atualiza automaticamente o produzido confirmado sem F5.
