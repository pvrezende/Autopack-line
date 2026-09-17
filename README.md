# AUTOPACKLINE — ETAPA 6

Núcleo funcional do software de rastreabilidade e paletização automatizada.

## Atualização mais recente — ETAPA 7.32

Consolidação profissional do reteste offline, sem ativar MES, CLP físico ou qualquer alteração na produção:

- busca de unidades por serial, OP ou modelo diretamente pela interface;
- exibição do produto, ordem de produção e estado preservado antes da simulação;
- histórico de tentativas traduzido e auditável;
- confirmação explícita antes de reprovar ou aprovar;
- bloqueio visual e no backend de aprovação sem reprovação anterior;
- proteção contra reutilização indevida de chave de idempotência;
- registros de auditoria para buscas, consultas e simulações;
- accordion identificado por `+`/`−`, com layout responsivo;
- operação real, produção, paletes, MES e socket físico permanecem bloqueados.

## Stack

- Frontend: React + TypeScript + Vite
- Backend: Python 3.12 + FastAPI
- ORM: SQLAlchemy 2
- Migrations: Alembic
- Banco: MySQL 8.4
- Infraestrutura: Docker Compose

## Estado atual

A ETAPA 5 (infraestrutura) foi validada em Windows 11 com Docker/WSL2. Esta entrega adiciona o núcleo funcional da ETAPA 6 sem alterar as integrações físicas ainda indefinidas.

Funcionalidades incluídas:

- cadastro de produtos;
- cadastro de linhas;
- quantidade máxima por palete configurável por produto + linha;
- histórico das configurações de quantidade;
- metas de produção configuráveis;
- ordens de produção locais;
- unidades rastreadas por número de série;
- parser do QR real delimitado por `;`;
- validação de EAN-13;
- registro de toda leitura (válida ou não);
- bloqueio de serial duplicado;
- simulação de confirmação de paletização separada da leitura;
- criação automática de palete técnico quando necessário;
- contagem de caixas e fechamento do palete ao atingir a configuração;
- histórico de leituras e paletes;
- dashboard inicial com dados reais do MySQL;
- espera estável do MySQL antes de executar migrations, reduzindo erros de startup.

Ainda **não** estão conectados: leitor físico, CLP/robô, MES, totem ou impressora.

## Regra importante de configuração

Quantidade por palete, metas e demais parâmetros variáveis não ficam fixos no código. Eles são editados no AUTOPACKLINE e persistidos no MySQL. Uma alteração de quantidade vale para novos paletes; paletes já abertos preservam a quantidade-alvo com que foram criados.

## QR de referência

Formato observado em caixa real:

```text
45HJFE12C2CG;7908412552656;ARC062600106197;000001275033;https://www.elgin.com.br
```

Campos confirmados:

1. código bruto de produto contendo o modelo;
2. EAN-13;
3. número de série;
4. ordem de produção (OP);
5. URL.

O significado do prefixo `45` ainda não foi confirmado. Por isso o sistema preserva o primeiro campo bruto e usa o produto cadastrado pelo EAN para obter o modelo oficial.

## Executar no Windows 11 / PowerShell

Na pasta raiz:

```powershell
docker compose down

docker compose up --build
```

O Compose usa o nome de projeto `autopackline_v1`, portanto reutiliza o volume já criado na validação anterior quando executado no mesmo Docker Desktop.

### Portas

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Health DB: http://localhost:8000/api/v1/health/db
- MySQL pelo Windows/Workbench: `127.0.0.1:3307`
- MySQL internamente no Docker: `mysql:3306`

A porta externa do MySQL pode ser alterada por `MYSQL_HOST_PORT` no `.env`.

## Primeiro teste da ETAPA 6

1. Abra **Configurações** no frontend.
2. Se ainda não existir linha, cadastre:
   - código `L01`;
   - nome `Linha 1`.
3. O produto da ETAPA 5 pode continuar no banco. Se estiver começando do zero, cadastre:
   - SKU: `HJFE12C2CG`
   - EAN: `7908412552656`
   - Modelo: `HJFE12C2CG`
   - Nome: `Condensadora 12.000 BTU`
   - Capacidade: `12000`
