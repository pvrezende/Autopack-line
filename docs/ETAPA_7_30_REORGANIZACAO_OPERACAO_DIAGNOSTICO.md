# ETAPA 7.30 — Reorganização profissional da interface

## Objetivo

Separar a operação diária da fábrica das ferramentas técnicas usadas durante o desenvolvimento, diagnóstico e futuro comissionamento.

## Interface operacional

- A tela Operação passa a exibir somente contexto da linha/OP, leitura QR/Barcode, resultado, progresso, palete e retorno operacional do CLP simulado.
- Os painéis técnicos Modbus, resiliência, health-check, evidências e comissionamento deixam de aparecer para o operador.
- Identificadores de etapas deixam de ocupar a navegação operacional.
- Os cards de infraestrutura ficam restritos à área técnica.

## Manutenção e Diagnóstico

- Nova entrada de menu disponível para Supervisor e Administrador.
- Preserva contrato, codec, handshake, supervisão, reconciliação, simulador, adaptador físico, motor automático, resiliência, logs, health-check, gate, plano, evidências e ensaio offline.
- Nenhuma regra industrial ou endpoint existente é removido.

## Perfis

- Operador: Dashboard e Operação.
- Supervisor: Dashboard, Indicadores, Operação, OPs, Jornada, Rastreabilidade e Diagnóstico.
- Administrador: acesso completo.
- O cadastro de usuário passa a prevenir preenchimento automático das credenciais administrativas.

## Segurança

- `PLC_PHYSICAL_ENABLED=false` permanece como padrão seguro.
- Nenhum socket Modbus físico é aberto por esta reorganização.
- Simulador, persistência, reconciliação e auditoria são preservados.

## Responsividade

A operação permanece compacta e utilizável em notebook/monitor com navegador em 100%. Conteúdo técnico continua em accordions na área dedicada.
