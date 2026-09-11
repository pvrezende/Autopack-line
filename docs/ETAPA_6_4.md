# ETAPA 6.4 — Acesso pela rede local (LAN)

IP observado em 10/08/2026: `10.90.100.162` (Wi-Fi).

## Acesso esperado

- No PC servidor: `http://localhost:5173`
- Em outro dispositivo na mesma rede: `http://10.90.100.162:5173`
- API: porta `8000`

O frontend agora descobre automaticamente o host usado no navegador e chama a API no mesmo IP, porta 8000. O backend já escuta em `0.0.0.0` e o CORS inclui localhost e o IP atual da LAN.

## Subir a versão

```powershell
docker compose down
docker compose up --build -d
docker compose ps
```

## Firewall do Windows (PowerShell como Administrador)

```powershell
New-NetFirewallRule -DisplayName "AUTOPACKLINE Frontend 5173" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5173 -Profile Private
New-NetFirewallRule -DisplayName "AUTOPACKLINE Backend 8000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -Profile Private
```

Teste primeiro de outro computador/celular conectado à mesma rede Wi-Fi. Se o IP do servidor mudar por DHCP, use o novo IPv4 exibido por `ipconfig`. Para instalação definitiva, recomenda-se reserva DHCP/IP fixo para o servidor AUTOPACKLINE.