4. Configure uma quantidade por palete. Para teste rápido, use `2` e depois ajuste para o valor real quando Engenharia definir.
5. Abra **Operação**, selecione `L01` e clique em **Simular leitura** usando o QR de referência.
6. Se a leitura retornar `VALID`, clique em **Confirmar paletização (simular CLP)**.
7. Para uma segunda unidade fictícia de teste, altere somente o serial no campo do QR, por exemplo `ARC062600106198`, e repita. Com quantidade configurada como `2`, o palete deve mudar para `FULL`.
8. Abra **Rastreabilidade** e confirme os registros.

A segunda unidade acima é apenas dado fictício de teste; não representa uma unidade real da produção.

## Persistência

```powershell
docker compose down
```

mantém os dados no volume. Para apagar deliberadamente o banco local:

```powershell
docker compose down -v
```

Não use `-v` se quiser preservar os dados.

## Migrations

- `0001_initial`: produtos e linhas;
- `0002_core_functional`: configurações, metas, OPs, unidades, scans, paletes e itens.

O backend executa `alembic upgrade head` automaticamente após o MySQL ficar estável.

## Pendências conhecidas

- origem oficial do lote;
- significado do prefixo `45`;
- modelo/protocolo do leitor físico;
- marca/modelo e tags do CLP;
- sinal real de confirmação de paletização;
- documentação e direção da integração MES;
- autenticação/permissões e auditoria completa;
- regra final de identificação/etiqueta de transporte.

## ETAPA 6.1 — Filtros e paginação da rastreabilidade

A tela de Rastreabilidade usa consultas paginadas no backend/MySQL, evitando carregar um histórico inteiro no navegador. Leituras podem ser filtradas por período, linha, status, serial, EAN e OP. Paletes podem ser filtrados por período, linha, produto, status, código do palete e OP. O tamanho de página pode ser 10, 20 ou 50 registros.

A migration `0003` adiciona campos indexados de serial, EAN e OP em `scan_events` e preserva os registros existentes por meio de backfill a partir do JSON já armazenado.

Ao atualizar uma instalação existente, execute apenas `docker compose down` e depois `docker compose up --build`. Não use `docker compose down -v`, pois isso removeria o volume persistente do MySQL.

## ETAPA 6.2 — Dashboard operacional

O Dashboard agora possui filtros por período, linha, produto e OP, cards calculados a partir do MySQL, taxa de aprovação, produção por hora, distribuição dos status de leitura, paletes em andamento e últimas ocorrências. Cards e ocorrências podem levar diretamente para a Rastreabilidade com os filtros correspondentes.

Os KPIs de eficiência por meta, takt e produtividade por turno continuam deliberadamente não calculados até a validação das respectivas regras industriais. Consulte `docs/ETAPA_6_2.md`.


## ETAPA 6.2.2 — Dashboard para leitura à distância
- KPIs com título à esquerda e valor destacado à direita.
- Tipografia ampliada no Dashboard para apresentação em monitor.
- Layout desktop permanece sem zoom/scale e sem rolagem vertical nas resoluções-alvo.

## ETAPA 6.3 — Login, perfis e auditoria

A versão atual exige autenticação. No primeiro start após a migration 0004, se não existir nenhum usuário, é criado o administrador inicial configurado no `.env`. Valores de desenvolvimento: `admin` / `Autopack@2026`. Troque a senha após o primeiro login.

Perfis: Operador (Dashboard + Operação), Supervisor (inclui Rastreabilidade) e Administrador (acesso total + Usuários/Configurações). Consulte `docs/ETAPA_6_3.md`.


## ETAPA 6.3.1 — Fuso horário operacional

O banco permanece em UTC. O frontend converte datas para `VITE_TIME_ZONE` (padrão `America/Manaus`) antes de exibir auditoria, último acesso, dashboard e rastreabilidade.


