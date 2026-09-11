# ETAPA 6.5.5 — Scanner móvel contínuo com confirmação

## Objetivo
Substituir o fluxo principal de fotografia por uma experiência de scanner contínuo semelhante à câmera nativa do celular.

## Fluxo
1. Abrir **Iniciar scanner ao vivo**.
2. Apontar a câmera traseira para QR Code ou barcode.
3. O ZXing monitora os quadros continuamente, sem o usuário tirar foto.
4. Ao encontrar um código, a câmera pausa e o conteúdo detectado é exibido.
5. O operador escolhe **Confirmar e copiar** ou **Não é esse · ler outro**.
6. Somente após confirmação o conteúdo é copiado para o campo e pode ser validado pelo backend.

## HTTPS na rede local
Browsers exigem contexto seguro para `getUserMedia()` fora de localhost. A versão mantém o AUTOPACKLINE HTTP em `:5173` e adiciona uma instância HTTPS de desenvolvimento em `:5174`.

- Uso normal: `http://IP_DO_PC:5173`
- Scanner móvel: `https://IP_DO_PC:5174`

O HTTPS desta etapa usa certificado de desenvolvimento gerado pelo Vite. Em implantação industrial final deve ser usado certificado confiável aprovado pela TI.

## Observação
Caso o navegador do dispositivo ainda não considere o certificado de desenvolvimento como contexto seguro após a confirmação do aviso, será necessário instalar/usar um certificado confiável na rede local. Isso deve ser alinhado com a TI da empresa.
