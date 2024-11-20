$(document).ready(function() {
    let templatesData = {};

    // Cargar idiomas al iniciar
    fetch('/api/idiomas')
        .then(response => response.json())
        .then(data => {
            const select = $('#language');
            data.forEach(idioma => {
                select.append(`<option value="${idioma.codigo}">${idioma.nombre}</option>`);
            });
        });

    // Activar el selector de departamentos cuando se seleccione un idioma
    $('#language').change(function() {
        const idiomaCodigo = $(this).val();
        const departamentoSelect = $('#departamento');

        departamentoSelect.prop('disabled', true);
        departamentoSelect.html('<option value="">Seleccionar departamento...</option>');

        if (idiomaCodigo) {
            fetch(`/api/departamentos?idioma=${idiomaCodigo}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(dept => {
                        departamentoSelect.append(`<option value="${dept.id}">${dept.nombre}</option>`);
                    });

                    departamentoSelect.prop('disabled', false);
                });
        }
    });

    // Activar y cargar templates al seleccionar un departamento
    $('#departamento').change(function () {
        const departamentoId = $(this).val();
        const idioma = $('#language').val(); // Obtener el idioma seleccionado
        const templateSelect = $('#template');
        const fieldsContainer = $('#fieldsContainer'); // Contenedor de campos adicionales

        // Resetear el campo de templates, la vista previa y los campos adicionales
        templateSelect.prop('disabled', true);
        templateSelect.html('<option value="">Seleccionar template...</option>');
        $('#messagePreview').text('');
        fieldsContainer.html(''); // Limpiar campos adicionales

        if (departamentoId && idioma) {
            fetch(`/api/templates?idioma=${idioma}&departamento_id=${departamentoId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        alert('No se encontraron templates para este departamento e idioma');
                        return;
                    }

                    // Mapear los templates al selector
                    templatesData = data.reduce((acc, template) => {
                        acc[template.template_id] = template;
                        return acc;
                    }, {});

                    data.forEach(template => {
                        templateSelect.append(
                            `<option value="${template.template_id}">${template.template_nombre}</option>`
                        );
                    });

                    // Habilitar el selector de templates
                    templateSelect.prop('disabled', false);
                })
                .catch(error => {
                    console.error('Error al cargar templates:', error);
                });
        } else {
            alert('Debe seleccionar un idioma y un departamento antes de cargar templates.');
        }
    });

    // Cuando cambie la plantilla, mostrar los campos variables
    $('#template').change(function () {
        const templateId = $(this).val();
        const fieldsContainer = $('#fieldsContainer');
        const template = templatesData[templateId];
        
        if (template) {
            // Limpiar los campos previos
            fieldsContainer.html('');

            // Si la plantilla tiene campos variables, los generamos
            if (template.campos_variables) {
                const campos = JSON.parse(template.campos_variables); // Convertir a array

                campos.forEach(campo => {
                    fieldsContainer.append(`
                        <div class="form-group" style="display: none;">
                            <label for="${campo}">${campo}:</label>
                            <input type="text" id="${campo}" class="form-control" placeholder="Ingresa ${campo}" />
                        </div>
                    `);
                });

                // Hacer visibles los campos adicionales
                fieldsContainer.show();
                fieldsContainer.children().each(function() {
                    $(this).fadeIn();
                });
            }

            // Mostrar el mensaje en vista previa
            $('#messagePreview').text(template.mensaje);
        }
    });

    // Actualizar el preview del mensaje
    $('#fieldsContainer').on('input', 'input', function() {
        const templateId = $('#template').val();
        const template = templatesData[templateId];

        if (template) {
            let mensajePreview = template.mensaje;
            $('#fieldsContainer input').each(function() {
                const inputId = $(this).attr('id');
                const inputValue = $(this).val();
                
                // Reemplazar el placeholder en el mensaje por el valor del input
                mensajePreview = mensajePreview.replace(`{${inputId}}`, inputValue);
            });
            
            // Actualizar la vista previa
            $('#messagePreview').text(mensajePreview);
        }
    });

    // Enviar mensaje
    $('#messageForm').on('submit', function(e) {
        e.preventDefault();

        // Obtener los datos del mensaje
        const formData = {
            idioma: $('#language').val(),
            departamento_id: $('#departamento').val(),
            template_id: $('#template').val(),
            phoneNumber: $('#phoneNumber').val(),
            message: $('#messagePreview').text(),
            campos: {} // Aquí almacenamos los valores de los campos personalizados
        };

        // Obtener los valores de los campos adicionales
        $('#fieldsContainer input').each(function() {
            formData.campos[$(this).attr('id')] = $(this).val();
        });
        console.log('JSON a enviar:', formData);
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
});