## ETAPA 6.3.2 — ajuste visual final

Corrigido o recuo do conteúdo em todas as telas quando o menu lateral é recolhido, evitando sobreposição do botão hambúrguer sobre o título “NÚCLEO FUNCIONAL”.

## ETAPA 6.3.3 — Edição de usuários
Administradores agora podem editar nome, usuário, perfil e status de contas existentes, mantendo as proteções da própria conta administrativa e a auditoria das alterações.


## ETAPA 6.3.4
Interface operacional ampliada e listas crescentes paginadas. Consulte `docs/ETAPA_6_3_4.md`.


## ETAPA 6.3.5
Correção da paginação da Rastreabilidade (8/12/20 por página) e mensagens de erro da API.

## ETAPA 6.3.6

Painel de cadastro/permissões recolhível, paginação compacta de usuários e auditoria e botão `?` para consultar a etapa atual sem ocupar espaço permanente da interface.

## ETAPA 6.5 — Leitura móvel

Celulares e tablets na LAN podem capturar QR Code/barcode pela câmera. O modo **Foto / câmera** funciona no acesso HTTP atual; o **Scanner ao vivo** está preparado para HTTPS. A leitura capturada continua passando pelas regras existentes do backend e pela rastreabilidade no MySQL. Consulte `docs/ETAPA_6_5.md`.


## ETAPA 6.5.1 — Correção de acesso/API

Correção do login HTTP 404 introduzido na 6.5. Em acesso HTTP (localhost ou LAN), o frontend chama automaticamente o FastAPI em `http://<host>:8000/api/v1`. Em HTTPS, mantém `/api/v1` para uso do proxy seguro.


## ETAPA 6.5.2 — leitura móvel robusta
- Leitura de foto com múltiplas estratégias (BarcodeDetector quando disponível + ZXing).
- Pré-processamento de fotos grandes de celular em múltiplas resoluções, cortes centrais e rotações.
- Conteúdo reconhecido é copiado automaticamente para o campo de operação.
- Prévia da última foto analisada e mensagens de diagnóstico.
- Layout da Operação otimizado para celulares, inclusive telas estreitas.


## ETAPA 6.5.3 — estabilidade no celular
No mobile/tablet, o menu lateral agora abre somente pelo botão hambúrguer. Toques, foco de campos e uso da câmera não reabrem automaticamente o menu, evitando oscilações e mudanças de layout durante a operação. No desktop, o auto-ocultamento após 5 segundos continua ativo.


## ETAPA 6.5.4 — Filtros de data

- Dashboard: Hoje, Ontem, Últimas 24h, Últimos 7 dias, Este mês, Data/período personalizado e Todo período.
- Rastreabilidade: os mesmos filtros para Leituras e Paletes.
- Auditoria administrativa: filtro por período preservando paginação.
- Datas personalizadas usam dia completo (00:00:00 até 23:59:59) e mantêm a conversão UTC/fuso local.
- O padrão continua sendo Hoje; para consultar 10/08 no dia 11/08 basta selecionar Ontem.

## ETAPA 6.5.5 — Scanner contínuo móvel
A leitura móvel principal agora é contínua, sem tirar foto. Na rede local, mantenha `http://IP:5173` para uso normal e use `https://IP:5174` no celular para liberar a câmera ao vivo. Ao detectar um QR/barcode, o sistema mostra o valor e exige confirmação antes de copiá-lo para o conteúdo capturado.


## ETAPA 6.5.6 — Scanner móvel rápido

A leitura móvel foi otimizada para usar `BarcodeDetector` quando disponível no navegador, com ZXing como fallback. O código reconhecido passa a preencher automaticamente o campo **Conteúdo capturado**, sem etapa intermediária de confirmação. A validação industrial continua sendo acionada manualmente pelo botão **Validar leitura**.

## ETAPA 6.6 — Ordens de Produção
A versão atual inclui gestão operacional de OP com ciclo OPEN/ACTIVE/PAUSED/COMPLETED/CANCELLED, vínculo a produto e linha, progresso produtivo, auditoria e validação da OP durante a leitura. Veja `docs/ETAPA_6_6.md`.

