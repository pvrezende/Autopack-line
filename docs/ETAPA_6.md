# ETAPA 6 — Núcleo funcional do AUTOPACKLINE

## Decisões implementadas

- QR real com cinco campos separados por `;`.
- Produto identificado no cadastro pelo EAN; o primeiro campo do QR é preservado bruto porque o prefixo `45` ainda não foi explicado.
- Serial é único por unidade.
- OP é armazenada como texto para preservar zeros à esquerda.
- Leitura e paletização são eventos diferentes.
- Paletização depende de configuração ativa de quantidade por produto + linha.
- Alterar a configuração não muda paletes já abertos.
- Palete contém somente um produto e uma OP nesta versão técnica; a regra de lote permanece pendente até a origem do lote ser confirmada.
- O sinal de CLP é simulado por botão; nenhuma comunicação física foi inventada.

## Pendências de integração

- origem oficial do lote;
- significado do prefixo `45`;
- leitor físico e protocolo;
- CLP/robô e sinal de caixa efetivamente paletizada;
- MES;
- autenticação/permissões;
- fluxo de transporte/totem/etiqueta.

## Atualização 6.1 — Rastreabilidade escalável
- Filtros de leituras por período, linha, status, serial, EAN e OP.
- Filtros de paletes por período, linha, produto, status, código e OP.
- Paginação server-side (10, 20 ou 50 registros por página).
- Novos campos indexados em `scan_events` para serial, EAN e OP (migration `0003`).
- Registros históricos permanecem no banco; filtros alteram apenas a consulta/exibição.
- Horários exibidos no frontend passam a interpretar timestamps do banco como UTC e apresentar no horário local do navegador.

## ETAPA 6.1 — Rastreabilidade: exportação e impressão
- Exportação CSV respeitando os filtros aplicados em Leituras e Paletes.
- Ação "Detalhes / imprimir" por registro.
- Relatório de leitura com status, data/hora, serial, EAN, OP, linha, ocorrência e código bruto.
- Relatório de palete com produto, EAN, OP, lote, linha, capacidade, datas e lista de seriais.
- CSS específico para impressão limpa e opção do navegador para salvar em PDF.


### Ajuste de impressão
- Cada leitura e cada palete possui agora ações separadas **Detalhes** e **Imprimir**.
- O botão **Imprimir** direto abre o relatório específico e chama a impressão do navegador, permitindo imprimir em papel ou salvar em PDF.

## ETAPA 6.1.2 — impressão consolidada por filtro
- Removida a impressão individual das linhas de leituras e paletes; o detalhe permanece apenas para consulta.
- A impressão passa a ser feita exclusivamente pelo botão **Imprimir período filtrado**.
- O relatório respeita os filtros aplicados e busca todos os registros do filtro, independentemente da paginação visual.
- Corrigido o CSS de impressão para retirar o layout principal do fluxo do documento. Isso elimina páginas em branco causadas pelo uso anterior de `visibility: hidden`, que ocultava os elementos mas ainda preservava a altura da aplicação no papel.
- Tabelas de impressão usam cabeçalho repetível e evitam quebra de uma linha entre páginas.
