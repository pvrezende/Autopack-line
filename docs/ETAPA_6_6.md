# ETAPA 6.6 — Ordens de Produção (OP)

## Objetivo
Transformar a OP em entidade operacional real do AUTOPACKLINE, vinculando produto, linha, quantidade planejada, leituras e paletes.

## Implementado
- Nova tela **Ordens de Produção** disponível no menu.
- Administrador: cadastrar e editar OP, definir produto, linha, lote, quantidade planejada e observações; também pode cancelar.
- Supervisor/Administrador: iniciar, pausar e finalizar OP.
- Operador: consulta das OPs e do progresso, sem permissão administrativa.
- Paginação de 6 OPs por página e filtros por status, linha, produto e número da OP.
- Indicadores de quantidade produzida, progresso percentual e paletes abertos/completos.
- Auditoria das ações de criação, edição, início, pausa, conclusão e cancelamento.
- Migração 0005 preserva OPs históricas e tenta inferir a linha a partir das leituras já existentes.
- A leitura QR passa a exigir que a OP exista, corresponda ao produto/linha e esteja **ATIVA**.

## Estados
- `OPEN`: cadastrada, aguardando início.
- `ACTIVE`: liberada para leituras.
- `PAUSED`: temporariamente bloqueada para leituras.
- `COMPLETED`: concluída.
- `CANCELLED`: cancelada.

## Regra importante
Uma OP com palete aberto não pode ser concluída ou cancelada. Isso evita encerrar a ordem deixando material em montagem.

## Teste sugerido
1. Acesse **Ordens de Produção** como Administrador.
2. Localize a OP histórica do QR (`000001275033`) ou crie uma nova.
3. Garanta que produto e linha estejam corretos.
4. Clique em **Iniciar**.
5. Vá para **Operação** e faça a leitura do QR.
6. Pause a OP e repita com outro serial: a leitura deve ser `REJECTED` por OP não ativa.
7. Reative a OP e repita o teste.
