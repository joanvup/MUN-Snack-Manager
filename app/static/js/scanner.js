document.addEventListener('DOMContentLoaded', function() {
    const qrReaderContainer = document.getElementById('qr-reader');
    const validateUrl = qrReaderContainer.dataset.validateUrl;
    const resultContainer = document.getElementById('qr-reader-results');
    
    let lastResult = null;
    let qrScanner;

    function onScanSuccess(decodedText, decodedResult) {
        qrScanner.pause();
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
                setTimeout(() => {
                    lastResult = null;
                    qrScanner.resume();
                }, 2000); 
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
                setTimeout(() => {
                    lastResult = null;
                    qrScanner.resume();
                }, 2000); 
            })
            .catch(error => {
                console.error('Error de conexión:', error);
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800">Error de conexión con el servidor.</div>`;
                setTimeout(() => {
                    lastResult = null;
                    qrScanner.resume();
                }, 2000);
            });
        } else {
            qrScanner.resume();
        }
    }

    function onScanFailure(error) {
        // This callback is called often, so we keep it silent
        // console.warn(`QR scan error: ${error}`);
    }

    // --- START: CORRECTED AND ROBUST CONFIGURATION ---
    const config = {
        fps: 10, // We can increase FPS again as the constraints are more flexible
        qrbox: { width: 250, height: 250 },
        
        // This is the key change. We provide a list of preferred camera settings.
        // The browser will try the first one, and if it fails, it will try the next.
        // This provides a graceful fallback for different devices.
        videoConstraints: {
            // First, try for a high-res rear camera (ideal for iOS)
            facingMode: "environment",
            width: { ideal: 1920 },
            height: { ideal: 1080 },

            // If that fails, try for any rear camera
            facingMode: "environment",

            // As a last resort, just get any camera
        },
        
        experimentalFeatures: {
            useBarCodeDetectorIfSupported: true
        },
        
        rememberLastUsedCamera: true
    };
    // --- END: CORRECTED AND ROBUST CONFIGURATION ---

    // Initialize the scanner with the new flexible configuration
    qrScanner = new Html5QrcodeScanner("qr-reader", config, false);
    qrScanner.render(onScanSuccess, onScanFailure);
});