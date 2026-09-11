# ETAPA 7.5 — Ciclo de palete e retorno da confirmação do CLP

Objetivo: completar o contrato lógico entre a confirmação do CLP e o ciclo do palete, ainda em modo simulado e sem presumir protocolo físico.

## Implementado

- A confirmação do CLP agora devolve explicitamente o estado do ciclo: `PALLET_IN_PROGRESS` ou `PALLET_COMPLETED`.
- O retorno informa a próxima ação: `AGUARDAR_PROXIMA_UNIDADE` ou `INICIAR_NOVO_PALETE`.
- A interface mostra o retorno do ciclo junto ao palete, sem adicionar painéis permanentes; a regra de seções recolhíveis permanece.
- Ao atingir a quantidade configurada por palete, o backend continua fechando o palete automaticamente e a resposta informa que a próxima unidade deverá iniciar outro palete.
- Nenhum valor de capacidade foi fixado no código; continua sendo usada a configuração produto + linha do MySQL.
- Nenhuma data foi fixada. Dashboard e indicadores continuam calculados pelos registros efetivamente existentes no período selecionado; em um novo dia, somente os registros daquele dia entram no filtro `Hoje`.
- Hardware físico continua bloqueado até definição real de fabricante/modelo, protocolo, endereço e tags.

Não há migration nesta etapa.
