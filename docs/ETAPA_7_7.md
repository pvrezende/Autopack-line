# ETAPA 7.7 — Retorno robusto do CLP simulado

Objetivo: consolidar o contrato de retorno operacional antes da conexão física do CLP.

- ACK (`PALLETIZE_CONFIRMED`) confirma a unidade no palete.
- NACK (`PALLETIZE_REJECTED`) devolve rejeição estruturada sem paletizar a unidade.
- Confirmação repetida da mesma unidade é bloqueada no backend como `DUPLICATE_BLOCKED`.
- O frontend bloqueia duplo clique depois de ACK aceito.
- Todas as respostas ficam auditáveis usando a tabela de auditoria já existente.
- Nenhum protocolo, IP, tag ou fabricante de CLP foi presumido.
- Sem migration nesta etapa.
