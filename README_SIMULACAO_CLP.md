# Simulação do CLP no AUTOPACKLINE

Este guia explica como preparar o AUTOPACKLINE e o CLP-Simulator para testar a
comunicação Modbus TCP sem conectar ao CLP físico da máquina.

## Visão geral

No ambiente real, o fluxo previsto é:

```text
SR-1000 → EtherNet/IP → CLP Delta AS228T-A → Modbus TCP → AUTOPACKLINE
```

No ambiente de desenvolvimento, o CLP-Simulator substitui o CLP Delta:

```text
Painel SR-1000 do simulador → CLP-Simulator → Modbus TCP → AUTOPACKLINE
```

O simulador disponibiliza os registradores. O AUTOPACKLINE é o cliente Modbus e
inicia as leituras.

## Branches usadas

- AUTOPACKLINE: `feature/clp-simulator-integration`
- CLP-Simulator: `feature/autopackline-d700-d879`

As alterações da integração ficam separadas das branches `main` dos dois
repositórios.

## Pré-requisitos

- Docker Desktop ou Rancher Desktop em execução;
- Node.js compatível com o CLP-Simulator;
- repositórios AUTOPACKLINE e CLP-Simulator disponíveis na máquina;
- portas livres: `3100` para o painel do simulador, `1502` para Modbus, `5173`
  para o frontend e `8000` para o backend.

## 1. Preparar o AUTOPACKLINE

Na raiz do AUTOPACKLINE, crie ou ajuste o arquivo `.env`:

```env
PLC_PHYSICAL_ENABLED=false
PLC_WRITE_ENABLED=false

PLC_EXTERNAL_SIMULATOR_ENABLED=true
PLC_EXTERNAL_SIMULATOR_WRITE_ENABLED=false
PLC_EXTERNAL_SIMULATOR_HOST=host.docker.internal
PLC_EXTERNAL_SIMULATOR_PORT=1502
PLC_EXTERNAL_SIMULATOR_UNIT_ID=1
PLC_EXTERNAL_SIMULATOR_LOGICAL_ORIGIN=700
PLC_EXTERNAL_SIMULATOR_REGISTER_BASE=0
PLC_EXTERNAL_SIMULATOR_TIMEOUT_MS=1000
```

Essa configuração possui três proteções importantes:

- o adaptador físico permanece desabilitado;
- a escrita física permanece desabilitada;
- a escrita no simulador também permanece desabilitada no primeiro teste.

`host.docker.internal` permite que o backend dentro do Docker acesse o simulador
executado diretamente no Windows.

## 2. Iniciar o CLP-Simulator

No PowerShell, dentro do repositório CLP-Simulator:

```powershell
$env:MODBUS_HOST="0.0.0.0"
npm.cmd install
npm.cmd start
```

Se o painel ainda não estiver compilado ou estiver em desenvolvimento, use:

```powershell
$env:MODBUS_HOST="0.0.0.0"
npm.cmd install
npm.cmd run dev
```

Abra o painel em:

```text
http://127.0.0.1:3100
```

A máquina `M1`, na porta `1502`, deve usar o perfil `autopackline`. Nesse perfil:

| Registrador lógico | Holding register do simulador | Uso |
|---|---:|---|
| D700–D749 | 0–49 | comandos do AUTOPACKLINE |
| D750–D779 | 50–79 | estado, handshake e diagnóstico |
| D800–D879 | 100–179 | dados do leitor SR-1000 |

## 3. Iniciar o AUTOPACKLINE

No PowerShell, dentro da raiz do AUTOPACKLINE:

```powershell
docker compose up --build
```

Abra:

```text
http://localhost:5173
```

Para desenvolvimento local, a conta administrativa inicial padrão é:

```text
Usuário: admin
Senha: Autopack@2026
```

Troque essa senha quando o ambiente não for exclusivamente local.

## 4. Testar a leitura Modbus

### No CLP-Simulator

1. Localize **Leitor SR-1000 · D800–D879**.
2. Mantenha ou informe um código curto, por exemplo:

   ```text
   X;7908412552656;S1;OP1;https://x.co
   ```

3. Selecione `GOOD READ`.
4. Clique em **Publicar leitura**.

