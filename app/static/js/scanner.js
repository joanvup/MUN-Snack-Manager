document.addEventListener('DOMContentLoaded', function () {
    const resultContainer = document.getElementById('qr-reader-results');
    const qrReaderDiv = document.getElementById('qr-reader');
    
    // Obtenemos la URL de validación desde un atributo data-* en el HTML.
    // Esto es una buena práctica para no 'hardcodear' URLs en el JS.
    const validationUrl = qrReaderDiv.dataset.validateUrl;

    let lastResult, countResults = 0;

    function onScanSuccess(decodedText, decodedResult) {
        // Para evitar envíos múltiples del mismo QR si se mantiene frente a la cámara.
        if (decodedText !== lastResult) {
            lastResult = decodedText;
            
            // Muestra un mensaje de "Procesando..." al usuario.
            resultContainer.innerHTML = `<div class="p-3 bg-gray-200 rounded text-gray-700">Procesando ID: <strong>${decodedText}</strong>...</div>`;

            // Realiza la petición al backend para validar el QR.
            fetch(validationUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 'id_participante': decodedText })
            })
            .then(response => {
                if (!response.ok) {
                    // Si el servidor responde con un error (ej. 400, 404), lo manejamos aquí.
                    return response.json().then(err => { throw err; });
                }
                return response.json();
            })
            .then(data => {
                // El servidor respondió correctamente. Mostramos el mensaje.
                let messageClass = data.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
                resultContainer.innerHTML = `
                    <div class="p-4 rounded-lg ${messageClass}">
                        <p class="font-bold text-lg">${data.success ? '✅ Éxito' : '❌ Error'}</p>
                        <p>${data.message}</p>
                        ${data.saldo_restante !== undefined ? `<p class="mt-1">Saldo restante: <strong>${data.saldo_restante}</strong></p>` : ''}
                    </div>
                `;
            })
            .catch(error => {
                // Captura errores de red o errores lanzados desde el .then() anterior.
                console.error('Error:', error);
                const errorMessage = error.message || "Error de conexión con el servidor. Inténtalo de nuevo.";
                resultContainer.innerHTML = `<div class="p-4 rounded-lg bg-red-100 text-red-800"><p class="font-bold">Error</p><p>${errorMessage}</p></div>`;
            });
        }
    }
    
    // Configura e inicia el escáner de QR.
    // { fps: 10, qrbox: 250 } -> 10 frames por segundo, y un cuadro de escaneo de 250x250px.
    try {
        var html5QrcodeScanner = new Html5QrcodeScanner(
            "qr-reader", { fps: 10, qrbox: { width: 250, height: 250 } }
        );
        html5QrcodeScanner.render(onScanSuccess);
    } catch (e) {
        console.error("No se pudo iniciar el escáner de QR:", e);
        qrReaderDiv.innerHTML = "<p class='text-red-500'>Error al iniciar el escáner. Asegúrate de tener una cámara y de haber concedido los permisos necesarios.</p>";
    }
});