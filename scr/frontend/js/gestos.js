/**
 * gestos.js: Captura a mão, desenha na tela e envia os dados para o backend.
 */
window.addEventListener('DOMContentLoaded', () => {
    const videoElement = document.getElementById('input_video');
    const canvasElement = document.getElementById('output_canvas');
    const canvasCtx = canvasElement.getContext('2d');

    // 1. Conecta ao WebSocket para ENVIAR dados
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => console.log("Controle: Conectado ao servidor WebSocket.");
    ws.onerror = (err) => console.error("Controle: Erro no WebSocket.", err);

    // 2. Lógica de desenho e envio no callback do MediaPipe
    function onResults(results) {
        // Desenha a imagem da câmera e o esqueleto da mão no canvas
        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
        if (results.multiHandLandmarks) {
            for (const landmarks of results.multiHandLandmarks) {
                drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, { color: '#FFFFFF', lineWidth: 3 });
                drawLandmarks(canvasCtx, landmarks, { color: '#00FF00', lineWidth: 1, radius: 4 });
            }
        }
        canvasCtx.restore();

        // Se detectou uma mão, processe e envie os dados
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            const landmarks = results.multiHandLandmarks[0];

            // Prepara o objeto de dados da ferramenta (seringa)
            const toolData = {
                source: 'hand_tracker', // Identificador para o receptor saber a origem
                position: landmarks[0], // Posição baseada no pulso (landmark 0)
                orientationTarget: landmarks[9] // Ponto para "olhar" (base do dedo médio)
            };

            // Envia os dados para o backend, que irá retransmitir
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(toolData));
            }
        }
    }

    // 3. Inicialização do MediaPipe (semelhante ao que você já tinha)
    const hands = new Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });
    hands.setOptions({ maxNumHands: 1, modelComplexity: 1, minDetectionConfidence: 0.7, minTrackingConfidence: 0.7 });
    hands.onResults(onResults);

    // 4. Inicialização da Câmera
    const camera = new Camera(videoElement, {
        onFrame: async () => {
            await hands.send({ image: videoElement });
        },
        width: 640,
        height: 480
    });
    camera.start();
});