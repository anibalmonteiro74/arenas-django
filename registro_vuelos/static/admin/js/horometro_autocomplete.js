$(document).ready(function() {
    // Función para obtener el último horómetro
    function getLastHorometro() {
        console.log("Obteniendo último horómetro...");
        var avion_id = $('#id_avion').val();
        console.log("Avión seleccionado ID:", avion_id);
        
        if (avion_id) {
            $.ajax({
                url: '/api/get_horometro/',
                data: {'avion_id': avion_id},
                dataType: 'json',
                success: function(data) {
                    console.log("Horómetro obtenido:", data.horometro);
                    
                    // Actualizar el campo horometro_inicio del primer tramo
                    setTimeout(function() {
                        $('.dynamic-tramos_vuelo input[id$="-horometro_inicio"]').first().val(data.horometro);
                        
                        // También actualizar el campo readonly en la sección general
                        $('#id_mostrar_ultimo_horometro').text(data.horometro);
                        $('.field-mostrar_ultimo_horometro .readonly').text(data.horometro);
                    }, 300);
                },
                error: function(xhr, status, error) {
                    console.error("Error al obtener horómetro:", error);
                    console.error("Estado:", status);
                    console.error("Respuesta:", xhr.responseText);
                }
            });
        }
    }
    
    // Múltiples formas de capturar el cambio de avión
    $('#id_avion').on('change', function() {
        console.log("Avión cambiado mediante evento change");
        getLastHorometro();
    });
    
    // Para select2 o widgets avanzados
    $(document).on('change', '#id_avion', function() {
        console.log("Avión cambiado mediante evento delegado");
        getLastHorometro();
    });
    
    // Para widgets de selección de Jazzmin
    $(document).on('select2:select', '#id_avion', function() {
        console.log("Avión cambiado mediante select2:select");
        getLastHorometro();
    });
    
    // Para controles estándar de Django
    $(document).on('input', '#id_avion', function() {
        console.log("Avión cambiado mediante input");
        getLastHorometro();
    });
    
    // También ejecutar cuando se añade un nuevo tramo
    $(document).on('click', '.add-row a', function() {
        console.log("Añadiendo nuevo tramo...");
        setTimeout(function() {
            // Obtener el último horómetro_fin y usarlo como inicio para el nuevo tramo
            var lastHorometroFin = $('.dynamic-tramos_vuelo input[id$="-horometro_fin"]').eq(-2).val();
            console.log("Último horómetro fin:", lastHorometroFin);
            
            if (lastHorometroFin) {
                $('.dynamic-tramos_vuelo input[id$="-horometro_inicio"]').last().val(lastHorometroFin);
            } else {
                getLastHorometro();
            }
        }, 300);
    });
    
    // Inicializar si ya hay un avión seleccionado al cargar la página
    console.log("Verificando avión inicial...");
    setTimeout(function() {
        if ($('#id_avion').val()) {
            console.log("Avión inicial encontrado:", $('#id_avion').val());
            getLastHorometro();
        }
    }, 500);
    
    console.log("🚀 horometro_autocomplete.js cargado correctamente");
});