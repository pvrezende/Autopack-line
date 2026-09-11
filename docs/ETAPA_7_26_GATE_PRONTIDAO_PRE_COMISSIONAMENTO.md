# ETAPA 7.26 — Gate de prontidão pré-comissionamento

## Objetivo
Consolidar em um único diagnóstico tudo que já está pronto no AUTOPACKLINE, o que ainda depende da automação e o que só pode ser validado presencialmente no comissionamento.

## Regras
- Nenhum socket Modbus físico é aberto nesta etapa.
- O desenvolvimento offline continua permitido somente se o health-check estiver saudável.
- O comissionamento real permanece bloqueado enquanto houver pendências de ladder, tabelas/IDs da automação ou validações exclusivas de fábrica.
- O adaptador físico bloqueado é considerado condição segura e esperada.

## Gate atual
O software diferencia explicitamente:
1. pronto para continuar offline;
2. pendente da automação;
3. pendente exclusivamente do comissionamento;
4. condição de segurança que impede conexão prematura.

Esta etapa não altera o contrato Modbus nem libera `192.168.0.2:502`.
