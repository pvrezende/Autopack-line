# Adendo da interface AUTOPACKLINE x CLP - Rev. 02

Data: 17/09/2026

Este documento substitui o adendo Rev.01. Ele congela o contrato para o
desenvolvimento offline do AUTOPACKLINE e identifica o que ja foi implementado na
Rev.04 do Ladder e o que ainda depende do comissionamento.

## 1. Identificacao da revisao

| Item | Valor |
|---|---|
| Versao do protocolo | 1 em D750 |
| Revisao do Ladder | 4 em D764 |
| Data da revisao | 17/09/2026, representada por D765=2026 e D766=917 |
| Arquivo de referencia | `CLP_COMAU_rev04_autopackline.MPU` |
| POU acrescentada | `PRG_08_AUTOPACKLINE` |

A versao do protocolo permanece 1 porque nenhum endereco ou significado da
Rev.01 foi deslocado. Os novos campos ocupam a faixa que estava reservada e sao
descobertos por D777.

## 2. Definicao de D764 a D779

Todos os registradores sao UINT16 e seguem no sentido CLP para PC.

| Endereco | Nome | Significado |
|---|---|---|
| D764 | AP_LADDER_REVISION | Revisao logica do Ladder; valor 4 nesta entrega |
| D765 | AP_LADDER_BUILD_YEAR | Ano da revisao; valor 2026 |
| D766 | AP_LADDER_BUILD_MMDD | Mes e dia sem separador; valor 917 para 17/09 |
| D767 | AP_READER_ONLINE | 0 offline/nao integrado; 1 comunicando |
| D768 | AP_READER_STATE | 0 inativo; 1 ocioso; 2 trigger solicitado; 3 lendo; 4 dado pronto; 5 erro |
| D769 | AP_READER_RESULT | 0 nenhum; 1 good read; 2 no read; 3 erro de comunicacao; 4 formato invalido |
| D770 | AP_READER_SEQUENCE | Sequencia incrementada a cada trigger do leitor |
| D771 | AP_READER_DATA_LENGTH | Comprimento do dado bruto em bytes, 0 a 64 |
| D772 | AP_READER_ERROR_CODE | Codigo de erro do leitor/integracao; 0 sem erro |
| D773 | AP_READER_GOOD_COUNT | Contador de good read, com retorno apos 65535 |
| D774 | AP_READER_NOREAD_COUNT | Contador de no read, com retorno apos 65535 |
| D775 | AP_READER_TRIGGER_COUNT | Contador de triggers, com retorno apos 65535 |
| D776 | AP_READER_LAST_TIME_MS | Tempo da ultima leitura em milissegundos, saturado em 65535 |
| D777 | AP_FEATURE_FLAGS | Capacidades realmente ativas, descritas abaixo |
| D778 | AP_READER_BLOCK_START | Primeiro D do bloco do leitor; valor 800 |
| D779 | AP_READER_BLOCK_LENGTH | Tamanho do bloco do leitor em words; valor 80 |

Bits de D777:

| Bit | Nome | Significado quando igual a 1 |
|---:|---|---|
| 0 | AP_FEATURE_DASHBOARD | Interface D700..D779 ativa |
| 1 | AP_FEATURE_RETEST | D705.4 e D749 validados pelo CLP |
| 2 | AP_FEATURE_READER_STATUS | D767..D776 contem diagnostico valido do SR-1000 |
| 3 | AP_FEATURE_READER_RAW | D800..D879 contem dado bruto valido do SR-1000 |
| 4 | AP_FEATURE_READER_PARSED | Campos serial/EAN/OP/modelo foram separados pelo CLP |

Na primeira geracao da Rev.04, D777=3. Isso informa que dashboard e reteste
estao implementados, mas o SR-1000 ainda nao foi mapeado no hardware EtherNet/IP
do ISPSoft. D767..D776 retornam zero ate essa integracao ser concluida. O software
nao deve tratar esses zeros como uma leitura do scanner.

## 3. Bloco do SR-1000

