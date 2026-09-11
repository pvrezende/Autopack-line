# ETAPA 6.2 — Dashboard operacional

Esta versão evolui o Dashboard do AUTOPACKLINE sem alterar as regras já validadas de leitura, bloqueio de duplicidade, paletização, fechamento automático e rastreabilidade.

## Implementado

- Filtros por período: Hoje, últimas 24 horas, últimos 7 dias, personalizado e todo período.
- Filtros por linha, produto/modelo e OP.
- Cards calculados diretamente no MySQL: leituras, válidas, ocorrências, taxa de aprovação, unidades paletizadas, paletes abertos e paletes completos.
- Produção por hora calculada a partir das unidades efetivamente adicionadas aos paletes.
- Distribuição por status: VALID, INVALID, REJECTED e DUPLICATE.
- Paletes em andamento com quantidade atual, capacidade configurada e percentual de preenchimento.
- Últimas ocorrências com horário, status, serial, linha e motivo.
- Navegação do Dashboard para a Rastreabilidade com os filtros correspondentes já aplicados.
- Layout responsivo sem `zoom` ou `transform: scale()`.

## Regras dos indicadores

- `Taxa de aprovação = leituras VALID / total de leituras * 100`.
- `Ocorrências = INVALID + REJECTED + DUPLICATE`.
- `Unidades paletizadas` conta itens efetivamente incluídos em paletes no período filtrado.
- `Paletes abertos` representa o estado atual dos paletes OPEN para linha/produto/OP selecionados, independentemente do instante em que foram abertos.
- `Paletes completos` considera a data de conclusão (`completed_at`) dentro do período escolhido.

## Ainda não ativado como KPI definitivo

Eficiência por meta, produtividade de turno, takt atingido e indicadores equivalentes permanecem como **REQUISITO A DEFINIR**, até que as regras industriais de turno/meta sejam validadas.


## Ajuste 6.2.1 — modo monitor
O Dashboard foi compactado no desktop para exibir os indicadores, filtros, gráficos, paletes em andamento e ocorrências dentro da altura útil de um monitor, sem rolagem vertical em resoluções de operação usuais. As demais telas mantêm o comportamento responsivo e rolagem normal.

## ETAPA 6.2.3 — Menu lateral inteligente

- Em desktop/monitor, o menu lateral é ocultado automaticamente após 5 segundos sem atividade.
- Qualquer movimento do mouse, tecla, clique/toque ou redimensionamento ativo faz o menu reaparecer e reinicia o temporizador.
- O botão hambúrguer permite ocultar/mostrar manualmente.
- Ao ocultar, o Dashboard aproveita a largura liberada automaticamente.
- Em telas de até 980 px o comportamento responsivo anterior é preservado e o menu não é auto-ocultado.
