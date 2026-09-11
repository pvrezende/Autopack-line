# ETAPA 6.5.6 — Scanner móvel rápido e preenchimento automático

- Scanner ao vivo passa a priorizar a API nativa `BarcodeDetector` do navegador quando disponível.
- Fallback para ZXing continua disponível para navegadores sem `BarcodeDetector`.
- Resolução da câmera ajustada para 1280x720 para reduzir latência de decodificação.
- Solicitação de foco contínuo quando suportada pelo aparelho.
- Quando há vários códigos no enquadramento, QR Code é priorizado e, em seguida, o conteúdo mais completo.
- Ao detectar o código, a câmera para e o valor completo é colocado automaticamente em **Conteúdo capturado**.
- O operador continua decidindo quando pressionar **Validar leitura**.
- Removida a etapa extra de “Confirmar e copiar”.
- Mantidos os filtros de data, acesso LAN/HTTPS, responsividade e permissões existentes.