O bloco do leitor fica separado em D800..D879 para nao reduzir os tamanhos dos
campos ja publicados em D700..D749. Todos os campos sao somente leitura para o
AUTOPACKLINE.

| Endereco | Nome | Tipo | Conteudo |
|---|---|---|---|
| D800 | READER_DATA_SEQUENCE | UINT16 | Copia da sequencia da leitura publicada |
| D801 | READER_DATA_RESULT | UINT16 | Mesmo dominio de D769 |
| D802 | READER_PAYLOAD_FLAGS | WORD | bit0 serial; bit1 EAN; bit2 OP; bit3 modelo; bit4 bruto |
| D803 | READER_SERIAL_LENGTH | UINT16 | 0 a 32 caracteres |
| D804..D819 | READER_SERIAL | ASCII[32] | Serial, dois caracteres por word |
| D820 | READER_EAN_LENGTH | UINT16 | 0 a 14 caracteres |
| D821..D827 | READER_EAN | ASCII[14] | EAN, dois caracteres por word |
| D828 | READER_OP_LENGTH | UINT16 | 0 a 16 caracteres |
| D829..D836 | READER_OP | ASCII[16] | Ordem de producao |
| D837 | READER_MODEL_LENGTH | UINT16 | 0 a 16 caracteres |
| D838..D845 | READER_MODEL | ASCII[16] | Codigo do modelo |
| D846 | READER_RAW_LENGTH | UINT16 | 0 a 64 caracteres |
| D847..D878 | READER_RAW_DATA | ASCII[64] | Conteudo bruto lido pelo SR-1000 |
| D879 | READER_DATA_ERROR | UINT16 | Codigo de erro associado a leitura |

O dado bruto e a fonte de auditoria. Os campos separados somente sao validos
quando o respectivo bit de D802 e o bit 4 de D777 estiverem ativos. A regra de
separacao depende do formato final configurado no SR-1000 e ainda sera validada
com codigos reais.

## 4. Codificacao de texto e byte order

O formato definido e AB12:

- dois caracteres ASCII por registrador;
- o primeiro caractere ocupa o byte alto;
- o segundo caractere ocupa o byte baixo;
- exemplo: `AB` e transmitido como word `0x4142`;
- texto impar termina com byte baixo `0x00`;
- os registradores restantes do campo devem ser zerados.

O software deve manter a ordem configuravel ate o primeiro teste Modbus, pois
algumas bibliotecas apresentam os bytes de uma word em ordem diferente da ordem
do protocolo.

## 5. Reteste na Rev.04

Confirmado e implementado:

- D705 bit 4 = RETEST_AUTHORIZED;
- D749 = ORIGINAL_REQUEST_SEQUENCE;
- pedido normal exige D705.4=0 e D749=0;
- reteste exige D705.4=1 e D749 diferente de zero;
- combinacao incoerente recebe D753=2 e nao inicia movimento;
- uma unidade aceita recebe ACK e a sequencia original e preservada internamente
  pelo CLP para diagnostico.

O CLP valida a estrutura do pedido, mas o AUTOPACKLINE continua responsavel por
verificar o historico do serial, a existencia da tentativa original, permissao do
usuario e limite de tentativas.

## 6. Rede e Modbus TCP

| Equipamento | Definicao |
|---|---|
| CLP Delta AS228T-A | 192.168.29.5/24, confirmado online |
| SR-1000 | 192.168.29.8/24, confirmado online |
| PC AUTOPACKLINE | 192.168.29.10/24 reservado; confirmar com TI antes da instalacao |
| Porta Modbus TCP | TCP 502; porta acessivel no CLP |
| Unit ID | 1, confirmado por leitura Modbus TCP em 17/09/2026 |
| Enderecos canonicos | Dispositivos Delta D700..D879 |
| Offset PDU confirmado | Endereco N acessa DN; a leitura do endereco 301 retornou D301=900 |
| Byte order numerico | Confirmado: 0x0384 foi recebido como 900 |
| Byte order de texto | AB12 definido; confirmar com texto conhecido no primeiro teste |
| Gateway da rede industrial | Nenhum por padrao |