## ETAPA 6.7 — Fluxo operacional da linha
Veja `docs/ETAPA_6_7.md`. A operação agora exige Linha + OP ativa, mostra o contexto/progresso da OP e bloqueia preventivamente QR de outra ordem antes da validação.


## ETAPA 6.8 — Metas configuráveis
Metas por hora, meta diária e takt agora podem ser cadastrados por linha/produto e são exibidos no Dashboard quando aplicáveis. A meta específica do produto prevalece sobre a meta geral da linha. Indicadores dependentes de turno/OEE continuam marcados como requisito a definir. Consulte `docs/ETAPA_6_8.md`.


## ETAPA 6.8.2
Takt calculado automaticamente a partir da Meta/hora e ajuda contextual no campo.

## ETAPA 6.9.1 — Meta × Produção real
O Dashboard passa a comparar as unidades paletizadas com as metas configuradas, mostrando atingimento diário e referência por hora. Consulte `docs/ETAPA_6_9_1.md`.


## ETAPAS 6.9.2–6.9.4 — Ritmo, desempenho por hora e evolução da meta

O Dashboard passou a calcular o ritmo real médio entre unidades paletizadas, comparar esse ritmo com o Takt planejado, mostrar desempenho por hora e o acumulado percentual da meta diária. Eficiência/OEE continuam fora do cálculo até a definição das regras reais de jornada e paradas.

## ETAPA 6.10 — Jornada, turnos, pausas e paradas
A aplicação agora permite configurar turnos por linha, pausas planejadas e registrar/encerrar paradas planejadas ou não planejadas. Esses dados formam a base temporal para os cálculos posteriores de eficiência e OEE, que continuam desativados até validação das regras industriais. Consulte `docs/ETAPA_6_10.md`.

## ETAPA 6.15 — Análise de perdas

A área Indicadores agora possui as abas **Histórico de OEE** e **Análise de perdas**.
A nova análise apresenta Pareto das paradas não planejadas por motivo e Pareto das
ocorrências de rastreabilidade, com filtros de 7, 14 e 30 dias, linha e produto.
Os cálculos utilizam as tabelas existentes no MySQL; não há migration nova.

## ETAPA 6.17 — Central de alertas operacionais

A área Indicadores possui agora a aba **Alertas operacionais**, que prioriza os indicadores classificados pela configuração da ETAPA 6.16 e apresenta recomendações de investigação e contexto operacional do dia. Não há migration nova.

## ETAPA 6.18 — Tendência histórica dos alertas

A área Indicadores possui agora a aba **Tendência dos alertas**, com filtros de 7, 14 e 30 dias, linha e produto. Disponibilidade, Performance, Qualidade e OEE são classificados por dia usando os limites configuráveis atuais. Nenhum dado histórico é alterado e não há migration nova.

## ETAPA 7.1 — Camada de integração do leitor QR / Barcode

A integração física foi iniciada sem exigir hardware. O backend agora possui um
`ReaderGateway` como ponto único de entrada e o adaptador `SIMULATOR_READER_V1`.
A tela Operação consulta o status da integração e envia a validação pelo novo
endpoint `/api/v1/integrations/reader/ingest`.

O leitor físico continua explicitamente **não conectado**. Nenhum protocolo USB,
serial ou Ethernet foi fixado antes de conhecermos o equipamento real. Não há
migration nova nesta etapa.

## ETAPA 7.2 — Adaptador USB/HID preparado

A tela Operação possui agora captura para leitores USB que se comportam como
teclado. Sem hardware, o fluxo pode ser validado colando um código no campo HID
e pressionando ENTER. O backend registra a origem `HID_USB` pelo adaptador
`HID_KEYBOARD_V1`, preservando todas as regras existentes. Hardware físico
continua explicitamente não conectado e não há migration nova.

## ETAPA 7.3 — Diagnóstico e homologação da entrada do leitor

