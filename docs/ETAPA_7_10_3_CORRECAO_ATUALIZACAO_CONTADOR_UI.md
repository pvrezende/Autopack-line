# ETAPA 7.10.3 — Correção da atualização do contador produzido confirmado

## Problema observado
Após um ACK aceito, a unidade mudava corretamente para `PALLETIZED` no MySQL e o palete era atualizado, porém o cartão da OP na tela Operação permanecia com o valor anterior de `produzido confirmado`. O botão global **Atualizar dados** também não recarregava a lista interna de OPs mantida pelo `OperationPanel`.

## Causa
O `OperationPanel` mantém `activeOrders` em estado local. Essa lista era recarregada após validar uma leitura, mas não depois do ACK. O refresh global do `App` recarregava produtos, linhas, configurações e dashboards, mas não forçava o estado local de OPs da tela Operação a consultar novamente `/production-orders`.

## Correção
- Após ACK com resultado, a tela consulta novamente as OPs ativas da linha e atualiza `activeOrders`.
- O `App` agora mantém `operationRefreshKey`; o botão **Atualizar dados** incrementa essa chave e força a tela Operação a recarregar suas OPs.
- A fonte da verdade continua sendo o backend/MySQL. Nenhum incremento de contador é feito manualmente no frontend.
- `produzido confirmado` continua sendo calculado apenas por unidades `PALLETIZED`.

## Regressões preservadas
- Retentativas e estado seguro do CLP (7.10).
- Separação entre leituras válidas e produzido confirmado (7.10.1).
- QR de teste com serial único (7.10.2).
- Interface recolhível/responsiva.
