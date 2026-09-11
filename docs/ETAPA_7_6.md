# ETAPA 7.6 — Continuidade automática do ciclo de paletes

## Objetivo
Validar a transição entre um palete concluído e o próximo palete da mesma OP/produto/linha.

## Implementado
- O retorno do CLP distingue `NEW_PALLET_STARTED`, `PALLET_IN_PROGRESS` e `PALLET_COMPLETED`.
- `new_pallet_started` informa explicitamente quando a unidade abriu um novo palete.
- A capacidade continua vindo de `product_pallet_configs` no MySQL.
- Nenhum protocolo físico de CLP foi presumido.
- A interface mostra a transição sem aumentar desnecessariamente a altura dos painéis.

## Teste esperado
Com o palete anterior completo, validar um serial novo e confirmar a paletização simulada. O resultado deve mostrar um código de palete diferente, `1 / capacidade`, estado `NOVO PALETE INICIADO` e a mensagem de criação automática do novo palete.