Inclui diagnóstico não persistente do conteúdo recebido pelo simulador ou
adaptador HID/USB. Permite conferir estrutura, EAN, serial, OP e URL antes da
validação produtiva, sem gravar registros no MySQL.

### ETAPA 7.3.1 — Regra de interface recolhível

A partir desta correção, blocos operacionais que aumentam a altura da tela devem usar painéis recolhíveis estilo hambúrguer/accordion. Na Operação, USB/HID, diagnóstico do leitor e último código detectado ficam recolhíveis, evitando corte e rolagem vertical desnecessária em monitor a 100% e em dispositivos móveis.

## ETAPA 7.4 — Integração CLP preparada

A confirmação de paletização da tela Operação agora passa pela camada `integrations/plc`, usando o adaptador `SIMULATOR_PLC_V1`. O contrato aceita o sinal `PALLETIZE_CONFIRMED` e mantém a regra de negócio já validada. O CLP físico continua explicitamente bloqueado até a definição do equipamento e protocolo reais. Consulte `docs/ETAPA_7_4.md`.

## ETAPA 7.5 — Ciclo do palete e retorno do CLP

A confirmação simulada do CLP agora retorna o estado do ciclo do palete e a próxima ação operacional. O fechamento continua dependente exclusivamente da quantidade por palete configurada no MySQL. Não há protocolo físico presumido nem valores/data fixos no código.


## ETAPA 7.6
Continuidade automática do ciclo: após um palete completo, a próxima unidade cria um novo palete e o retorno do CLP identifica explicitamente `NEW_PALLET_STARTED`.


## ETAPA 7.7
Retorno robusto do CLP simulado: ACK/NACK, rejeição sem paletização e proteção contra confirmação duplicada.

## ETAPA 7.8 — Sincronização persistida do ciclo CLP

O ciclo entre leitura válida e confirmação do CLP agora pode ser reconstruído a partir do MySQL. A tela Operação restaura a unidade atual após refresh, identifica `AWAITING_PLC` ou `PALLETIZED`, mantém NACK como tentativa não consumida e bloqueia sinais/validações fora da sequência. O estado usa as tabelas existentes; não há migration nem protocolo físico presumido. Consulte `docs/ETAPA_7_8.md`.

## ETAPA 7.8.1 — Correção da persistência após refresh

A recuperação do ciclo deixou de depender do `sessionStorage`: ao abrir a Operação com linha e OP selecionadas, o frontend consulta o MySQL pelo endpoint `latest-cycle` e restaura a unidade mais recente como `AWAITING_PLC` ou `PALLETIZED`. Consulte `docs/ETAPA_7_8_1_CORRECAO_PERSISTENCIA_REFRESH.md`.

## ETAPA 7.9 — Timeout, reconexão e estado seguro do CLP

A camada `integrations/plc` passou a simular falhas de comunicação sem alterar o estado produtivo no MySQL. É possível testar desconexão, reconexão e timeout do próximo ACK/NACK. O timeout é configurável por `PLC_SIMULATOR_TIMEOUT_SECONDS`. Falhas deixam a unidade aguardando CLP para uma nova tentativa segura. Consulte `docs/ETAPA_7_9.md`.


## ETAPA 7.10 — Retentativa controlada e recuperação operacional do CLP

Time­outs transitórios passam a ter retentativa controlada no backend. O número máximo de tentativas e o intervalo são configuráveis por `PLC_RETRY_MAX_ATTEMPTS` e `PLC_RETRY_INTERVAL_SECONDS`. Apenas timeout é repetido automaticamente; desconexão, NACK e sequência inválida permanecem fail-safe. Se o limite for esgotado, nenhuma paletização é gravada e a mesma unidade pode ser retomada após a comunicação ser restabelecida. Consulte `docs/ETAPA_7_10.md`.


## ETAPA 7.10.1 — contador de produção confirmada
O contador "produzido" da OP passa a representar somente unidades `PALLETIZED` (ACK do CLP aceito). Leituras `SCANNED` são expostas separadamente como `scanned_quantity`. Consulte `docs/ETAPA_7_10_1_CORRECAO_CONTADOR_PRODUCAO.md`.

