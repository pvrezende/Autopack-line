# ETAPA 7.32 — Consolidação profissional do reteste offline

## Objetivo

Transformar a fundação técnica da ETAPA 7.31 em uma área segura e compreensível para consulta e validação offline, sem assumir regras ainda pendentes da automação ou da Elgin.

## Entregas

- Endpoint `GET /api/v1/retests/units` para busca por serial, OP ou modelo.
- Retorno de produto, OP, estado da unidade, total de tentativas e última decisão.
- Lista selecionável de unidades na interface, eliminando consulta manual ao MySQL.
- Histórico em português e identificação clara de que nenhuma tentativa foi contabilizada.
- Confirmação antes de cada simulação.
- Aprovação indisponível até existir reprovação anterior.
- Auditoria de busca, consulta de histórico e simulação.
- Proteção contra colisão de chaves de idempotência.
- Interface recolhível com indicador visual `+`/`−` e adaptação para telas menores.

## Segurança preservada

- `RETEST_ENABLED=false` mantém o fluxo real bloqueado.
- Nenhum socket Modbus é aberto por esta funcionalidade.
- A unidade preserva seu estado produtivo original.
- Contadores de produção e paletes não são alterados.
- Fontes MES, CLP e OPERATOR continuam indisponíveis.

## Definições ainda pendentes

- Origem oficial de aprovação e reprovação.
- Regra de autorização e limite de retestes.
- Contrato e disponibilidade do MES.
- Impacto definitivo na produção e paletização.

Essas definições não foram simuladas como regras reais e não bloqueiam os testes offline desta etapa.

## Validação esperada

1. Abrir **Manutenção e Diagnóstico** e expandir o card de reteste.
2. Buscar uma unidade por serial, OP ou modelo.
3. Selecionar a unidade e conferir seu contexto.
4. Confirmar que a aprovação começa bloqueada.
5. Simular uma reprovação.
6. Simular o reteste aprovado.
7. Atualizar o histórico e confirmar a permanência das tentativas.
8. Conferir que ambas possuem `counted_in_production = 0` e que o estado da unidade não mudou.
