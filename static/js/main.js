const templates = {
    welcome: {
        es: "¡Hola! Bienvenido a nuestro servicio.",
        en: "Hello! Welcome to our service."
    },
    reminder: {
        es: "Te recordamos tu cita programada.",
        en: "This is a reminder of your scheduled appointment."
    },
    confirmation: {
        es: "Tu solicitud ha sido confirmada.",
        en: "Your request has been confirmed."
    }
};

function updatePreview() {
    const language = $('#language').val();
    const template = $('#template').val();
    const phoneNumber = $('#phoneNumber').val();

    if (template && templates[template]) {
        let message = templates[template][language] || '';
        if (phoneNumber) {
            message += `\n\nNúmero: ${phoneNumber}`;
        }
        $('#messagePreview').text(message);
    }
}

$('#language, #template, #phoneNumber').on('change input', updatePreview);

$('#messageForm').on('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        language: $('#language').val(),
        template: $('#template').val(),
        phoneNumber: $('#phoneNumber').val(),
        message: $('#messagePreview').text()
    };

    fetch('/api/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        alert('Mensaje enviado exitosamente');
    })
    .catch(error => {
        alert('Error al enviar el mensaje');
        console.error('Error:', error);
    });
});