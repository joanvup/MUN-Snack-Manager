document.addEventListener('DOMContentLoaded', function() {
    // ... (código para obtener URLs y contenedores sin cambios) ...
    const qrReaderContainer = document.getElementById('qr-reader');
    const validateUrl = qrReaderContainer.dataset.validateUrl;
    const resultContainer = document.getElementById('qr-reader-results');
    
    let lastResult = null;

    function onScanSuccess(decodedText, decodedResult) {
        // ... (la lógica de parseo y fetch que ya funciona no necesita cambios) ...
        if (decodedText !== lastResult) {
            lastResult = decodedText;
            
            let participantId;
            try {
                const participantData = JSON.parse(decodedText);
                if (participantData && participantData.id) {
                    participantId = participantData.id;
                    resultContainer.innerHTML = `<div class="p-3 bg-gray-200 rounded">Escaneado: <strong>${participantData.nombre || 'Participante'}</strong>. Validando...</div>`;
                } else {
                    throw new Error("El formato del QR es incorrecto (no se encontró 'id').");
                }
            } catch (error) {
                console.error("Error al parsear el QR:", error);
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800"><strong>Error:</strong> Código QR no válido.</div>`;
                setTimeout(() => { lastResult = null; }, 2000); 
                return;
            }

            fetch(validateUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 'id_participante': participantId })
            })
            .then(response => response.json())
            .then(data => {
                let messageClass = data.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
                resultContainer.innerHTML = `
                    <div class="p-4 rounded ${messageClass}">
                        <p class="font-bold">${data.success ? 'Éxito' : 'Error'}</p>
                        <p>${data.message}</p>
                        ${data.saldo_restante !== undefined ? `<p>Saldo restante: ${data.saldo_restante}</p>` : ''}
                    </div>
                `;
                setTimeout(() => { lastResult = null; }, 2000); 
            })
            .catch(error => {
                console.error('Error de conexión:', error);
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800">Error de conexión con el servidor.</div>`;
                setTimeout(() => { lastResult = null; }, 2000);
            });
        }
    }
    
    function onScanFailure(error) {
        // Este callback opcional puede ayudar a diagnosticar problemas.
        // Se llama repetidamente, así que no mostramos un error visible al usuario
        // para no ser molestos, pero lo registramos en la consola para depuración.
        // console.warn(`Código QR no detectado: ${error}`);
    }

    // --- INICIO: CAMBIO CLAVE PARA COMPATIBILIDAD UNIVERSAL ---

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        rememberLastUsedCamera: true,
        // Aquí está la nueva estrategia.
        // Usamos un array de restricciones. El navegador intentará la primera.
        // Si falla con OverconstrainedError, intentará la segunda, y así sucesivamente.
        videoConstraints: [
            { facingMode: { exact: "environment" } }, // 1. Intenta la cámara trasera de forma estricta (para iOS)
            { facingMode: "environment" },            // 2. Si falla, intenta la cámara trasera de forma flexible
            { facingMode: "user" }                     // 3. Si todo lo demás falla, pide la cámara frontal (selfie)
        ]
    };

    const html5QrcodeScanner = new Html5QrcodeScanner("qr-reader", config, /* verbose= */ false);
    
    // --- FIN: CAMBIO CLAVE ---
    
    html5QrcodeScanner.render(onScanSuccess, onScanFailure);
});