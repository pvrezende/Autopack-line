# ETAPA 7.35 — Runtime Modbus com CLP-Simulator

## Entrega

- polling operacional iniciado pela tela Operação a cada 250 ms;
- heartbeat do PC escrito em D701 a cada segundo;
- snapshot consistente de D750–D779 e D800–D879;
- ingestão automática do dado bruto do leitor sem duplicar D770 já processado;
- receita Modbus 1–8 vinculada ao produto e protegida por flag de liberação;
- persistência de `REQUEST_SEQUENCE`, payload e leitura bruta antes do primeiro write;
- escrita em duas fases: D704–D749 e depois D700–D703;
- reconciliação de ACK, conclusão D760/D761, paletização idempotente e D703=0;
- exportação CSV das transações Modbus;
- parser de QR configurável para resolver o limite de 64 bytes do bloco bruto;
- limite provisório de retestes e ordem separada de retrabalho para unidade depositada.

## Separação física

O runtime desta etapa usa exclusivamente `PLC_EXTERNAL_SIMULATOR_*`. O endereço
do Delta real permanece sob `PLC_PHYSICAL_*`, com socket e escrita desabilitados.
Os gates de compilação ISPSoft, offset, AB12, rede, EtherNet/IP e autorização
ponta a ponta agora são confirmações explícitas, todas falsas por padrão.

## Ensaio executado

O AUTOPACKLINE conectou ao CLP-Simulator em `host.docker.internal:1502`, confirmou
D750=1/D764=4/D765=2026/D766=917, leu D754=50 e escreveu D701. A execução produtiva
com leitura, receita e OP exige dados operacionais cadastrados e uma leitura
publicada no simulador.

## Próxima etapa

Corrigir no CLP-Simulator a retransmissão idempotente, duplicidade por serial,
supervisão de D701, estados/falhas completos, `NO_READ` sem payload e reset de
interface sem apagar contagens. Depois repetir a matriz de resiliência e fechar
os gates de comissionamento em modo somente leitura antes de autorizar escrita.
