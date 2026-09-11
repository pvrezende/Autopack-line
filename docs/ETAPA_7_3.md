# ETAPA 7.3 — Diagnóstico e homologação da entrada do leitor

Objetivo: permitir conferir exatamente o conteúdo entregue pelo leitor antes de
registrar uma leitura produtiva.

A tela Operação passa a oferecer **Diagnosticar conteúdo**. O diagnóstico:

- não cria `scan_event`;
- não cria unidade de produção;
- não altera palete;
- não cria auditoria de leitura;
- identifica origem/adaptador, tamanho e quantidade de campos;
- valida o QR estruturado de 5 campos e exibe produto bruto, EAN, serial, OP e URL;
- mostra o erro de formato quando o conteúdo não segue a estrutura esperada.

Endpoint: `POST /api/v1/integrations/reader/diagnose`.

O recurso funciona com `SIMULATOR` e `HID_USB`. `PHYSICAL` permanece bloqueado
até o modelo/protocolo real do equipamento ser definido.

Não há migration nesta etapa.
