# ETAPA 6.5.1 — Correção de acesso/API

- Corrige HTTP 404 em `/api/v1/auth/login` no frontend.
- Em HTTP, usa automaticamente `http://<IP-ou-host>:8000/api/v1`.
- Em HTTPS, usa `/api/v1`, permitindo proxy do Vite para o backend.
- Mantém a leitura móvel QR/Barcode da ETAPA 6.5.
- Mantém acesso LAN da ETAPA 6.4.
