# ETAPA 7.19 — Simulador completo do CLP D700–D763

## Objetivo
Exercitar offline o contrato lógico enviado pela automação sem abrir conexão com a máquina real.

## Implementado
- Memória lógica D700–D749 (PC → CLP) e D750–D763 (CLP → PC).
- Escrita em duas fases: D704–D749 antes de D700–D703.
- ACK por D752/D753, READY/BUSY/FAULT em D755, heartbeat D751.
- Conclusão física simulada por D760/D761 e origem D762=1.
- Contagem/capacidade do palete em D757–D759.
- Sequência duplicada, máquina ocupada, falha, rejeição e aborto.
- Reuso do codec real da etapa 7.15 para montar/decodear registradores.
- Testes automatizados do simulador.

## Segurança de escopo
Esta etapa NÃO abre socket Modbus TCP e NÃO conecta em 192.168.0.2. Endereço/offset físico, byte order AB12 e revisão do ladder continuam para comissionamento. D754, D756 e IDs reais de receita continuam dependentes das tabelas da automação.

## Resultado esperado
O software passa a possuir um CLP lógico reproduzível para as próximas etapas offline, sem inventar os itens ainda pendentes do Fleidimir/comissionamento.
