# ETAPA 6.16 — Metas, alertas e classificação dos indicadores

## Objetivo
Permitir que os limites de Disponibilidade, Performance, Qualidade e OEE sejam configurados pelo Administrador, sem valores industriais fixos no código.

## Regras
- limite geral por linha;
- limite específico por produto opcional, com prioridade sobre o limite geral da linha;
- cada indicador possui limite de **Atenção** e **Crítico**;
- valor >= Atenção: **OK**;
- valor < Atenção e >= Crítico: **ATENÇÃO**;
- valor < Crítico: **CRÍTICO**;
- sem dado: nenhuma classificação artificial é criada.

## Banco
Nova tabela `indicator_thresholds`, versionada pela migration `0007`. Alterações de limite preservam histórico por validade, seguindo o mesmo padrão das metas de produção.

## Interface
Em Configurações, os limites ficam em painéis recolhíveis. Na Dashboard, a faixa de OEE recebe classificação compacta sem criar uma nova linha vertical.
