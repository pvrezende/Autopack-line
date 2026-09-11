# ETAPA 6.5.2 — Leitura móvel robusta e responsiva

Correções para uso em celulares como o Moto G84:

- captura pela câmera traseira via campo de arquivo em HTTP local;
- tentativa nativa via BarcodeDetector quando disponível;
- fallback ZXing em imagem original;
- fallback ZXing em versões redimensionadas, recortadas e rotacionadas da foto;
- cópia automática do código detectado para Conteúdo capturado;
- prévia da foto analisada;
- interface da tela Operação compactada e responsiva para celular;
- mantém validação industrial no backend após o usuário tocar em Validar leitura.
