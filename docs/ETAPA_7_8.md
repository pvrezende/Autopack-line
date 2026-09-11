# ETAPA 7.8 — Sincronização persistida do ciclo CLP

Objetivo: impedir perda de contexto entre leitura válida e confirmação do CLP, além de bloquear sinais fora da sequência operacional.

## O que foi incluído

- Novo endpoint `GET /api/v1/integrations/plc/cycle` para consultar no MySQL o estado real de uma unidade.
- Estado `AWAITING_PLC` quando a leitura válida existe, mas a unidade ainda não foi paletizada.
- Estado `PALLETIZED` quando a confirmação já foi gravada, incluindo o palete recuperado do banco.
- Detecção de `CONTEXT_MISMATCH` quando a unidade pertence a outra linha.
- Bloqueio `OUT_OF_SEQUENCE` para ACK/NACK enviados em uma ordem inválida.
- Após NACK, a unidade continua aguardando o CLP e pode receber um novo ACK.
- O frontend preserva a unidade atual no `sessionStorage` e recupera o ciclo depois de atualizar a página.
- Enquanto houver uma unidade `AWAITING_PLC`, uma nova validação é bloqueada no frontend para evitar perda de sequência.
- O painel de sincronização fica dentro do accordion do CLP, preservando a regra de interface compacta/responsiva.

## Persistência

Nenhuma tabela nova foi criada. O estado é reconstruído usando `production_units`, `pallet_items`, `pallets` e `production_orders`, que já são a fonte de verdade do processo.

## Hardware

O modo continua simulado (`SIMULATOR_PLC_V1`). Nenhum protocolo, IP, tag, fabricante ou endereço físico foi presumido.

## Teste principal

1. Faça uma leitura nova e obtenha `VALID`.
2. Verifique `AGUARDANDO RETORNO DO CLP`.
3. Atualize a página com `Ctrl + F5` antes do ACK.
4. O sistema deve restaurar a mesma unidade e continuar aguardando o CLP.
5. Simule NACK: o estado deve continuar aguardando retorno.
6. Depois envie ACK: a unidade deve ser paletizada e o estado deve virar `UNIDADE JÁ SINCRONIZADA`.
7. Atualize a página novamente: o estado confirmado e o palete devem ser recuperados do MySQL.

Sem migration nesta etapa.
