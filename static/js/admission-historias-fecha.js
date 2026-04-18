(function () {
  const TOAST_DURATION_MS = 3000;

  function toggleStatus(element) {
    if (element.innerText === "Pendiente") {
      element.innerText = "Recibido";
      element.classList.remove("btn-status-pendiente");
      element.classList.add("btn-status-recibido");
    } else {
      element.innerText = "Pendiente";
      element.classList.remove("btn-status-recibido");
      element.classList.add("btn-status-pendiente");
    }
  }

  function getToastContainer() {
    let container = document.getElementById("admissionToastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "admissionToastContainer";
      container.className = "toast-container position-fixed bottom-0 end-0 p-3";
      document.body.appendChild(container);
    }
    return container;
  }

  function showToast(message, tone = "success") {
    if (typeof bootstrap === "undefined" || !bootstrap.Toast) {
      console.warn(message);
      return;
    }
    const container = getToastContainer();
    const toast = document.createElement("div");
    toast.className = `toast admission-toast ${tone}`;
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "assertive");
    toast.setAttribute("aria-atomic", "true");
    toast.innerHTML = `
      <div class="toast-body fw-semibold">${message}</div>
      <div class="toast-progress"></div>
    `;
    container.appendChild(toast);

    const toastInstance = bootstrap.Toast.getOrCreateInstance(toast, { autohide: false });
    toastInstance.show();
    window.setTimeout(() => toastInstance.hide(), TOAST_DURATION_MS);
    toast.addEventListener("hidden.bs.toast", () => toast.remove(), { once: true });
  }

  function buildRowHtml(medicosOptions) {
    return `
      <td style="border-right: 2px solid #dee2e6;"><input type="text" class="form-control border-0 text-center numero-historia"></td>
      <td style="border-right: 2px solid #dee2e6;"><select class="form-select border-0 medico-select"><option value="">Seleccionar...</option>${medicosOptions}</select></td>
      <td class="especialidad-cell" style="border-right: 2px solid #dee2e6;">Sin especialidad</td>
      <td style="border-right: 2px solid #dee2e6;"><select class="form-select border-0 text-center turno-select"><option value="M">M</option><option value="T">T</option></select></td>
      <td style="border-right: 2px solid #dee2e6;"><input type="text" class="form-control border-0 text-center responsable-input" placeholder="Nombre responsable"></td>
      <td><span class="status-badge btn-status-pendiente js-toggle-status">Pendiente</span></td>
      <td><button type="button" class="btn btn-sm btn-outline-danger js-delete-historia" title="Eliminar historia"><i class="bi bi-trash"></i></button></td>
    `;
  }

  function addRow(medicosOptions) {
    const tbody = document.getElementById("tbodyHistorias");
    const newRow = document.createElement("tr");
    newRow.className = "record-row";
    newRow.dataset.historiaId = "";
    newRow.innerHTML = buildRowHtml(medicosOptions);
    tbody.appendChild(newRow);
    refreshSideAddButton();
    applyFilters();
    newRow.querySelector(".numero-historia").focus();
  }

  function syncEspecialidadFromMedico(row) {
    if (!row) return;
    const medicoSelect = row.querySelector(".medico-select");
    const especialidadCell = row.querySelector(".especialidad-cell");
    if (!medicoSelect || !especialidadCell) return;

    const selectedOption = medicoSelect.options[medicoSelect.selectedIndex];
    const especialidad = selectedOption?.dataset?.especialidad || "Sin especialidad";
    especialidadCell.innerText = especialidad;
  }

  function applyFilters() {
    const especialidadFilter = document.getElementById("filterEspecialidad")?.value || "";
    const turnoFilter = document.getElementById("filterTurno")?.value || "";
    const estadoFilter = document.getElementById("filterEstado")?.value || "";

    const rows = document.querySelectorAll(".record-row");
    rows.forEach((row) => {
      const especialidad = row.querySelector(".especialidad-cell")?.innerText?.trim() || "";
      const turno = row.querySelector(".turno-select")?.value || "";
      const estado = row.querySelector(".status-badge")?.innerText?.trim() || "";

      const matchEspecialidad = !especialidadFilter || especialidad === especialidadFilter;
      const matchTurno = !turnoFilter || turno === turnoFilter;
      const matchEstado = !estadoFilter || estado === estadoFilter;

      row.style.display = matchEspecialidad && matchTurno && matchEstado ? "" : "none";
    });
    refreshSideAddButton();
  }

  function refreshSideAddButton() {
    const addButton = document.getElementById("btnSideAddRow");
    const tableWrap = document.getElementById("recordsTableWrap");
    const rows = document.querySelectorAll(".record-row");
    if (!addButton || !tableWrap) return;

    if (!rows.length) {
      addButton.style.top = "54px";
      addButton.style.display = "inline-flex";
      return;
    }

    const lastRow = rows[rows.length - 1];
    const tableRect = tableWrap.getBoundingClientRect();
    const rowRect = lastRow.getBoundingClientRect();
    const topPx = rowRect.top - tableRect.top + rowRect.height / 2 - 14;
    addButton.style.top = `${Math.max(8, topPx)}px`;
    addButton.style.display = "inline-flex";
  }

  async function persistStatus(historiaId, nuevoEstado) {
    const response = await fetch("/admission/cambiar_estado", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ historia_id: parseInt(historiaId, 10), estado: nuevoEstado }),
    });
    if (!response.ok) return false;
    const data = await response.json().catch(() => ({}));
    return data.status === "success";
  }

  async function deleteHistoria(historiaId) {
    const response = await fetch("/admission/eliminar_historia", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ historia_id: parseInt(historiaId, 10) }),
    });
    if (!response.ok) return false;
    const data = await response.json().catch(() => ({}));
    return data.status === "success";
  }

  function clearFieldErrors() {
    document.querySelectorAll(".field-error").forEach((field) => field.classList.remove("field-error"));
  }

  function markFieldError(field) {
    field.classList.add("field-error");
  }

  function rowConflictNumeroDia(numA, medA, turnA, numB, medB, turnB) {
    if (!numA || !numB) return false;
    if (numA.toLowerCase() !== numB.toLowerCase()) return false;
    return medA === medB || turnA === turnB;
  }

  function findLocalDuplicateNumeroHistoriaInputs() {
    const rows = [...document.querySelectorAll(".record-row")];
    const dups = new Set();
    for (let i = 0; i < rows.length; i += 1) {
      const ra = rows[i];
      const na = ra.querySelector(".numero-historia")?.value?.trim() || "";
      const ma = ra.querySelector(".medico-select")?.value || "";
      const ta = (ra.querySelector(".turno-select")?.value || "").trim().toUpperCase();
      for (let j = i + 1; j < rows.length; j += 1) {
        const rb = rows[j];
        const nb = rb.querySelector(".numero-historia")?.value?.trim() || "";
        const mb = rb.querySelector(".medico-select")?.value || "";
        const tb = (rb.querySelector(".turno-select")?.value || "").trim().toUpperCase();
        if (rowConflictNumeroDia(na, ma, ta, nb, mb, tb)) {
          dups.add(ra.querySelector(".numero-historia"));
          dups.add(rb.querySelector(".numero-historia"));
        }
      }
    }
    return [...dups].filter(Boolean);
  }

  function parseRows() {
    const rows = document.querySelectorAll(".record-row");
    const historias = [];
    const invalidFields = [];

    rows.forEach((row) => {
      const historiaId = row.dataset.historiaId || "";
      const numeroInput = row.querySelector(".numero-historia");
      const medicoSelect = row.querySelector(".medico-select");
      const turnoSelect = row.querySelector(".turno-select");
      const responsableInput = row.querySelector(".responsable-input");
      const estadoBadge = row.querySelector(".status-badge");

      const numeroHistoria = numeroInput.value.trim();
      const medicoId = medicoSelect.value;
      const turno = turnoSelect.value;
      const responsableNombre = responsableInput.value.trim();
      const estado = estadoBadge.innerText.trim();
      const hasAnyField = numeroHistoria || medicoId || responsableNombre;
      const hasAllFields = numeroHistoria && medicoId && responsableNombre;

      if (!historiaId && hasAnyField && !hasAllFields) {
        if (!numeroHistoria) invalidFields.push(numeroInput);
        if (!medicoId) invalidFields.push(medicoSelect);
        if (!responsableNombre) invalidFields.push(responsableInput);
      }

      if (!historiaId && hasAllFields) {
        historias.push({
          numero_historia: numeroHistoria,
          medico_id: parseInt(medicoId, 10),
          turno,
          responsable_triaje: responsableNombre,
          estado,
        });
      }
    });

    return { historias, invalidFields };
  }

  function setSavingState(isSaving) {
    const saveButton = document.getElementById("btnSaveRecords");
    if (!saveButton) return;
    saveButton.disabled = isSaving;
    saveButton.innerHTML = isSaving
      ? '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Guardando...'
      : '<i class="bi bi-check-lg"></i> Guardar';
  }

  async function saveRecords() {
    clearFieldErrors();
    const { historias, invalidFields } = parseRows();

    if (invalidFields.length) {
      invalidFields.forEach(markFieldError);
      showToast("Hay filas incompletas. Completa N° Historia, Médico y Resp. Triaje.", "warning");
      return;
    }

    if (!historias.length) {
      showToast("Agrega al menos un registro antes de guardar.", "warning");
      return;
    }

    const dupNumInputs = findLocalDuplicateNumeroHistoriaInputs();
    if (dupNumInputs.length) {
      dupNumInputs.forEach((field) => field?.classList.add("field-error"));
      showToast(
        "Mismo número el mismo día: no puede repetirse con el mismo médico o el mismo turno. " +
          "Solo puede repetirse con otro médico y otro turno.",
        "warning"
      );
      return;
    }

    setSavingState(true);

    try {
      const fechaObjetivo = document.body.getAttribute("data-fecha-objetivo")?.trim() || "";
      const payload = fechaObjetivo ? { historias, fecha_objetivo: fechaObjetivo } : { historias };

      const response = await fetch("/admission/guardar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => ({}));

      if (response.ok) {
        showToast("Historias guardadas correctamente.", "success");
        window.setTimeout(() => {
          window.location.href = result.redirect_url || "/admission/fechas";
        }, 400);
      } else {
        showToast(result.message || "Error al guardar los registros.", "danger");
      }
    } catch (error) {
      console.error("Error:", error);
      showToast("Error al conectar con el servidor.", "danger");
    } finally {
      setSavingState(false);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const medicosOptions = document.getElementById("medicos-options-template")?.innerHTML || "";

    refreshSideAddButton();
    document.querySelectorAll(".record-row").forEach(syncEspecialidadFromMedico);
    applyFilters();
    document.getElementById("btnSideAddRow")?.addEventListener("click", () => addRow(medicosOptions));
    document.getElementById("btnSaveRecords")?.addEventListener("click", saveRecords);
    document.getElementById("filterEspecialidad")?.addEventListener("change", applyFilters);
    document.getElementById("filterTurno")?.addEventListener("change", applyFilters);
    document.getElementById("filterEstado")?.addEventListener("change", applyFilters);
    document.getElementById("btnClearFilters")?.addEventListener("click", () => {
      const filterEspecialidad = document.getElementById("filterEspecialidad");
      const filterTurno = document.getElementById("filterTurno");
      const filterEstado = document.getElementById("filterEstado");
      if (filterEspecialidad) filterEspecialidad.value = "";
      if (filterTurno) filterTurno.value = "";
      if (filterEstado) filterEstado.value = "";
      applyFilters();
    });

    document.addEventListener("input", (event) => {
      if (event.target.classList.contains("field-error")) {
        event.target.classList.remove("field-error");
      }
    });

    document.addEventListener("change", (event) => {
      if (event.target.classList.contains("medico-select")) {
        const row = event.target.closest(".record-row");
        syncEspecialidadFromMedico(row);
      }
      if (event.target.classList.contains("medico-select") || event.target.classList.contains("turno-select")) {
        applyFilters();
      }
    });

    window.addEventListener("resize", refreshSideAddButton);

    document.addEventListener("click", async (event) => {
      const statusEl = event.target.closest(".js-toggle-status");
      if (statusEl) {
        const row = statusEl.closest(".record-row");
        const historiaId = row?.dataset?.historiaId;
        toggleStatus(statusEl);
        const newEstado = statusEl.innerText.trim();

        if (historiaId) {
          const ok = await persistStatus(historiaId, newEstado);
          if (!ok) {
            toggleStatus(statusEl);
            showToast("No se pudo actualizar el estado.", "danger");
            return;
          }
          showToast(`Estado actualizado a ${newEstado}.`, "success");
        }
        applyFilters();
      }

      const deleteBtn = event.target.closest(".js-delete-historia");
      if (deleteBtn) {
        const row = deleteBtn.closest(".record-row");
        if (!row) return;
        const historiaId = row.dataset.historiaId;

        if (historiaId) {
          const ok = await deleteHistoria(historiaId);
          if (!ok) {
            showToast("No se pudo eliminar la historia.", "danger");
            return;
          }
        }

        row.remove();
        refreshSideAddButton();
        applyFilters();
        showToast("Historia eliminada.", "success");
      }

    });
  });
})();

