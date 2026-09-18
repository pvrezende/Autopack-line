# ETAPA 7.34 — Correções Rev.02 e conexão segura com simulador externo

## Correções do contrato

- D705.4 e D749 agora fazem parte do payload real do codec.
- Pedido normal exige D705.4=0 e D749=0; reteste exige D705.4=1 e D749 diferente de zero.
- D754 e D756 são traduzidos pelas tabelas oficiais, incluindo o estado 20.
- O simulador interno mantém D750-D879, identidade Rev.04 e publicação do leitor.
- O parser valida UINT16, resultados, flags D802 e capacidades D777.
- O snapshot do leitor é aceito somente se D770, D777 e D800 permanecerem coerentes durante a leitura.

## Transporte do CLP-Simulator

O backend possui cliente Modbus TCP mínimo para FC03 e FC16 sem dependência
externa adicional. O perfil `EXTERNAL_CLP_SIMULATOR_MODBUS_TCP_REV02` é separado
do adaptador físico e usa, por padrão:

- `host.docker.internal:1502`, Unit ID 1;
- D700 mapeado ao holding 0;
- D750-D779 mapeado a 50-79;
- D800-D879 mapeado a 100-179.

O probe é explícito, auditado e restrito a Supervisor/Administrador. Nenhum socket
é aberto no startup. A escrita exige simultaneamente
`PLC_EXTERNAL_SIMULATOR_ENABLED=true` e
`PLC_EXTERNAL_SIMULATOR_WRITE_ENABLED=true`.

## Separação do CLP físico

As flags do simulador externo não alteram `PLC_PHYSICAL_ENABLED`,
`PLC_READ_ONLY_ENABLED` ou `PLC_WRITE_ENABLED`. A conexão física real continua
bloqueada até o fechamento dos gates de comissionamento.

## Perfil implementado no repositório CLP-Simulator

A branch `feature/autopackline-d700-d879` implementa a máquina de estados
D700-D879 nos holdings 0-179 e preserva o perfil PCM nas demais estações. O fluxo
Modbus TCP foi validado com leitura de identidade, heartbeat, escrita em duas
fases, ACK, BUSY e conclusão física simulada.

## Limite identificado no bloco bruto

O QR real documentado ultrapassa os 64 bytes reservados em D847-D878. O simulador
mantém o limite da Rev.02 e rejeita publicações maiores, evitando truncamento
silencioso. Antes do comissionamento, Automação e AUTOPACKLINE devem decidir entre
ampliar o bloco, retirar a URL do dado transportado ou publicar o bruto por outro
mecanismo auditável.
