# ETAPA 7.8.1 — Correção da persistência após refresh

## Problema encontrado no teste real
Uma unidade VALID aguardando retorno do CLP permanecia no MySQL, porém após Ctrl+F5 o frontend voltava para “Aguardando validação” e não reconstruía o painel ACK/NACK.

## Correção
- Novo endpoint `GET /api/v1/integrations/plc/latest-cycle?line_id=...&production_order_id=...`.
- O backend localiza no MySQL a unidade mais recente da OP e reconstrói seu ciclo usando a mesma regra `inspect_cycle`.
- A tela Operação consulta esse endpoint sempre que linha + OP ativa estão definidas.
- O estado `AWAITING_PLC` ou `PALLETIZED` é restaurado mesmo se o sessionStorage falhar ou estiver vazio.
- O conteúdo capturado antigo é limpo na restauração para não exibir um serial diferente da unidade restaurada.
- O contexto restaurado informa explicitamente o serial e o estado recuperado do MySQL.

Nenhuma migration nova. Nenhum valor de processo foi fixado em código.
