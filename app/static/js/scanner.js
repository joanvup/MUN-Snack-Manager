document.addEventListener('DOMContentLoaded', function() {
    // Obtenemos el contenedor del lector y la URL de validación que pasamos desde el HTML
    const qrReaderContainer = document.getElementById('qr-reader');
    const validateUrl = qrReaderContainer.dataset.validateUrl;
    const resultContainer = document.getElementById('qr-reader-results');
    
    let lastResult = null;

    function onScanSuccess(decodedText, decodedResult) {
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
                setTimeout(() => { lastResult = null; }, 2000); 
                return; // Detenemos la ejecución
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
            })
            .catch(error => {
                console.error('Error de conexión:', error);
                resultContainer.innerHTML = `<div class="p-4 rounded bg-red-100 text-red-800">Error de conexión con el servidor.</div>`;
                setTimeout(() => { lastResult = null; }, 2000);
            });
        }
    }

    // Inicializamos el escáner
    const html5QrcodeScanner = new Html5QrcodeScanner(
        "qr-reader", 
        { 
            fps: 10, 
            qrbox: { width: 250, height: 250 } 
        },
        false
    );
    html5QrcodeScanner.render(onScanSuccess);
});