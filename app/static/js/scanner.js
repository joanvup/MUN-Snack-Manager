document.addEventListener('DOMContentLoaded', function() {
    // --- Elementos del DOM ---
    const qrReaderContainer = document.getElementById('qr-reader');
    const validateUrl = qrReaderContainer.dataset.validateUrl;
    const resultContainer = document.getElementById('qr-reader-results');
    const cameraSelectorContainer = document.getElementById('camera-selector-container');
    const cameraSelector = document.getElementById('camera-selector');
    
    let lastResult = null;
    let html5QrcodeScanner; // Hacemos el scanner una variable global en este scope

    // --- Lógica de Escaneo Exitoso (sin cambios) ---
    function onScanSuccess(decodedText, decodedResult) {
        if (decodedText !== lastResult) {
            lastResult = decodedText;
            // ... (el resto de esta función es idéntica a la versión anterior)
            let participantId;
            try {
                const participantData = JSON.parse(decodedText);
                if (participantData && participantData.id) {
                    participantId = participantData.id;
                    resultContainer.innerHTML = `<div class="p-3 bg-gray-200 rounded">Escaneado: <strong>${participantData.nombre || 'Participante'}</strong>. Validando...</div>`;
                } else { throw new Error("QR sin 'id'."); }
            } catch (error) {
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800"><strong>Error:</strong> Código QR no válido.</div>`;
                setTimeout(() => { lastResult = null; }, 2000); 
                return;
            }
            fetch(validateUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ 'id_participante': participantId })})
            .then(response => response.json()).then(data => {
                let messageClass = data.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
                resultContainer.innerHTML = `<div class="p-4 rounded ${messageClass}"><p class="font-bold">${data.success ? 'Éxito' : 'Error'}</p><p>${data.message}</p>${data.saldo_restante !== undefined ? `<p>Saldo restante: ${data.saldo_restante}</p>` : ''}</div>`;
                setTimeout(() => { lastResult = null; }, 2000); 
            }).catch(error => {
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800">Error de conexión con el servidor.</div>`;
                setTimeout(() => { lastResult = null; }, 2000);
            });
        }
    }

    function onScanFailure(error) { /* Opcional: para depuración */ }

    // --- INICIO: LÓGICA MEJORADA DE INICIALIZACIÓN Y SELECCIÓN DE CÁMARA ---

    // Función para iniciar o reiniciar el escáner con una cámara específica
    function startScanner(deviceId) {
        const config = {
            fps: 10,
            qrbox: { width: 250, height: 250 },
            rememberLastUsedCamera: true
        };

        // Si se proporciona un deviceId, lo usamos de forma estricta.
        // Si no, dejamos que la librería decida (comportamiento por defecto).
        if (deviceId) {
            config.videoConstraints = { deviceId: { exact: deviceId } };
        }

        html5QrcodeScanner = new Html5QrcodeScanner("qr-reader", config, false);
        html5QrcodeScanner.render(onScanSuccess, onScanFailure);
    }
    
    // Función principal para configurar el selector de cámaras
    function setupCameraSelector() {
        Html5Qrcode.getCameras().then(cameras => {
            if (cameras && cameras.length) {
                let preferredCameraId = null;

                // Si hay más de una cámara, mostramos el selector
                if (cameras.length > 1) {
                    cameraSelectorContainer.classList.remove('hidden');
                    
                    cameras.forEach(camera => {
                        const option = document.createElement('option');
                        option.value = camera.id;
                        option.innerHTML = camera.label || `Cámara ${cameraSelector.length + 1}`;
                        cameraSelector.appendChild(option);

                        // Intentamos pre-seleccionar una cámara trasera por defecto
                        const label = camera.label.toLowerCase();
                        if (label.includes('back') || label.includes('rear') || label.includes('trasera')) {
                            preferredCameraId = camera.id;
                        }
                    });
                }

                // Si encontramos una cámara trasera preferida, la seleccionamos
                if (preferredCameraId) {
                    cameraSelector.value = preferredCameraId;
                }
                
                // Iniciamos el escáner con la cámara seleccionada (o la primera si no hay preferida)
                startScanner(cameraSelector.value);

                // Añadimos el listener para cambiar de cámara
                cameraSelector.addEventListener('change', () => {
                    if (html5QrcodeScanner && html5QrcodeScanner.isScanning) {
                        html5QrcodeScanner.clear().then(() => {
                            startScanner(cameraSelector.value);
                        }).catch(err => {
                            console.error("Fallo al limpiar el escáner anterior:", err);
                            startScanner(cameraSelector.value); // Intentar iniciar de todas formas
                        });
                    } else {
                        startScanner(cameraSelector.value);
                    }
                });
            }
        }).catch(err => {
            console.error("Error al obtener las cámaras:", err);
            resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800"><strong>Error:</strong> No se pudo acceder a las cámaras del dispositivo. Verifique los permisos.</div>`;
        });
    }

    // Ejecutamos la configuración
    setupCameraSelector();
});