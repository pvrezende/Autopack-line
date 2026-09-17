# Adendo da interface AUTOPACKLINE x CLP - Rev. 01

Data: 17/09/2026

Este documento complementa a Rev.00 e congela as definicoes necessarias para o
desenvolvimento offline do AUTOPACKLINE. Os enderecos D700..D779 ainda precisam
ser implementados e testados no Ladder antes do uso na maquina.

## 1. Versoes

| Item | Definicao |
|---|---|
| Versao do protocolo AUTOPACKLINE | 1, retornada em D750 |
| Ladder oficial de referencia | `CLP_COMAU_rev03_heartbeat_as.MPU` |
| Revisao logica do Ladder | Rev.03, gerada em 16/09/2026 |
| Proxima revisao prevista | Rev.04, com D700..D779 e interface do scanner |

O arquivo online do CLP deve ser comparado com a Rev.03 antes de gerar a Rev.04.
A revisao do Ladder ainda nao possui um registrador proprio no contrato Modbus.

## 2. Estados de D754

D754 deve espelhar o estado principal D301 do CLP.

| D754 | Nome | Descricao |
|---:|---|---|
| 0 | INIT | Inicializacao; aguarda reset/liberacao para ir ao estado 10 |
| 10 | WAIT_PERMISSIVES | Aguarda seguranca, ar, automatico e receita confirmada |
| 20 | WAIT_ROBOT | Reservado para espera/home do robo; nao usado na Rev.03 |
| 30 | CHECK_PALLET | Verifica palete presente e posicionado |
| 40 | FEED_EMPTY_PALLET | Alimentacao de palete vazio em andamento |
| 50 | READY | Celula pronta para iniciar uma unidade |
| 60 | WAIT_ROBOT_START_ACK | Aguarda reconhecimento de partida do Comau |
| 65 | WAIT_TAPE_ENTRY | Aguarda caixa entrar na aplicadora |
| 66 | MOVE_TAPE | Move a caixa; a subfase fica em D310 |
| 67 | APPLY_TAPE | Executa aplicacao; a subfase fica em D310 |
| 80 | WAIT_ROBOT_PICK | Aguarda confirmacao de coleta do Comau |
| 90 | WAIT_ROBOT_PLACE | Aguarda confirmacao de deposito do Comau |
| 100 | PALLET_COMPLETE | Palete completo, aguardando liberacao/retirada |
| 110 | DISCHARGE_PALLET | Descarga automatica do palete em andamento |
| 900 | FAULT | Falha ativa; movimento de processo bloqueado |

Resumo para a interface:

- READY: D754 = 50;
- BUSY com uma unidade: D754 = 60, 65, 66, 67, 80 ou 90;
- troca de palete ativa: D754 = 40 ou 110;
- falha: D754 = 900;
- demais estados: parada/espera controlada.

## 3. Codigos de falha de D756

D756 deve espelhar D302.

| D756 | Falha |
|---:|---|
| 0 | Sem falha |
| 100 | Rele/circuito de seguranca nao confirmado |
| 110 | Pressao de ar baixa |
| 120 | Protecao do motor do alimentador aberta |
| 121 | Protecao da esteira de entrada aberta |
| 122 | Protecao da esteira da fita aberta |
| 123 | Protecao da esteira de descarga aberta |
| 130 | Falha da aplicadora de fita |
| 140 | Falha informada pelo Comau |
| 141 | Comau perdeu READY durante o ciclo |
| 150 | Sensores das duas posicoes de fita ativos simultaneamente |
| 151 | Palete posicionado sem confirmacao de presenca |
| 160 | Receita perdeu confirmacao durante o ciclo |
| 410 | Timeout na alimentacao do palete |
| 610 | Timeout no reconhecimento de partida do Comau |
| 650 | Timeout na entrada da aplicadora |
| 660 | Timeout no movimento da esteira da fita |
| 670 | Timeout na aplicacao de fita |
| 810 | Timeout na coleta do robo |
| 910 | Timeout no deposito do robo |
| 1110 | Timeout na descarga do palete |
| 9999 | Estado interno invalido, reservado para diagnostico |

Quando D756 = 140, o detalhe da falha do robo deve ser consultado no codigo
retornado pelo Comau em D202. A tabela de codigos do Comau ainda sera ampliada.

## 4. IDs das receitas

Os IDs abaixo ficam reservados desde ja. Receita reservada nao significa receita
liberada para movimento.

