param(
    [Parameter(Mandatory = $true)][string]$Username,
    [Parameter(Mandatory = $true)][string]$Password,
    [switch]$SkipModbus
)

$ErrorActionPreference = "Stop"
$api = "http://localhost:8000/api/v1"

Write-Host "1/6 - Containers" -ForegroundColor Cyan
docker compose ps

Write-Host "2/6 - Migração do banco" -ForegroundColor Cyan
$revision = docker compose exec -T backend alembic current
if ($LASTEXITCODE -ne 0 -or $revision -notmatch "0011") { throw "Migração 0011 não aplicada: $revision" }
$revision

Write-Host "3/6 - Configuração segura" -ForegroundColor Cyan
docker compose exec -T backend python -c "from app.core.config import settings; print('RETEST_ENABLED=',settings.retest_enabled); print('MES_REAL_ENABLED=',settings.mes_quality_enabled); print('MES_MODE=',settings.mes_quality_mode); print('PLC_FISICO=',settings.plc_physical_enabled)"

Write-Host "4/6 - Login e contrato Rev.03" -ForegroundColor Cyan
$login = Invoke-RestMethod -Method Post -Uri "$api/auth/login" -ContentType "application/json" -Body (@{ username=$Username; password=$Password } | ConvertTo-Json)
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$rev = Invoke-RestMethod -Uri "$api/integrations/plc/rev03" -Headers $headers
if ($rev.identity_probe.D764 -ne 6 -or $rev.identity_probe.D766 -ne 918 -or $rev.identity_probe.D779 -ne 89) {
    throw "Contrato Rev.03 incorreto: D764=$($rev.identity_probe.D764), D766=$($rev.identity_probe.D766), D779=$($rev.identity_probe.D779)"
}
Write-Host "REV03_OK - Ladder $($rev.identity_probe.D764), data $($rev.identity_probe.D766), bloco $($rev.identity_probe.D779)" -ForegroundColor Green

Write-Host "5/6 - Regra MES/NG" -ForegroundColor Cyan
$mes = Invoke-RestMethod -Uri "$api/mes-quality/status" -Headers $headers
if ($mes.line_stops_on_ng -ne $false) { throw "Regra inválida: NG não deve parar a linha." }
Write-Host "MES_NG_CONTINUA_LINHA_OK - modo $($mes.mode), endpoint real configurado=$($mes.endpoint_configured)" -ForegroundColor Green

Write-Host "6/6 - CLP-Simulator Rev.03" -ForegroundColor Cyan
if ($SkipModbus) {
    Write-Host "Teste Modbus ignorado por solicitação." -ForegroundColor Yellow
} else {
    $probe = Invoke-RestMethod -Method Post -Uri "$api/integrations/plc/external-simulator/probe" -Headers $headers
    if (-not $probe.connected -or $probe.probe -ne "READ_REV03_SNAPSHOT_OK") {
        throw "CLP-Simulator ainda não respondeu no contrato Rev.03: $($probe.message)"
    }
    Write-Host "MODBUS_REV03_OK - heartbeat $($probe.handshake.plc_heartbeat)" -ForegroundColor Green
}

Write-Host "VALIDAÇÃO CONCLUÍDA" -ForegroundColor Green