Essa ação simula o SR-1000 e preenche D767–D779 e D800–D879. Ela também ativa
em D777 as flags que autorizam o AUTOPACKLINE a usar os dados do leitor.

### No AUTOPACKLINE

1. Entre com um usuário Supervisor ou Administrador.
2. Abra **Manutenção e Diagnóstico**.
3. No cartão **Teste Modbus com o CLP-Simulator**, clique em
   **Testar conexão e leitura Modbus**.

O resultado esperado é:

```text
READ_REV02_SNAPSHOT_OK
```

A tela também deve mostrar:

- conexão estabelecida;
- heartbeat do simulador;
- estado `READY`;
- identidade do protocolo e Ladder Rev.04 válida;
- resultado, serial, EAN, OP, modelo e conteúdo bruto publicados.

O socket é aberto apenas durante o teste explícito e fechado em seguida.

## 5. O que o teste comprova

O teste valida:

- acesso TCP à porta `1502`;
- comunicação Modbus TCP com Unit ID `1`;
- tradução de D700 para holding register `0`;
- leitura consistente de D750–D779 e D800–D879;
- identidade Rev.04;
- heartbeat;
- feature flags de D777;
- ordem dos bytes e parser do conteúdo do leitor.

Ele não valida EtherNet/IP, o SR-1000 físico, o Ladder compilado no ISPSoft ou o
CLP Delta real. Essas verificações continuam pendentes para o comissionamento.

## 6. Teste de escrita

O adaptador também suporta escrita em D700–D749, mas ela permanece bloqueada por
padrão. Para liberar escrita exclusivamente no CLP-Simulator:

```env
PLC_EXTERNAL_SIMULATOR_WRITE_ENABLED=true
```

Mantenha obrigatoriamente:

```env
PLC_PHYSICAL_ENABLED=false
PLC_WRITE_ENABLED=false
```

Depois de alterar o `.env`, recrie o backend:

```powershell
docker compose up -d --build --force-recreate backend
```

Ainda não existe um botão operacional para a escrita externa. A liberação deve
ser usada somente por teste automatizado ou por uma futura ação explícita de
diagnóstico, com sequência, ACK e conclusão verificáveis.

## 7. Testes automatizados

AUTOPACKLINE:

```powershell
docker compose run --rm backend pytest
cd frontend
npm.cmd run build
```

CLP-Simulator:

```powershell
npm.cmd test
npm.cmd run build
```

## 8. Solução de problemas

### O botão de teste não aparece

O botão fica no AUTOPACKLINE, não no CLP-Simulator. Use um usuário Supervisor ou
Administrador e abra **Manutenção e Diagnóstico**. No simulador, o botão se chama
**Publicar leitura**.

### Conexão recusada ou timeout

Confirme:

- CLP-Simulator em execução;
- `M1` conectada na porta `1502`;
- `MODBUS_HOST=0.0.0.0` antes de iniciar o simulador;
- backend configurado com `host.docker.internal:1502`;
- firewall do Windows permitindo a conexão local.

### Perfil ou identidade incompatível

Confira em `machines.json` se a máquina da porta `1502` contém:

```json
"profile": "autopackline"
```

O AUTOPACKLINE espera D750=1, D764=4, D765=2026, D766=917, D778=800 e
D779=80.

### Frontend reiniciando com erro do esbuild

Reconstrua as imagens após confirmar que `frontend/.dockerignore` exclui
`node_modules`:

```powershell
docker compose build --no-cache frontend frontend_secure
docker compose up -d --force-recreate frontend frontend_secure
```

## Limitação conhecida do conteúdo bruto

O campo D847–D878 reserva 32 registradores, portanto comporta somente 64 bytes.
O QR real de referência é maior que esse limite. O simulador rejeita conteúdos
maiores em vez de truncá-los silenciosamente.

Antes do comissionamento, Automação e Software precisam definir uma das opções:

- ampliar o bloco;
- não transportar a URL pelo bloco Modbus;
- usar outra fonte para a auditoria do conteúdo completo.

## Segurança para o primeiro teste físico

O uso do simulador não libera automaticamente o CLP real. A primeira conexão
física deve continuar somente leitura e depende da Rev.04 compilada e validada,
rede aprovada, confirmação do offset, teste `AB12`, byte order e comparação com o
programa online no CLP.