Ja podem ser usados no desenvolvimento: IP do CLP, IP do scanner, IP reservado do
PC, porta 502, Unit ID 1, endereco PDU direto e AB12. Dependem do comissionamento:
aceite da TI para o IP do PC, ajuste 0-based/1-based da API utilizada, confirmacao
pratica do byte order de texto e porta fisica do switch.

Evidencia da leitura sem escrita em 17/09/2026: PDU 301 retornou 900 e PDU 302
retornou 123, valores coerentes com D301/D302. Isso tambem indica que a maquina
estava em estado de falha 900, codigo 123, no instante do teste.

O computador de producao deve ter uma interface dedicada a rede 192.168.29.0/24.
Se tambem usar a rede corporativa, deve utilizar outra interface e as regras de
roteamento/firewall da TI.

## 7. Fluxo do SR-1000 e AUTOPACKLINE

1. O CLP comanda o trigger do SR-1000 por EtherNet/IP.
2. O CLP publica o resultado e o dado bruto em D767..D879.
3. O AUTOPACKLINE detecta uma nova leitura pela mudanca de D770/D800.
4. O AUTOPACKLINE preserva o dado bruto, interpreta os campos e valida cadastro,
   duplicidade, receita e regras de qualidade.
5. O AUTOPACKLINE grava D704..D749 e depois D700..D703.
6. O CLP responde em D752/D753 e so inicia o ciclo no estado D754=50.

O AUTOPACKLINE nao aciona o leitor, robo, valvulas, motores nem funcoes de
seguranca diretamente.

## 8. Autorizacao de reteste e retrabalho

A Automacao confirma a implementacao tecnica, mas a regra de negocio precisa ser
aprovada formalmente por Processo e Qualidade. Proposta para o desenvolvimento:

- perfis autorizadores: Qualidade e Supervisor de Producao;
- operador comum nao autoriza;
- usuario, data/hora e motivo controlado sao obrigatorios;
- limite deve ser parametrizavel; usar 2 retestes como valor provisorio apenas em
  simulacao, sem liberar producao ate a aprovacao;
- unidade ja depositada nao entra como reteste comum;
- unidade depositada exige ordem de retrabalho, nova instancia de processo e
  vinculo imutavel com a unidade e o ciclo originais.

O responsavel nominal por aprovar os perfis, motivos e limite ainda deve ser
indicado pela lideranca de Processo/Qualidade.

## 9. Itens para o AUTOPACKLINE preparar antes do comissionamento

- cliente Modbus com IP, Unit ID, offset e byte order configuraveis;
- simulador dos blocos D700..D779 e D800..D879;
- persistencia atomica de REQUEST_SEQUENCE e ORIGINAL_REQUEST_SEQUENCE;
- reconciliacao por D752, D760 e D761 depois de reconexao;
- parser configuravel do dado bruto do leitor;
- historico imutavel de leitura, tentativa, autorizacao, ACK e deposito;
- controle de perfis, motivo e limite de reteste;
- fluxo separado de retrabalho;
- telas de saude para CLP, leitor, heartbeat e versoes D750/D764..D766;
- exportacao de log com horario, serial, leitura bruta, receita e sequencias;
- testes automatizados de duplicidade, timeout, no read, queda de rede, reinicio
  do PC, reinicio do CLP e resposta repetida.

## 10. Estado da Rev.04

O arquivo foi gerado e validado estruturalmente fora do ISPSoft. A validacao local
confirmou 8 POUs, 221 redes e preservacao do mapa D100/D200. Antes de download no
CLP ainda sao obrigatorios:

1. abrir/importar no ISPSoft e compilar sem erros;
2. comparar o programa online com a base usada na Rev.04;
3. executar teste de mesa sem movimento, com saidas bloqueadas;
4. validar heartbeat, ACK/NACK e estados por monitoramento;
5. somente depois habilitar o inicio de ciclo pelo comando do AUTOPACKLINE;
6. configurar e testar os assemblies EtherNet/IP do SR-1000;
7. apos o teste do leitor, ativar em D777 apenas as capacidades comprovadas.
