document.addEventListener("DOMContentLoaded", function () {
    const fechaInput = document.querySelector("input[name='fecha']");
    const horaSelect = document.querySelector("select[name='hora']");
    const dentistaIdInput = document.getElementById("selected_dentist_id");
    const reservarSection = document.getElementById("section-reservar");
    const turnosAgendadosSection = document.getElementById("section-agendados");
    const listaTurnos = document.getElementById("lista-turnos");
    const seleccionDentistaSection = document.getElementById("section-seleccion-dentista");
    const inicioSection = document.getElementById("section-inicio");
    const userEmail = document.getElementById("user-email")?.textContent.trim();

    if (userEmail === "dentistafunes@gmail.com") {
        console.log("🔹 Usuario administrador detectado.");
        mostrarSeccion("section-agendados");
    } else {
        mostrarSeccion("section-inicio");
    }

    if (!fechaInput || !dentistaIdInput || !horaSelect) {
        console.error("❌ No se encontraron los elementos del formulario.");
        return;
    }

    if (listaTurnos && listaTurnos.children.length > 0) {
        turnosAgendadosSection.style.display = "block";
    } else {
        turnosAgendadosSection.style.display = "none";
    }

    fechaInput.addEventListener("change", function () {
        const fecha = this.value;
        const dentistaId = dentistaIdInput.value;

        if (!dentistaId) {
            alert("⚠️ Por favor, selecciona un dentista antes de elegir la fecha.");
            return;
        }

        // Mostrar spinner mientras se cargan los horarios
        horaSelect.innerHTML = '<option disabled>Cargando horarios...</option>';

        fetch(`/api/horarios_disponibles?dentista_id=${dentistaId}&fecha=${fecha}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Error al cargar los horarios");
                }
                return response.json();
            })
            .then(data => {
                console.log("✅ Horarios recibidos:", data);
                horaSelect.innerHTML = "";

                if (!data.horarios || data.horarios.length === 0) {
                    horaSelect.innerHTML = '<option disabled>No hay horarios disponibles</option>';
                    return;
                }

                data.horarios.forEach(horario => {
                    const option = document.createElement("option");
                    option.value = horario.hora;
                    option.textContent = horario.hora;

                    if (!horario.disponible) {
                        option.disabled = true;
                        option.style.color = "gray";
                        option.textContent += " (Ocupado)";
                    }

                    horaSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error("❌ Error al cargar los horarios:", error);
                horaSelect.innerHTML = '<option disabled>Error al cargar los horarios</option>';
            });
    });

    const urlParams = new URLSearchParams(window.location.search);
    const redirectTo = urlParams.get("redirect_to");

    if (redirectTo === "agendados") {
        mostrarSeccion("section-agendados");
    }
});

function selectDentist(id, name) {
    document.getElementById("selected_dentist_id").value = id;
    document.getElementById("dentista_nombre").value = name;
    mostrarSeccion("section-reservar");
}

function mostrarSeccion(idSeccion) {
    const secciones = ["section-inicio", "section-seleccion-dentista", "section-reservar", "section-agendados"];

    secciones.forEach(seccion => {
        const elemento = document.getElementById(seccion);
        if (elemento) {
            elemento.style.display = (seccion === idSeccion) ? "block" : "none";
        }
    });

    const sectionElement = document.getElementById(idSeccion);
    if (sectionElement) {
        sectionElement.scrollIntoView({ behavior: "smooth" });
    }
}

document.querySelectorAll(".navbar-nav .nav-link").forEach(link => {
    link.addEventListener("click", function () {
        const navbarToggler = document.querySelector(".navbar-toggler");
        if (navbarToggler && window.innerWidth < 992) {
            navbarToggler.click();
        }
    });
});