# ETAPA 7.25 — Health-check operacional e autodiagnóstico

Objetivo: consolidar uma verificação automática e segura do ambiente antes de aceitar novas unidades no fluxo simulado/autônomo.

## Verificações
- Backend/API respondendo.
- MySQL acessível por `SELECT 1`.
- Motor de produção automática preparado offline.
- Simulador D700-D763 disponível sem socket físico.
- Matriz de resiliência aprovada.
- Ausência de transações pendentes bloqueantes.
- Adaptador físico mantido bloqueado como condição esperada antes do comissionamento.

## Regra de segurança
A etapa 7.25 não abre conexão Modbus física, não tenta acessar `192.168.0.2:502` e não libera a máquina real. O objetivo é preparar autodiagnóstico e bloqueio preventivo antes da fase de comissionamento.

O painel é temporário de desenvolvimento/diagnóstico e será movido para área técnica na reorganização final da interface.
