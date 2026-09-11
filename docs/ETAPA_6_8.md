# ETAPA 6.8 — Metas e regras produtivas configuráveis

## Objetivo
Ativar no AUTOPACKLINE as metas de produção que já existiam como parâmetros editáveis, sem fixar valores em código e sem inventar regras industriais ainda não validadas.

## Implementado
- Meta por hora configurável por linha e opcionalmente por produto.
- Meta diária configurável.
- Takt configurável em segundos.
- Histórico preservado: ao salvar uma nova meta, a anterior é encerrada e a nova passa a ser a ativa.
- Meta específica do produto tem prioridade sobre a meta geral da linha.
- Dashboard mostra a meta somente quando uma linha é selecionada, evitando misturar metas de linhas diferentes.
- Produção por hora passa a exibir realizado/meta quando houver meta/hora.
- Para os períodos Hoje e Ontem, o Dashboard calcula o progresso simples da meta diária: unidades paletizadas / meta diária.
- Tela Configurações mostra as metas ativas com paginação.

## Não implementado de propósito
Ainda não calculamos automaticamente:
- OEE;
- eficiência de turno;
- disponibilidade;
- horas produtivas;
- desconto de intervalos/paradas;
- meta proporcional a turno parcial.

Esses indicadores dependem de regras industriais que precisam ser confirmadas antes de virarem lógica do sistema.

## Teste sugerido
1. Entre como Administrador.
2. Vá em Configurações > Metas de produção.
3. Cadastre, por exemplo, uma meta geral para L01: meta/hora 10, meta diária 80, takt 360 s.
4. Vá ao Dashboard.
5. Selecione L01 e Período Hoje.
6. Confirme que aparece o cartão de Meta aplicada.
7. Confirme que Produção por hora mostra realizado/meta.
8. Cadastre depois uma meta específica para um produto da L01 e filtre esse produto no Dashboard.
9. Confirme que a meta específica do produto passa a ter prioridade.

## Ajuste 6.8.1
Tela de Configurações reorganizada em painéis recolhíveis tipo hambúrguer, mantendo apenas uma seção operacional aberta por vez para reduzir rolagem vertical.
