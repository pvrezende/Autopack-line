# ETAPA 7.22.1 — Responsividade / compactação da UI

## Objetivo
Garantir uso normal da tela Operação com o navegador em 100% de zoom em notebooks e monitores, sem esconder conteúdo por `overflow: hidden` e sem recorrer a `transform: scale()` ou zoom CSS.

## Alterações
- Painéis técnicos da Operação iniciam recolhidos.
- Mantida a regra de apenas um accordion técnico aberto por vez.
- Removido o corte vertical da Operação causado por `height: 100vh` + `overflow: hidden`.
- Densidade compacta para viewport desktop/notebook com até 1000 px de altura.
- Cabeçalho, status, leitor e accordions compactados apenas na tela Operação.
- Sidebar aberta reduzida para 210 px nesse perfil; o auto-recolhimento existente foi preservado.
- Conteúdo aberto permanece completo e a página pode rolar naturalmente quando diagnóstico técnico for expandido.
- Layout mobile/tablet existente preservado.

## Critério de aceite
1. Chrome/Edge em 100% de zoom.
2. Tela Operação legível e utilizável sem elementos cortados.
3. Todos os accordions 7.15–7.22 fechados no carregamento inicial.
4. Abrir um accordion não elimina conteúdo: a página rola se necessário.
5. Menu lateral continua recolhível.
6. Nenhuma alteração na lógica de produção, Modbus, banco ou fluxo automático.

## Observação
Os painéis técnicos continuam temporariamente na Operação para validação das etapas. A reorganização final para Diagnóstico/Engenharia permanece planejada para a etapa de UI profissional.
