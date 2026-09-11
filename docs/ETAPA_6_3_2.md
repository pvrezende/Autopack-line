# ETAPA 6.3.2 — Ajuste final do menu recolhível

Correção visual aplicada sobre a versão 6.3.1 já validada.

## Ajuste

- O botão hambúrguer não sobrepõe mais o texto **NÚCLEO FUNCIONAL** quando o menu lateral é recolhido.
- O recuo de segurança de 58 px agora vale para **todas as telas** do sistema, e não apenas para o Dashboard.
- Mantidas integralmente as funcionalidades já aprovadas: Dashboard operacional, Operação/QR, Configurações administrativas, Rastreabilidade com filtros/exportação/impressão, usuários/perfis, auditoria e conversão de horário para `America/Manaus`.

## Atualização

Preserve o volume do MySQL. Use `docker compose down` e depois `docker compose up --build`. Não use `docker compose down -v`.
