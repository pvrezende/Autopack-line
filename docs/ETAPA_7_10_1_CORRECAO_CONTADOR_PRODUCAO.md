# ETAPA 7.10.1 — Correção do contador de produção confirmada

## Problema encontrado em teste
A OP incrementava o campo visual "produzido" no momento em que uma leitura VALID criava uma `production_unit` em estado `SCANNED`. Assim, após o ACK do CLP, a unidade passava para `PALLETIZED`, mas o número não aumentava novamente — porque aquela unidade já havia sido contada antes da confirmação física.

## Correção
- `produced_quantity` agora conta somente unidades `PALLETIZED`, isto é, produção confirmada pelo retorno do CLP/paletização.
- `scanned_quantity` preserva a quantidade de leituras válidas/unidades criadas, inclusive as que ainda aguardam CLP.
- O progresso da OP usa produção confirmada.
- A tela Operação identifica explicitamente **produzido confirmado** e mostra também o total de **leituras válidas**.
- A regra de segurança para impedir troca de produto em OP com qualquer unidade criada continua usando todas as unidades, portanto não foi enfraquecida.
- Nenhuma migration é necessária; a correção usa o `status` já existente em `production_units`.

## Regra resultante
`VALID/SCANNED` aumenta leituras válidas. Somente `ACK -> PALLETIZED` aumenta produção confirmada. Timeout, NACK ou retentativas esgotadas nunca aumentam produção confirmada.
