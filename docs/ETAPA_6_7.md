# ETAPA 6.7 — Fluxo operacional da linha

## Objetivo
Transformar a tela Operação em um fluxo orientado à OP ativa, reduzindo risco de leitura na ordem errada e aproximando a interface do uso real na linha.

## Implementado
- Seleção obrigatória de Linha + OP ATIVA antes da validação.
- Busca automática das OPs ativas da linha escolhida.
- Seleção automática quando existe apenas uma OP ativa na linha.
- Cartão operacional com OP, produto, quantidade produzida/planejada, progresso e paletes abertos.
- Validação preventiva no frontend: quando o QR contém uma OP diferente da selecionada, a leitura é bloqueada antes do envio.
- Backend continua sendo a autoridade final das regras da OP e das validações já implementadas na 6.6.
- Botão “Validar leitura” só é habilitado com uma OP ativa selecionada.
- Leitura móvel, scanner ao vivo, estados VALID/INVALID/REJECTED/DUPLICATE e paletização simulada foram preservados.

## Teste sugerido
1. Inicie uma OP na tela Ordens de Produção.
2. Abra Operação e selecione a linha.
3. Confira se a OP ativa aparece automaticamente (quando única).
4. Leia um QR da mesma OP: deve seguir para validação normal.
5. Tente um QR de outra OP: deve ser bloqueado informando a divergência.
6. Pause a OP: ao retornar/recarregar Operação, ela não deve aparecer como OP ativa.
