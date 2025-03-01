
document.addEventListener("DOMContentLoaded", function () {
    const avionSelect = document.querySelector("#id_avion");
    const horometroCampo = document.querySelector("div.form-row.field-mostrar_ultimo_horometro div.readonly");

    if (!avionSelect) {
        console.error("❌ No se encontró el campo de selección de avión.");
        return;
    }

    avionSelect.addEventListener("change", function () {
        console.log("🔄 Cambio detectado en el avión. ID seleccionado:", avionSelect.value);

        fetch(`/registro_vuelos/api/get_horometro/?avion_id=${avionSelect.value}`)
            .then(response => response.json())
            .then(data => {
                console.log("✅ Horómetro recibido:", data);

                if (horometroCampo) {
                    horometroCampo.textContent = data.horometro;
                    console.log("✅ Horómetro actualizado correctamente.");
                } else {
                    console.error("⚠ No se encontró el campo de horómetro en el HTML.");
                }
            })
            .catch(error => console.error("❌ Error al obtener el horómetro:", error));
    });
});