| ID | Codigo do produto | Dimensao de embalagem | Arranjo | Passo Z | Estado |
|---:|---|---|---|---:|---|
| 1 | 45HDFE09C2CA | 775 x 315 x 515 mm | 6 x 3 = 18 | 500 mm efetivos | Movimento atual validado |
| 2 | 45HDFE12C2CA | 775 x 315 x 515 mm | 6 x 3 = 18 | 500 mm efetivos | Compartilha geometria da receita 1 |
| 3 | 45HDFE18C2CA | 825 x 380 x 570 mm | 6 x 2 = 12 | 575 mm efetivos | Pendente teste fisico |
| 4 | 45HDFE24C2CA | 915 x 390 x 670 mm | A definir | A definir | Nao liberada |
| 5 | 45HDFE30C2CA | 933 x 422 x 715 mm | 4 x 2 = 8 | 720 mm efetivos | Pontos ainda nao ensinados |
| 6 | 45HDFE36C2CA | 933 x 422 x 715 mm | 4 x 2 = 8 | 720 mm efetivos | Compartilha geometria da receita 5 |
| 7 | HGFE36C2CA | 1020 x 430 x 770 mm | A definir | A definir | Nao liberada |
| 8 | HGQE36C2CA | 1020 x 430 x 770 mm | A definir | A definir | Nao liberada |

Para o contrato Modbus:

- D704 recebe um desses IDs;
- D763 devolve o ID efetivamente ativo;
- receitas 4, 7 e 8 devem receber NACK/dados invalidos ate serem liberadas;
- receitas 3, 5 e 6 somente devem ser liberadas depois do teste fisico;
- o dashboard pode cadastrar todos os IDs, exibindo o status de liberacao.

## 5. Inicializacao e reset

### 5.1 Inicializacao da maquina

1. O CLP inicia em D301/D754 = 0.
2. As saidas de processo permanecem em estado seguro.
3. O operador remove as causas de seguranca e confirma pressao de ar.
4. Um reset local autorizado leva a maquina ao estado 10.
5. O CLP valida a receita e o eco do Comau.
6. Com palete, Comau e permissivos prontos, a maquina chega ao estado 50.
7. Somente no estado 50 o AUTOPACKLINE pode solicitar uma nova unidade.

Nao deve existir partida automatica apenas pelo retorno de energia ou rede.

### 5.2 Inicializacao da interface AUTOPACKLINE

1. Conectar ao CLP por Modbus TCP.
2. Ler D750..D763 antes de escrever.
3. Confirmar D750 = 1.
4. Recuperar do banco o ultimo REQUEST_SEQUENCE pendente.
5. Comparar o pendente com D752, D760 e D761.
6. Iniciar/incrementar o heartbeat D701 a cada segundo.
7. Usar AP_COMMAND = 4 somente para solicitar sincronizacao da interface.
8. Nao enviar nova unidade antes de resolver a sequencia pendente.

### 5.3 Reset

- O reset de falha da maquina e local, pela IHM/CLP, depois da remocao da causa.
- O dashboard nao comanda diretamente reset de seguranca, motores, valvulas ou robo.
- AP_COMMAND = 3 reseta somente o handshake da interface AUTOPACKLINE quando nao
  houver unidade aceita/em processamento.
- O reset de interface nao apaga historico, contagem do palete nem sequencias ja
  concluidas.
- Depois do reset da maquina, D756 volta a zero e D754 volta a 10.

## 6. Regra de duplicidade e reteste autorizado

O identificador de transporte e REQUEST_SEQUENCE. O identificador do produto e o
SERIAL. Eles nao devem ser tratados como a mesma coisa.

### 6.1 Primeira passagem reprovada

1. O AUTOPACKLINE registra a tentativa com serial, codigo lido, data/hora, motivo
   da reprovacao e REQUEST_SEQUENCE.
2. A unidade nao e liberada para o ciclo de paletizacao.
3. Pode ser enviado AP_COMMAND = 2 para registrar/sincronizar a rejeicao, sem
   movimentar a maquina.
4. O historico da tentativa permanece imutavel.

### 6.2 Reteste

Para destravar o desenvolvimento, fica reservado:

- D705 bit 4 = RETEST_AUTHORIZED;
- D749 = ORIGINAL_REQUEST_SEQUENCE, zero na primeira passagem e preenchido no
  reteste com a sequencia da tentativa original.

