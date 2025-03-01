document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ tramo_vuelo_validaciones.js cargado correctamente");

    function toggleFields(row) {
        let formaPago = row.querySelector("[id$='-forma_pago']");
        let moneda = row.querySelector("[id$='-moneda']");
        let caja = row.querySelector("[id$='-caja']");
        let tasaCambio = row.querySelector("[id$='-tasa_cambio']");
        let cantidadMoneda = row.querySelector("[id$='-cantidad_moneda']");
        let montoEnGramos = row.querySelector("[id$='-pago_en_gramos']");

        if (!formaPago) {
            console.log("⚠️ No se encontró el campo 'forma_pago' en esta fila.");
            return;
        }

        console.log(`📌 Forma de Pago en fila ${formaPago.id}: ${formaPago.value}`);

        if (formaPago.value === "moneda") {
            if (moneda) moneda.disabled = false;
            if (caja) caja.disabled = false;
            if (tasaCambio) tasaCambio.disabled = false;
            if (cantidadMoneda) cantidadMoneda.disabled = false;
            if (montoEnGramos) {
                montoEnGramos.disabled = true;
                montoEnGramos.value = "";
            }
        } else if (formaPago.value === "gramos") {
            if (moneda) moneda.disabled = true;
            if (caja) caja.disabled = true;
            if (tasaCambio) tasaCambio.disabled = true;
            if (cantidadMoneda) cantidadMoneda.disabled = true;
            if (montoEnGramos) montoEnGramos.disabled = false;
        } else if (formaPago.value === "no_aplica") {
            if (moneda) moneda.disabled = true;
            if (caja) caja.disabled = true;
            if (tasaCambio) tasaCambio.disabled = true;
            if (cantidadMoneda) cantidadMoneda.disabled = true;
            if (montoEnGramos) montoEnGramos.disabled = true;
        }
    }

    function applyValidation() {
        let rows = document.querySelectorAll("tr.dynamic-tramos_vuelo");
        rows.forEach(row => {
            let formaPago = row.querySelector("[id$='-forma_pago']");
            if (formaPago) {
                formaPago.addEventListener("change", () => toggleFields(row));
                toggleFields(row);  // Ejecutar al cargar la página
            }
        });
    }

    // Aplicar validación inicial
    applyValidation();

    // **Detectar cuando Django agrega nuevas filas inline**
    let observer = new MutationObserver(function (mutationsList) {
        for (let mutation of mutationsList) {
            if (mutation.type === "childList") {
                console.log("🆕 Nueva fila detectada, aplicando validaciones...");
                applyValidation();
            }
        }
    });

    // **Observar el contenedor de los formularios inline**
    let inlineContainer = document.querySelector("#tramos_vuelo-group");  // Ajusta este ID si es diferente
    if (inlineContainer) {
        observer.observe(inlineContainer, { childList: true, subtree: true });
        console.log("👀 Observando cambios en el formulario inline...");
    } else {
        console.log("⚠️ No se encontró el contenedor de los tramos de vuelo.");
    }
});