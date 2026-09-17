# ETAPA 7.33 — Contrato Modbus Rev.02 e preparação física segura

## Entregue

- Referência oficial `ADENDO_INTERFACE_AUTOPACKLINE_REV02_2026-09-17`.
- Identidade esperada: D750=1, D764=4, D765=2026 e D766=917.
- Mapas D700–D749, D750–D779 e bloco do leitor D800–D879.
- Rede parametrizada: CLP 192.168.29.5, PC 192.168.29.10, porta 502 e Unit ID 1.
- Offset e byte order configuráveis; exemplo AB12 em HIGH_LOW (`0x4142`, `0x3132`).
- Estados oficiais, receitas, feature flags D777 e parser completo do bloco do leitor.
- Reteste por D705.4 e D749 documentado.
- Tela profissional de diagnóstico Rev.02 e gates de comissionamento.
- Conexão física e leitura real permanecem desabilitadas por padrão.

## Segurança

Esta etapa não abre socket Modbus e não escreve na máquina. A ativação física depende da compilação/validação da Rev.04, aceite da TI, validação de offset/byte order e integração EtherNet/IP do SR-1000.
