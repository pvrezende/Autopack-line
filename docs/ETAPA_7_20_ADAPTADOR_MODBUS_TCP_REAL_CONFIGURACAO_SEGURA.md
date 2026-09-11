# ETAPA 7.20 — Adaptador Modbus TCP real + configuração segura

Preparação offline do transporte físico para o Delta AS228T-A. Esta etapa NÃO abre socket e NÃO tenta conectar ao IP 192.168.0.2.

## Configuração preparada
- CLP servidor: 192.168.0.2:502
- AUTOPACKLINE: cliente Modbus TCP
- mapa lógico: escrita D700-D749; leitura D750-D763
- escrita em duas fases: D704-D749 antes de D700-D703
- reconexão: ler D752/D754/D757/D758/D760/D761 antes de qualquer escrita
- feature flag `PLC_PHYSICAL_ENABLED=false` por padrão

## Gates para ativação futura
A conexão real só poderá ser habilitada após ladder D700-D763, tabelas D754/D756, IDs de receita, offset Modbus, teste ASCII AB12 e revisão do ladder estarem confirmados.
