# ETAPA 7.33.1 — Correção de consistência do contrato Rev.02

## Objetivo

Eliminar informações técnicas obsoletas que ainda apareciam nos diagnósticos anteriores à confirmação da Rev.02 e da Ladder Rev.04.

## Corrigido

- contrato principal atualizado para `D700–D749`, `D750–D779` e `D800–D879`;
- rede atualizada para CLP `192.168.29.5`, PC `192.168.29.10`, porta `502` e Unit ID `1`;
- D705.4 e D749 documentados como autorização de reteste e sequência original;
- D754, D756 e receitas deixam de aparecer como pendentes da automação;
- identidade Rev.04 adicionada ao contrato: D750=1, D764=4, D765=2026 e D766=917;
- diagnósticos, supervisão, simulador, gate e plano de comissionamento alinhados à Rev.02;
- interface deixa de mostrar “PROPOSTA · LADDER PENDENTE” e IP antigo.

## Segurança preservada

Esta correção não abre socket e não habilita escrita física. A comunicação real continua bloqueada até:

1. abrir, compilar e comparar a Rev.04 no ISPSoft;
2. validar offset 0/1 e byte order com `AB12`;
3. confirmar porta física e rede da máquina;
4. validar a integração EtherNet/IP do SR-1000 e as capacidades em D777;
5. executar a primeira comunicação em modo somente leitura, com autorização de comissionamento.