No reteste autorizado:

1. O mesmo SERIAL recebe um novo REQUEST_SEQUENCE.
2. O dashboard marca D705.4 = 1.
3. D749 referencia a primeira tentativa rejeitada.
4. O CLP/dashboard preservam as duas tentativas e as vinculam ao mesmo SERIAL.
5. A nova tentativa pode ser aceita se a original nao tiver sido depositada.

### 6.3 Regras de idempotencia

- Mesmo REQUEST_SEQUENCE e mesmo payload: retransmissao; devolver a resposta ja
  registrada, sem criar novo ciclo ou novo historico.
- Mesmo REQUEST_SEQUENCE com payload diferente: rejeitar como erro de protocolo.
- Novo REQUEST_SEQUENCE com SERIAL ja visto, sem reteste autorizado: resultado 3,
  duplicidade.
- Novo REQUEST_SEQUENCE com SERIAL ja visto, D705.4 = 1 e D749 valido: reteste
  permitido, mantendo o vinculo historico.
- SERIAL ja depositado/concluido nao pode voltar como reteste comum. Exige fluxo
  separado de retrabalho autorizado, ainda nao definido.

A pessoa/perfil que autoriza o reteste ainda deve ser confirmada por Processo ou
Qualidade. Para o software, prever usuario, data/hora e motivo obrigatorios.

## 7. Conexao entre PC, leitor e CLP

Arquitetura definida:

```text
SR-1000 -- EtherNet/IP --> CLP Delta AS228T-A
                               |
                               +-- Modbus TCP porta 502 --> PC AUTOPACKLINE
                               |
                               +-- interface existente --> Comau C5G
```

- O CLP sera o controlador de trigger e resultado do SR-1000.
- O AUTOPACKLINE nao comandara o leitor diretamente em producao.
- O PC recebera do CLP o resultado/identificacao necessarios ao handshake.
- Acesso direto do PC ao SR-1000 fica restrito a configuracao e diagnostico.
- IP atual do SR-1000: `192.168.29.8/24`.
- IP atual do EB80: `192.168.29.7/24`.
- IP do scanner EtherNet/IP NETX do Comau: `192.168.29.9/24`.
- O IP online do CLP e o IP definitivo do PC ainda precisam ser confirmados.
- Se o CLP nao estiver na rede `192.168.29.0/24`, sera necessario alterar o IP do
  SR-1000 ou definir uma interface/rota industrial aprovada. Nao presumir roteamento.

## 8. O que pode avancar offline

O desenvolvedor do AUTOPACKLINE pode implementar agora:

- cliente Modbus TCP e mock do bloco D700..D779;
- polling de 250 ms e heartbeat de 1 s;
- maquina de estados baseada em D754/D755;
- tabela de falhas D756;
- cadastro dos IDs 1..8 e status de liberacao;
- persistencia de REQUEST_SEQUENCE;
- ACK/NACK e idempotencia;
- historico de tentativas e reteste autorizado;
- reconexao e reconciliacao usando D752/D760/D761;
- telas de estado, unidade atual, palete, falha e comunicacao;
- testes automatizados de timeout, duplicidade e queda de conexao.

## 9. Dependencias de campo

Permanecem dependentes da maquina:

- implementar D700..D779 no Ladder Rev.04;
- confirmar IP do CLP, Unit ID e offset Modbus;
- confirmar byte order de palavras e textos;
- integrar SR-1000 ao CLP e confirmar assemblies/tamanho dos dados;
- medir os tempos do leitor e validar good read/no read;
- validar os estados e falhas durante o ciclo real;
- confirmar a fonte final de PLACE_COMPLETE;
- definir o mecanismo fisico da peca rejeitada;
- aprovar por Processo/Qualidade quem autoriza reteste e retrabalho;
- executar teste ponta a ponta com uma unidade e depois com repeticao.

## 10. Responsabilidades

- Automacao/CLP/robo: confirmar estados, falhas, registros, receita, scanner e
  comportamento da maquina.
- AUTOPACKLINE: comunicacao, persistencia, idempotencia, banco, telas e logs.
- Processo/Qualidade: regra de reprovacao, autorizacao de reteste e retrabalho.
- TI: IPs, switch, segmentacao, firewall, usuarios e backup.
- Seguranca da maquina: permissivos e funcoes seguras; o dashboard nao substitui
  nenhuma delas.
