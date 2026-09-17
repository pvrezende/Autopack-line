# ETAPA 7.31 — Fundação controlada de reteste offline

## Objetivo

Preparar o AUTOPACKLINE para manter várias tentativas vinculadas à mesma unidade, sem remover a proteção contra duplicidade e sem inventar as regras definitivas do processo da Elgin.

## Implementado

- migration `0009` com a tabela `retest_attempts`;
- uma unidade continua sendo identificada de forma única pelo serial;
- tentativas numeradas e vinculadas à unidade;
- decisões simuladas `REJECTED` e `APPROVED`;
- origem, motivo, autorização, usuário, data/hora e detalhes da tentativa;
- chave de idempotência para impedir duplicação da mesma tentativa;
- histórico consultável pelo serial;
- auditoria `RETEST_SIMULATED`;
- painel compacto e recolhível em **Manutenção e Diagnóstico**;
- correção do teste do dashboard para o contrato atual com `cumulative_quantity`.

## Segurança

Configuração padrão:

```env
RETEST_ENABLED=false
RETEST_SIMULATOR_ENABLED=true
```

Enquanto `RETEST_ENABLED=false`, o sistema não aceita uma regra real vinda de MES, CLP ou operador. A simulação:

- não muda o estado da unidade;
- não aumenta produção;
- não adiciona caixa ao palete;
- não abre socket Modbus;
- não libera automaticamente um reteste real;
- exige rejeição anterior e autorização explícita para simular aprovação;
- retorna a tentativa existente quando a chave de idempotência é repetida.

## APIs

- `GET /api/v1/retests/status`
- `GET /api/v1/retests?serial_number=...`
- `POST /api/v1/retests/simulate`

Todas exigem perfil `SUPERVISOR` ou `ADMIN`.

## Definições externas ainda pendentes

- origem oficial da aprovação/reprovação;
- contrato e disponibilidade do MES;
- regra de autorização de reteste;
- limite de tentativas;
- significado dos motivos e códigos;
- impacto definitivo em produção e paletização.

## Comissionamento

Nenhuma conexão com o CLP físico é realizada nesta etapa. `PLC_PHYSICAL_ENABLED` permanece bloqueado e os parâmetros físicos continuam sujeitos à validação da automação.
