# ETAPA 7.2 — Adaptador USB/HID preparado

Objetivo: preparar o AUTOPACKLINE para leitores USB que funcionam como teclado
(HID Keyboard), sem exigir que o equipamento físico já esteja disponível.

## Como funciona

Leitores HID normalmente enviam os caracteres do QR/barcode para o campo que
está focado e terminam a leitura com ENTER. A tela Operação agora possui uma
área própria **USB / HID**:

1. selecione Linha e OP ativa;
2. clique em **Ativar captura HID/USB**;
3. mantenha o campo de entrada focado;
4. o leitor futuro digitará o conteúdo e enviará ENTER;
5. o AUTOPACKLINE copia o valor para `Conteúdo capturado`;
6. a validação continua manual por padrão, podendo ser habilitada a validação
   automática após o ENTER.

Sem hardware, o fluxo pode ser testado colando o QR de teste no campo HID e
pressionando ENTER.

## Backend

O `ReaderGateway` aceita a origem `HID_USB` e identifica o adaptador
`HID_KEYBOARD_V1`. Essa origem usa as mesmas regras do `ScanService` já
validadas. A origem genérica `PHYSICAL` continua bloqueada, pois o modelo e o
protocolo do leitor real ainda não foram definidos.

`hardware_connected` continua `false`. A aplicação não afirma que existe um
leitor conectado quando não existe.

Não há migration de banco nesta etapa.
