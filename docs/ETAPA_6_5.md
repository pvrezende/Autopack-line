# ETAPA 6.5 — Leitura móvel QR Code / Barcode

A ETAPA 6.5 transforma celular/tablet na mesma LAN em leitor móvel auxiliar do AUTOPACKLINE.

## O que foi implementado

- Botão **Foto / câmera**: usa o seletor/câmera nativa do celular e decodifica a foto no navegador.
- Botão **Scanner ao vivo**: câmera contínua com preferência pela câmera traseira.
- Leitura multi-formato com `@zxing/browser` (QR Code + códigos 1D/2D suportados pelo ZXing).
- Anti-repetição de captura do mesmo código por 2,5 segundos.
- Código lido preenche automaticamente o campo de conteúdo e continua usando o MESMO endpoint de validação existente do backend.
- A paletização continua separada da leitura e o CLP permanece simulado.
- API do frontend passou a usar `/api/v1` no mesmo host, com proxy do Vite para o backend. Isso evita dependência de `localhost:8000` e evita mixed-content quando HTTPS for ativado.

## Uso recomendado agora (HTTP na LAN)

Acesse normalmente:

`http://10.90.100.162:5173`

No celular, entre em **Operação > Foto / câmera**. O navegador abre a câmera/aplicativo de foto; fotografe o QR ou barcode e aguarde a captura.

Esse modo foi incluído justamente para permitir teste móvel mesmo antes de configurarmos certificado HTTPS confiável.

## Scanner ao vivo / HTTPS opcional

Câmera contínua via `getUserMedia` exige contexto seguro no navegador. Para experimentar HTTPS autoassinado:

1. Crie/edite `.env` na raiz:

```env
AUTOPACKLINE_HTTPS=true
```

2. Reconstrua:

```powershell
docker compose down
docker compose up --build -d
```

3. Acesse:

`https://10.90.100.162:5173`

O Vite gera certificado autoassinado para desenvolvimento. Alguns celulares/navegadores podem exigir aceitar/confiar manualmente no certificado. Para uso industrial definitivo, usar certificado confiável da rede interna é preferível.

## Barcode x regra industrial

O leitor consegue CAPTURAR barcode. Porém a regra atual do backend valida o payload AUTOPACKLINE com 5 campos separados por `;` (modelo/EAN/serial/OP/URL). Um barcode que contenha somente EAN será capturado, mas pode ser marcado como inválido/rejeitado até definirmos como EAN-only deve completar serial e OP. Essa regra não foi inventada nesta etapa.

## Teste sugerido

1. Subir Docker.
2. Acessar pelo celular na mesma rede.
3. Login como operador.
4. Selecionar Linha 1.
5. Tocar **Foto / câmera** e fotografar o QR real.
6. Confirmar que o conteúdo aparece no campo.
7. Tocar **Validar leitura**.
8. Confirmar status e rastreabilidade.
