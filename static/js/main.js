$(document).ready(function() {
    let templatesData = {};
    let departamentosMap = {}; // Mapa para departamentos
    let idiomasMap = {}; // Mapa para idiomas

    // Cargar los departamentos en el mapa
    fetch('/api/departamentos')
        .then(response => response.json())
        .then(data => {
            console.log('Departamentos cargados:', data);

            data.forEach(depto => {
                departamentosMap[depto.id] = depto.nombre;
            });

            // Después de cargar los departamentos, cargar los idiomas
            loadLanguages();
        })
        .catch(error => {
            console.error('Error al cargar departamentos:', error);
        });

    // Función para cargar los idiomas
    function loadLanguages() {
        fetch('/api/idiomas')
            .then(response => response.json())
            .then(data => {
                const select = $('#language');
                data.forEach(idioma => {
                    idiomasMap[idioma.codigo] = idioma.nombre;
                    select.append(`<option value="${idioma.codigo}">${idioma.nombre}</option>`);
                });

                // Ahora que los idiomas están cargados, cargar los templates y el historial
                loadTemplates();
                loadMessageHistory();
            })
            .catch(error => {
                console.error('Error al cargar idiomas:', error);
            });
    }

    // Función para cargar los templates
    function loadTemplates() {
        const idiomaSeleccionado = $('#language').val(); // Idioma seleccionado en el selector

        // Verificar si ya se ha seleccionado un idioma para cargar los templates
        if (idiomaSeleccionado) {
            fetch(`/api/templates?idioma=${idiomaSeleccionado}`)
                .then(response => response.json())
                .then(data => {
                    templatesData = data.reduce((acc, template) => {
                        acc[template.template_id] = template; // Almacena el template completo
                        return acc;
                    }, {});

                    // Limpiar el selector de templates antes de agregar los nuevos templates
                    const templateSelect = $('#template');
                    templateSelect.html('<option value="">Seleccionar template...</option>');

                    // Agregar templates al selector
                    data.forEach(template => {
                        templateSelect.append(
                            `<option value="${template.template_id}">${template.template_nombre}</option>`
                        );
                    });

                    // Llamar a la función que actualizará el historial de mensajes
                    loadMessageHistory();
                })
                .catch(error => {
                    console.error('Error al cargar templates:', error);
                });
        }
    }

    // Función para cargar el historial de mensajes
    function loadMessageHistory() {
        fetch('/api/historial-mensajes')
            .then(response => response.json())
            .then(data => {
                console.log('Historial de mensajes cargado:', data);
                    
                const tableBody = $('#historyTableBody');
                
                tableBody.html(''); // Limpiar la tabla antes de cargar los datos

                data.forEach(message => {
                    const departamentoNombre = departamentosMap[message.departamento_id] || 'Sin departamento';
                    const idiomaNombre = idiomasMap[message.idioma] || 'Sin idioma';
                    const template = templatesData[message.template_id] ? templatesData[message.template_id].template_nombre : 'Sin template';
                    const numero = message.numero_destino || 'No disponible';
                    const mensaje = message.mensaje || 'Mensaje no disponible';
                    const fecha = new Date(message.fecha_envio).toLocaleString() || 'Fecha no disponible';

                    // Agregar una fila en la tabla
                    tableBody.append(`
                        <tr>
                            <td>${idiomaNombre}</td>
                            <td>${departamentoNombre}</td>
                            <td>${template}</td>
                            <td>${numero}</td>
                            <td>${mensaje}</td>
                            <td>${fecha}</td>
                        </tr>
                    `);
                });
            })
            .catch(error => {
                console.error('Error al cargar el historial de mensajes:', error);
            });
    }

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
            const url = `/api/templates?idioma=${idioma}&departamento_id=${departamentoId}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        alert('No se encontraron templates para este departamento e idioma');
                        return;
                    }

                    // Mapear los templates al selector
                    templatesData = data.reduce((acc, template) => {
                        acc[template.template_id] = template; // Almacena el template completo
                        return acc;
                    }, {});

                    // Limpiar el select antes de agregar los nuevos templates
                    templateSelect.html('<option value="">Seleccionar template...</option>');

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
            } else {
                // Si no tiene campos variables, no mostrar nada
                fieldsContainer.hide();
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
                
                // Reemplazar el placeholder en el mensaje por el valor del input solo si el valor existe
                if (inputValue) {
                    mensajePreview = mensajePreview.replace(`{${inputId}}`, inputValue);
                }
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
            mensaje: $('#messagePreview').text(),
        };

        // Enviar los datos al servidor
        fetch('/api/enviar-mensaje', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        })
            .then(response => response.json())
            .then(data => {
                console.log('Mensaje enviado:', data);
                loadMessageHistory(); // Recargar el historial de mensajes después de enviar
            })
            .catch(error => {
                console.error('Error al enviar el mensaje:', error);
            });
    });
});
