# ETAPA 7.1 — Camada de integração do leitor QR / Barcode

Objetivo: separar a origem física da leitura das regras de negócio já validadas.

Nesta etapa **não é necessário leitor físico**. O AUTOPACKLINE passa a possuir uma
camada única de entrada (`ReaderGateway`) e um adaptador `SIMULATOR_READER_V1`.
A leitura simulada percorre a mesma validação já utilizada em Operação: parser,
produto, OP, duplicidade, rastreabilidade e criação da unidade.

Endpoints:

- `GET /api/v1/integrations/reader/status`
- `POST /api/v1/integrations/reader/ingest`

O status informa explicitamente `hardware_connected=false`. A origem `PHYSICAL`
é recusada enquanto o modelo/protocolo do equipamento não for definido. Assim,
não existe protocolo USB, serial ou Ethernet inventado no código.

Quando o leitor real estiver disponível, será criado um adaptador físico que
entrega o conteúdo ao mesmo `ReaderGateway`, preservando as regras atuais.

Não há migration nesta etapa.
