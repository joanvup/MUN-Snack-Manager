document.addEventListener('DOMContentLoaded', function() {
    // Obtenemos el contenedor del lector y la URL de validación que pasamos desde el HTML
    const qrReaderContainer = document.getElementById('qr-reader');
    const validateUrl = qrReaderContainer.dataset.validateUrl;
    const resultContainer = document.getElementById('qr-reader-results');
    
    let lastResult = null;
    let qrScanner; // Hacemos el scanner accesible globalmente en este script

    function onScanSuccess(decodedText, decodedResult) {
        // Detener el escaneo inmediatamente para procesar el resultado y evitar múltiples lecturas
        qrScanner.pause();

        if (decodedText !== lastResult) {
            lastResult = decodedText;
            
            let participantId;
            try {
                // 1. Intentamos convertir el texto escaneado en un objeto JavaScript
                const participantData = JSON.parse(decodedText);

                // 2. Verificamos que el objeto tenga una propiedad 'id'
                if (participantData && participantData.id) {
                    participantId = participantData.id;
                    resultContainer.innerHTML = `<div class="p-3 bg-gray-200 rounded">Escaneado: <strong>${participantData.nombre || 'Participante'}</strong>. Validando...</div>`;
                } else {
                    throw new Error("El formato del QR es incorrecto (no se encontró 'id').");
                }
            } catch (error) {
                // 3. Si el QR no es un JSON válido o no tiene 'id', mostramos un error
                console.error("Error al parsear el QR:", error);
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800"><strong>Error:</strong> Código QR no válido.</div>`;
                // Reanudar el escaneo después de un error
                setTimeout(() => {
                    lastResult = null;
                    qrScanner.resume();
                }, 2000); 
                return;
            }

            // 4. Enviamos SOLO el ID extraído a la URL que obtuvimos del HTML
            fetch(validateUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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
                // Reanudar el escaneo después de un resultado
                setTimeout(() => {
                    lastResult = null;
                    qrScanner.resume();
                }, 2000); 
            })
            .catch(error => {
                console.error('Error de conexión:', error);
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800">Error de conexión con el servidor.</div>`;
                setTimeout(() => { lastResult = null; }, 2000);
            });
        } else {
            // Si es el mismo resultado, simplemente reanudamos el escaneo
            qrScanner.resume();
        }
    }
    function onScanFailure(error) {
        // Este callback se llama a menudo, así que lo mantenemos silencioso
        // console.warn(`QR scan error: ${error}`);
    }
    // --- INICIO: CONFIGURACIÓN OPTIMIZADA ---
    const config = {
        fps: 5, // 1. Reducir FPS: Menos cuadros por segundo, pero de mayor calidad.
        qrbox: { width: 250, height: 250 },
        
        // 2. Forzar el uso de la cámara trasera y una resolución más alta (si está disponible)
        videoConstraints: {
            facingMode: { exact: "environment" },
            width: { min: 1280 },
            height: { min: 720 }
        },
        
        // 3. Usar el escáner experimental (puede ser mejor con códigos densos)
        experimentalFeatures: {
            useBarCodeDetectorIfSupported: true
        },
        
        // 4. Mejorar el manejo del enfoque (si el navegador lo soporta)
        focusMode: "continuous",
        
        rememberLastUsedCamera: true
    };
    // --- FIN: CONFIGURACIÓN OPTIMIZADA ---
    // Inicializamos el escáner

    // Inicializamos el escáner con la nueva configuración
    qrScanner = new Html5QrcodeScanner("qr-reader", config, false);
    qrScanner.render(onScanSuccess, onScanFailure);
});