### ETAPA 7.12 — NACK final do CLP
- Um `PALLETIZE_REJECTED` (NACK) agora é tratado como decisão final da unidade, não como timeout.
- A unidade passa de `SCANNED` para `PLC_REJECTED` no MySQL.
- Nenhum item de palete é criado e o contador de produzido confirmado não aumenta.
- O ciclo é liberado imediatamente para a próxima leitura.
- As retentativas configuradas continuam exclusivas para timeout de comunicação; não é necessário clicar NACK três vezes.

## ETAPA 7.14 — contrato Modbus TCP real
O contrato proposto AUTOPACKLINE ↔ Delta AS228T-A foi formalizado em código e documentação. A comunicação física permanece desabilitada enquanto o ladder D700-D763 não estiver implementado. Consulte `GET /api/v1/integrations/plc/modbus-contract` e `docs/ETAPA_7_14_CONTRATO_MODBUS_TCP_REAL.md`.

## ETAPA 7.19 — Simulador completo do CLP D700-D763
Foi adicionado um simulador lógico determinístico do contrato Modbus proposto, sem conexão física. Ele mantém D700-D763 em memória, reutiliza o codec da 7.15 e exercita ACK, BUSY, conclusão, rejeição, falha, heartbeat e palete. Consulte `docs/ETAPA_7_19_SIMULADOR_COMPLETO_CLP_D700_D763.md`.

## ETAPA 7.21 — Motor de produção automática (offline)
O motor de decisões do fluxo sem operador está modelado e testado offline. Ele arma o leitor quando o sistema está livre, exige validação automática do código, bloqueia novas unidades em BUSY/falha/comunicação degradada, persiste a identidade antes do write, diferencia ACK de conclusão física e só confirma produção com D760=REQUEST_SEQUENCE e D761=1. A ligação automática deste motor ao ReaderGateway/HID será feita na ETAPA 7.22; o CLP físico continua bloqueado.

## ETAPA 7.28 — Pacote de evidências e checklist de comissionamento
Os 12 passos da 7.27 agora possuem um manifesto de evidências com estado, evidência esperada e campos mínimos para registro futuro. O snapshot offline referencia health-check, resiliência, gate e plano sem marcar testes físicos como concluídos. Nenhum socket Modbus é aberto. Consulte `docs/ETAPA_7_28_PACOTE_EVIDENCIAS_COMISSIONAMENTO.md`.


## ETAPA 7.29 — Ensaio geral pré-comissionamento offline
Consolida health-check, resiliência, gate de prontidão, plano e pacote de evidências em um dry-run único. Nenhuma conexão física é aberta; o resultado esperado é `REHEARSAL_READY_OFFLINE`, zero FAIL e socket físico fechado. Consulte `docs/ETAPA_7_29_ENSAIO_GERAL_PRE_COMISSIONAMENTO_OFFLINE.md`.

## ETAPA 7.30 — Reorganização profissional da interface

A interface separa o trabalho diário da fábrica das ferramentas técnicas. A tela
Operação concentra linha, OP, leitura, progresso e resultado produtivo; contrato
Modbus, resiliência, health-check, evidências e controles de falha do simulador
ficam em Manutenção e Diagnóstico, disponível a Supervisor e Administrador. Os
perfis e regras industriais existentes foram preservados, assim como o bloqueio
do adaptador físico. Consulte
`docs/ETAPA_7_30_REORGANIZACAO_OPERACAO_DIAGNOSTICO.md`.
# Histórico — ETAPA 7.31

A versão atual inclui a fundação controlada de reteste offline: histórico de várias tentativas por unidade, idempotência, auditoria, simulador e painel técnico recolhível. O reteste real permanece desabilitado (`RETEST_ENABLED=false`) até a definição das regras de processo. Consulte `docs/ETAPA_7_31_FUNDACAO_RETESTE_OFFLINE.md`.
