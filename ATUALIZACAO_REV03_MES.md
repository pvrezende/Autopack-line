# AUTOPACKLINE — atualização Rev.03 e contenção MES/NG

## O que esta versão entrega

- Contrato oficial Rev.03: Ladder Rev.06, data 18/09/2026 e POU `PRG_08_AUTOPACKLINE`.
- Leitura Modbus `D700–D779 + D800–D888`.
- Identidade obrigatória: `D750=1`, `D764=6`, `D765=2026`, `D766=918`, `D777=15`, `D778=800`, `D779=89`.
- Dado bruto do leitor em `D847–D887`, até 82 bytes; erro em `D888`.
- Compatibilidade temporária da rota antiga `/plc/rev02`, mas todo o conteúdo retornado já é Rev.03.
- Fundação MES segura enquanto o contrato Elgin não chega: integração real desligada, simulador habilitado.
- Resultado NG não para a linha. A unidade pode ser depositada, mas o palete recebe `HOLD_NG` e um alerta persistente com serial, palete e posição.
- O alerta só é encerrado após confirmação de retirada por Supervisor ou Administrador, com observação auditável.
- Resultado NG recebido depois da deposição também cria o alerta corretamente.

## Atualização no Windows sem perder o banco

Execute no PowerShell. Não use `docker compose down -v`, pois `-v` apagaria o volume do MySQL.

```powershell
cd "C:\Users\Paulo\OneDrive\Área de Trabalho\Autopack Line"

docker compose exec -T mysql mysqldump `
  -uroot `
  -proot_autopackline `
  --single-transaction `
  --routines `
  --triggers `
  autopackline > "..\autopackline_backup_antes_rev03.sql"

Copy-Item .env "..\autopackline_env_antes_rev03.txt" -Force
docker compose down
cd ..
Rename-Item "Autopack Line" "Autopack Line - backup antes Rev03"
Expand-Archive ".\AUTOPACKLINE_REV03_MES_NG_2026-09-18.zip" -DestinationPath "." -Force
Copy-Item ".\Autopack Line - backup antes Rev03\.env" ".\Autopack Line\.env" -Force
cd ".\Autopack Line"
```

Acrescente ao `.env` apenas se as linhas ainda não existirem:

```dotenv
MES_QUALITY_ENABLED=false
MES_QUALITY_SIMULATOR_ENABLED=true
MES_QUALITY_MODE=PENDING_CONTRACT
MES_QUALITY_BASE_URL=
MES_QUALITY_TIMEOUT_MS=3000
```

Mantenha as configurações já validadas do simulador externo. Exemplo da máquina de teste:

```dotenv
PLC_EXTERNAL_SIMULATOR_ENABLED=true
PLC_EXTERNAL_SIMULATOR_WRITE_ENABLED=true
PLC_EXTERNAL_SIMULATOR_HOST=192.168.50.20
PLC_EXTERNAL_SIMULATOR_PORT=1502
PLC_EXTERNAL_SIMULATOR_UNIT_ID=1
PLC_EXTERNAL_SIMULATOR_LOGICAL_ORIGIN=700
PLC_EXTERNAL_SIMULATOR_REGISTER_BASE=0
```

Suba a versão nova:

```powershell
docker compose build --no-cache backend frontend frontend_secure
docker compose up -d
docker compose ps
docker compose logs backend --tail 120
```

O backend executa `alembic upgrade head` automaticamente. Confirme:

```powershell
docker compose exec -T backend alembic current
```

O resultado precisa conter `0011`.

## Validação automática

Com o CLP-Simulator do Ádrio já atualizado para Rev.03 e publicando uma leitura:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\VALIDAR_REV03.ps1 -Username admin -Password "SUA-SENHA-ATUAL"
```

Enquanto o simulador do Ádrio ainda não estiver na Rev.03:

```powershell
.\VALIDAR_REV03.ps1 -Username admin -Password "SUA-SENHA-ATUAL" -SkipModbus
```

## Teste controlado do alerta NG

Use somente um serial de teste que já esteja paletizado. Entre na aplicação como Supervisor/Administrador e obtenha o token automaticamente pelo comando abaixo:

```powershell
$api = "http://localhost:8000/api/v1"
$login = Invoke-RestMethod -Method Post -Uri "$api/auth/login" `
  -ContentType "application/json" `
  -Body (@{username="admin"; password="SUA-SENHA-ATUAL"} | ConvertTo-Json)
$headers = @{Authorization="Bearer $($login.access_token)"}

$serialTeste = "GOOD0001"
Invoke-RestMethod -Method Post -Uri "$api/mes-quality/simulate-result" `
  -Headers $headers -ContentType "application/json" `
  -Body (@{serial_number=$serialTeste; result="NG"; external_event_id="TESTE-NG-$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"} | ConvertTo-Json)

Invoke-RestMethod -Uri "$api/mes-quality/incidents?status=PENDING_REMOVAL" -Headers $headers | Format-List
```

Resultado esperado no Dashboard:

1. A produção permanece funcionando.
2. Surge `PALETE SOB INSPEÇÃO`.
3. O alerta mostra serial, modelo, OP, código do palete e ordem/posição.
4. O alerta permanece após atualizar a página e reiniciar containers.
5. Ao clicar em **Confirmar retirada do palete**, o sistema exige observação e registra usuário/data.

## Informações ainda necessárias do MES Elgin

Não habilite `MES_QUALITY_ENABLED=true` até receber e validar:

- URL e ambiente de homologação/produção;
- autenticação e renovação de credenciais;
- consulta por serial ou evento enviado pelo MES;
- valores oficiais para OK, NG e indisponibilidade;
- identificador idempotente do teste;
- data/hora e fuso horário;
- timeout, repetição, rate limit e comportamento de contingência;
- exemplos reais de requisição e resposta;
- regra oficial de reteste e autoridade para liberação.

Quando essas informações chegarem, o adaptador Elgin será conectado à fundação já criada sem alterar a regra operacional: NG não para a linha e mantém o palete sob inspeção até retirada confirmada.
