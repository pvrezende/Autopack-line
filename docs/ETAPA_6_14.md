# ETAPA 6.14 — Relatórios gerenciais de OEE

## Objetivo
Permitir que Supervisor e Administrador levem os indicadores consolidados para análise, reunião e registro sem depender da paginação da tela.

## Entrega
- Exportação CSV do período filtrado em **Indicadores**.
- CSV compatível com Excel em pt-BR (UTF-8 com BOM e separador `;`).
- Relatório de impressão com filtros, resumo e histórico diário completo.
- A impressão usa o diálogo do navegador, permitindo papel ou **Salvar como PDF**.
- Exportação e impressão incluem todos os dias retornados pelo filtro (7, 14 ou 30), não apenas a página visual.
- Mantida responsividade para monitor e celular.
- Sem nova tabela ou migration.

## Validação sugerida
1. Indicadores > últimos 30 dias > L01 > HJFE12C2CG.
2. Exportar CSV e confirmar 30 linhas diárias mais cabeçalho/resumo.
3. Abrir CSV no Excel e conferir 13/08/2026 = 98,3 / 3,3 / 80,0 / 2,6.
4. Imprimir relatório e confirmar que o histórico completo aparece, inclusive dias que estavam nas páginas 2–5 da tela.
