(function () {
  const TOAST_DURATION_MS = 3000;
  let allRegistros = [];
  let filteredRegistros = [];
  let activeQuickFilter = "all";
  let registroModal = null;
  let confirmDeleteModal = null;
  let pendingDeleteRow = null;
  let activeModalFecha = null;

  function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeEspecialidadLabel(raw) {
    const text = (raw || "").trim();
    if (!text || text.toUpperCase() === "N/A") return "Sin especialidad";
    return text;
  }

  function parseDate(fecha) {
    const [d, m, y] = fecha.split("/");
    return new Date(`${y}-${m}-${d}T00:00:00`);
  }

  function formatInputDateToDisplay(inputDateValue) {
    if (!inputDateValue) return "";
    const [year, month, day] = inputDateValue.split("-");
    return `${day}/${month}/${year}`;
  }

  function applyQuickFilter(items) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (activeQuickFilter === "today") {
      return items.filter((item) => {
        const itemDate = parseDate(item.fecha);
        itemDate.setHours(0, 0, 0, 0);
        return itemDate.getTime() === today.getTime();
      });
    }

    if (activeQuickFilter === "last7") {
      const threshold = new Date(today);
      threshold.setDate(threshold.getDate() - 6);
      return items.filter((item) => {
        const itemDate = parseDate(item.fecha);
        itemDate.setHours(0, 0, 0, 0);
        return itemDate >= threshold && itemDate <= today;
      });
    }

    return items;
  }

  function applySearchFilter() {
    const selectedDateText = formatInputDateToDisplay(document.getElementById("searchDateInput")?.value || "");

    let baseItems = applyQuickFilter(allRegistros);
    baseItems = baseItems.filter((item) => {
      const matchDate = !selectedDateText || item.fecha === selectedDateText;
      return matchDate;
    });

    filteredRegistros = baseItems;
    renderTable();
  }

  function renderTable() {
    const container = document.getElementById("recordsContainer");
    const noRecords = document.getElementById("noRecordsMessage");
    const summary = document.getElementById("recordsSummary");

    if (filteredRegistros.length === 0) {
      container.innerHTML = "";
      noRecords.classList.remove("d-none");
      if (summary) {
        summary.innerHTML =
          '<span class="summary-pill summary-pill-muted"><i class="bi bi-info-circle me-1"></i>Sin carpetas con el filtro actual</span>';
      }
    } else {
      noRecords.classList.add("d-none");
      let html = "";
      let totalHistorias = 0;
      let totalPend = 0;
      let totalRec = 0;
      filteredRegistros.forEach((item) => {
        const total = item.total || 0;
        const pendientes = item.pendientes || 0;
        const recibidas = item.recibidas || 0;
        totalHistorias += total;
        totalPend += pendientes;
        totalRec += recibidas;

        let pctRec = 0;
        let pctPend = 0;
        if (total > 0) {
          pctRec = Math.round((recibidas / total) * 1000) / 10;
          pctPend = Math.round((pendientes / total) * 1000) / 10;
        }

        const fechaSafe = escapeHtml(item.fecha);
        const fechaAttr = String(item.fecha).replace(/"/g, "");
        html += `<button type="button" class="record-card record-folder-btn" data-fecha="${fechaAttr}">`;
        html += '<div class="record-card-top">';
        html += '<div class="record-folder-icon"><i class="bi bi-folder2-open"></i></div>';
        html += '<div class="record-card-heading">';
        html += `<div class="record-date">${fechaSafe}</div>`;
        html += '<div class="record-caption">Historias clínicas del día</div>';
        html += "</div></div>";

        html += '<div class="record-progress-block">';
        html += '<div class="record-progress-head">';
        html += `<span class="record-progress-stat record-progress-stat--ok"><i class="bi bi-check2-circle me-1"></i>${pctRec}% recibidas</span>`;
        html += `<span class="record-progress-stat record-progress-stat--pend"><i class="bi bi-hourglass-split me-1"></i>${pctPend}% pendientes</span>`;
        html += "</div>";
        html += '<div class="record-progress-track" role="img" aria-label="Proporción recibidas y pendientes">';
        html += `<div class="record-progress-seg record-progress-seg--rec" style="width:${pctRec}%;"></div>`;
        html += `<div class="record-progress-seg record-progress-seg--pend" style="width:${pctPend}%;"></div>`;
        html += "</div></div>";

        html += '<div class="record-meta">';
        html += `<span class="meta-badge meta-total"><i class="bi bi-journal-text me-1"></i>${total} total</span>`;
        html += `<span class="meta-badge meta-pendientes"><i class="bi bi-hourglass-split me-1"></i>${pendientes} pend.</span>`;
        html += `<span class="meta-badge meta-recibidas"><i class="bi bi-check2-circle me-1"></i>${recibidas} recib.</span>`;
        html += "</div>";

        html += '<div class="record-card-footer">';
        html += '<span class="record-open-label">Abrir carpeta</span>';
        html += '<span class="record-open-icon"><i class="bi bi-chevron-right"></i></span>';
        html += "</div>";
        html += "</button>";
      });
      container.innerHTML = html;
      if (summary) {
        const n = filteredRegistros.length;
        summary.innerHTML = `
          <span class="summary-pill"><i class="bi bi-calendar3 me-1"></i><strong>${n}</strong> ${n === 1 ? "carpeta" : "carpetas"}</span>
          <span class="summary-pill"><i class="bi bi-journal-text me-1"></i><strong>${totalHistorias}</strong> historias</span>
          <span class="summary-pill summary-pill-warn"><i class="bi bi-hourglass-split me-1"></i><strong>${totalPend}</strong> pendientes</span>
          <span class="summary-pill summary-pill-ok"><i class="bi bi-check2-circle me-1"></i><strong>${totalRec}</strong> recibidas</span>
        `;
      }
    }
  }

  function setQuickFilter(filterName) {
    activeQuickFilter = filterName;
    document.querySelectorAll(".quick-filter-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-filter") === filterName);
    });
    applySearchFilter();
  }

  function getTodayDisplayDate() {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, "0");
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const year = now.getFullYear();
    return `${day}/${month}/${year}`;
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
    if (typeof bootstrap === "undefined" || !bootstrap.Toast) return;
    const container = getToastContainer();
    const toast = document.createElement("div");
    toast.className = `toast admission-toast ${tone}`;
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "assertive");
    toast.setAttribute("aria-atomic", "true");
    toast.innerHTML = `<div class="toast-body fw-semibold">${message}</div><div class="toast-progress"></div>`;
    container.appendChild(toast);
    const instance = bootstrap.Toast.getOrCreateInstance(toast, { autohide: false });
    instance.show();
    window.setTimeout(() => instance.hide(), TOAST_DURATION_MS);
    toast.addEventListener("hidden.bs.toast", () => toast.remove(), { once: true });
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

  function openRegistroModal(fechaDisplay) {
    activeModalFecha = fechaDisplay;
    const titleEl = document.getElementById("registroModalTitle");
    if (titleEl) {
      titleEl.innerText = `Nuevo registro de historias - ${fechaDisplay}`;
    }
    registroModal?.show();
  }

  function toggleStatus(element) {
    if (element.innerText.trim() === "Pendiente") {
      element.innerText = "Recibido";
      element.classList.remove("btn-status-pendiente");
      element.classList.add("btn-status-recibido");
    } else {
      element.innerText = "Pendiente";
      element.classList.remove("btn-status-recibido");
      element.classList.add("btn-status-pendiente");
    }
  }

  function buildModalRowHtml(medicosOptions, rowData = {}) {
    const numeroHistoria = escapeHtml(rowData.numero_historia || "");
    const turno = rowData.turno || "M";
    const responsable = escapeHtml(rowData.responsable_triaje || "");
    const estado = rowData.estado === "Recibido" ? "Recibido" : "Pendiente";
    const estadoClass = estado === "Recibido" ? "btn-status-recibido" : "btn-status-pendiente";
    const especialidadLabel = escapeHtml(normalizeEspecialidadLabel(rowData.especialidad));

    return `
      <td style="border-right: 2px solid #dee2e6;"><input type="text" class="form-control border-0 text-center numero-historia" value="${numeroHistoria}"></td>
      <td style="border-right: 2px solid #dee2e6;"><select class="form-select border-0 medico-select"><option value="">Seleccionar...</option>${medicosOptions}</select></td>
      <td class="especialidad-cell" style="border-right: 2px solid #dee2e6;">${especialidadLabel}</td>
      <td style="border-right: 2px solid #dee2e6;"><select class="form-select border-0 text-center turno-select"><option value="M" ${turno === "M" ? "selected" : ""}>M</option><option value="T" ${turno === "T" ? "selected" : ""}>T</option></select></td>
      <td style="border-right: 2px solid #dee2e6;"><input type="text" class="form-control border-0 text-center responsable-input" placeholder="Nombre responsable" value="${responsable}"></td>
      <td style="border-right: 2px solid #dee2e6;"><span class="status-badge ${estadoClass} js-toggle-status">${escapeHtml(estado)}</span></td>
      <td><button type="button" class="btn btn-sm btn-outline-danger js-modal-delete-row" title="Eliminar fila"><i class="bi bi-trash"></i></button></td>
    `;
  }

  function syncEspecialidadFromMedico(row) {
    if (!row) return;
    const medicoSelect = row.querySelector(".medico-select");
    const especialidadCell = row.querySelector(".especialidad-cell");
    if (!medicoSelect || !especialidadCell) return;
    const selectedOption = medicoSelect.options[medicoSelect.selectedIndex];
    const especialidad = selectedOption?.dataset?.especialidad || "Sin especialidad";
    especialidadCell.textContent = especialidad;
  }

  function applyModalFilters() {
    const especialidadFilter = document.getElementById("modalFilterEspecialidad")?.value || "";
    const turnoFilter = document.getElementById("modalFilterTurno")?.value || "";
    const estadoFilter = document.getElementById("modalFilterEstado")?.value || "";

    document.querySelectorAll(".modal-record-row").forEach((row) => {
      const especialidad = row.querySelector(".especialidad-cell")?.textContent?.trim() || "";
      const turno = row.querySelector(".turno-select")?.value || "";
      const estado = row.querySelector(".status-badge")?.textContent?.trim() || "";

      const matchEspecialidad = !especialidadFilter || especialidad === especialidadFilter;
      const matchTurno = !turnoFilter || turno === turnoFilter;
      const matchEstado = !estadoFilter || estado === estadoFilter;

      row.style.display = matchEspecialidad && matchTurno && matchEstado ? "" : "none";
    });
  }

  function resetModalFilters() {
    const fe = document.getElementById("modalFilterEspecialidad");
    const ft = document.getElementById("modalFilterTurno");
    const fs = document.getElementById("modalFilterEstado");
    if (fe) fe.value = "";
    if (ft) ft.value = "";
    if (fs) fs.value = "";
  }

  function getRowPayload(row) {
    const numeroHistoria = row.querySelector(".numero-historia")?.value.trim() || "";
    const medicoId = row.querySelector(".medico-select")?.value || "";
    const turno = row.querySelector(".turno-select")?.value || "M";
    const responsableTriaje = row.querySelector(".responsable-input")?.value.trim() || "";
    const estado = row.querySelector(".status-badge")?.innerText.trim() || "Pendiente";

    return {
      numero_historia: numeroHistoria,
      medico_id: medicoId ? parseInt(medicoId, 10) : null,
      turno,
      responsable_triaje: responsableTriaje,
      estado,
    };
  }

  function setRowSnapshot(row) {
    row.dataset.original = JSON.stringify(getRowPayload(row));
  }

  function isExistingRowChanged(row) {
    if (!row.dataset.historiaId) return false;
    const originalRaw = row.dataset.original || "";
    if (!originalRaw) return false;
    const currentRaw = JSON.stringify(getRowPayload(row));
    return originalRaw !== currentRaw;
  }

  function addModalRow(medicosOptions, rowData = null) {
    const tbody = document.getElementById("modalTbodyHistorias");
    if (!tbody) return;

    const row = document.createElement("tr");
    row.className = "modal-record-row";
    row.dataset.historiaId = rowData?.id ? String(rowData.id) : "";
    row.innerHTML = buildModalRowHtml(medicosOptions, rowData || {});
    tbody.appendChild(row);

    const medicoSelect = row.querySelector(".medico-select");
    if (medicoSelect) {
      if (rowData?.medico_id) {
        medicoSelect.value = String(rowData.medico_id);
      } else if (rowData?.medico) {
        const targetText = String(rowData.medico).trim().toLowerCase();
        const match = Array.from(medicoSelect.options).find((opt) => opt.textContent.trim().toLowerCase() === targetText);
        if (match) medicoSelect.value = match.value;
      }
    }

    if (rowData?.id) setRowSnapshot(row);
    syncEspecialidadFromMedico(row);
    applyModalFilters();
    if (!rowData) row.querySelector(".numero-historia")?.focus();
    updateModalActionLabel();
  }

  function clearModalRows(medicosOptions) {
    const tbody = document.getElementById("modalTbodyHistorias");
    if (!tbody) return;
    resetModalFilters();
    tbody.innerHTML = "";
    addModalRow(medicosOptions);
    updateModalActionLabel();
  }

  function ensureModalHasAtLeastOneRow(medicosOptions) {
    const tbody = document.getElementById("modalTbodyHistorias");
    if (!tbody) return;
    if (tbody.querySelectorAll(".modal-record-row").length === 0) {
      addModalRow(medicosOptions);
    }
  }

  async function loadHistoriasForFecha(fechaDisplay, medicosOptions) {
    const tbody = document.getElementById("modalTbodyHistorias");
    if (!tbody) return;
    resetModalFilters();
    tbody.innerHTML = "";

    const fechaUrl = fechaDisplay.replace(/\//g, "-");
    try {
      const response = await fetch(`/admission/historias_json/${fechaUrl}`);
      const result = await response.json().catch(() => ({}));
      const historias = Array.isArray(result.historias) ? result.historias : [];

      if (!response.ok || result.status !== "success") {
        clearModalRows(medicosOptions);
        return;
      }

      if (!historias.length) {
        clearModalRows(medicosOptions);
        return;
      }

      historias.forEach((historia) => addModalRow(medicosOptions, historia));
      applyModalFilters();
      updateModalActionLabel();
    } catch (error) {
      console.error("Error cargando historias para modal:", error);
      clearModalRows(medicosOptions);
    }
  }

  function rowConflictNumeroDia(numA, medA, turnA, numB, medB, turnB) {
    if (!numA || !numB) return false;
    if (numA.toLowerCase() !== numB.toLowerCase()) return false;
    return medA === medB || turnA === turnB;
  }

  function findLocalDuplicateNumeroHistoriaInputs() {
    const rows = [...document.querySelectorAll(".modal-record-row")];
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

  function parseModalRows() {
    const rows = document.querySelectorAll(".modal-record-row");
    const historias = [];
    const actualizaciones = [];
    const invalidFields = [];

    rows.forEach((row) => {
      const historiaId = row.dataset.historiaId || "";
      const numeroInput = row.querySelector(".numero-historia");
      const medicoSelect = row.querySelector(".medico-select");
      const turnoSelect = row.querySelector(".turno-select");
      const responsableInput = row.querySelector(".responsable-input");
      const estadoBadge = row.querySelector(".status-badge");

      const numeroHistoria = numeroInput?.value.trim() || "";
      const medicoId = medicoSelect?.value || "";
      const turno = turnoSelect?.value || "M";
      const responsableNombre = responsableInput?.value.trim() || "";
      const estado = estadoBadge?.innerText.trim() || "Pendiente";

      const hasAnyField = numeroHistoria || medicoId || responsableNombre;
      const hasAllFields = numeroHistoria && medicoId && responsableNombre;

      [numeroInput, medicoSelect, responsableInput].forEach((field) => field?.classList.remove("field-error"));

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

      if (historiaId && isExistingRowChanged(row)) {
        if (!hasAllFields) {
          if (!numeroHistoria) invalidFields.push(numeroInput);
          if (!medicoId) invalidFields.push(medicoSelect);
          if (!responsableNombre) invalidFields.push(responsableInput);
        } else {
          actualizaciones.push({
            id: parseInt(historiaId, 10),
            numero_historia: numeroHistoria,
            medico_id: parseInt(medicoId, 10),
            turno,
            responsable_triaje: responsableNombre,
            estado,
          });
        }
      }
    });

    return { historias, actualizaciones, invalidFields };
  }

  function updateModalActionLabel() {
    const btn = document.getElementById("btnModalSaveRecords");
    if (!btn) return;

    const rows = document.querySelectorAll(".modal-record-row");
    let hasDirtyExisting = false;
    let hasNewComplete = false;

    rows.forEach((row) => {
      const historiaId = row.dataset.historiaId || "";
      const payload = getRowPayload(row);
      const hasAllFields = payload.numero_historia && payload.medico_id && payload.responsable_triaje;

      if (historiaId && isExistingRowChanged(row)) hasDirtyExisting = true;
      if (!historiaId && hasAllFields) hasNewComplete = true;
    });

    const label = hasDirtyExisting ? "Actualizar historias" : "Guardar historias";
    btn.dataset.baseLabel = label;
    btn.innerHTML = hasDirtyExisting
      ? '<i class="bi bi-arrow-repeat me-1"></i>Actualizar historias'
      : '<i class="bi bi-check-lg me-1"></i>Guardar historias';
    btn.disabled = !(hasDirtyExisting || hasNewComplete);
  }

  function setModalSavingState(isSaving) {
    const btn = document.getElementById("btnModalSaveRecords");
    if (!btn) return;
    btn.disabled = isSaving;
    btn.innerHTML = isSaving
      ? '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Guardando...'
      : (btn.dataset.baseLabel === "Actualizar historias"
          ? '<i class="bi bi-arrow-repeat me-1"></i>Actualizar historias'
          : '<i class="bi bi-check-lg me-1"></i>Guardar historias');
  }

  async function saveFromModal(medicosOptions) {
    const { historias, actualizaciones, invalidFields } = parseModalRows();
    if (invalidFields.length) {
      invalidFields.forEach((field) => field?.classList.add("field-error"));
      return;
    }
    const dupNumInputs = findLocalDuplicateNumeroHistoriaInputs();
    if (dupNumInputs.length) {
      dupNumInputs.forEach((field) => field?.classList.add("field-error"));
      showToast(
        "Mismo número en la misma carpeta: no puede repetirse con el mismo médico o el mismo turno. " +
          "Solo puede repetirse con otro médico y otro turno.",
        "warning"
      );
      return;
    }
    if (!historias.length && !actualizaciones.length) return;

    setModalSavingState(true);
    try {
      const response = await fetch("/admission/guardar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ historias, actualizaciones, fecha_objetivo: activeModalFecha }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        showToast(result.message || "No se pudo guardar el registro.", "danger");
        return;
      }
      showToast(actualizaciones.length ? "Historias actualizadas correctamente." : "Historias guardadas correctamente.", "success");
      registroModal?.hide();
      clearModalRows(medicosOptions);
      window.location.reload();
    } catch (error) {
      console.error("Error al guardar desde modal:", error);
    } finally {
      setModalSavingState(false);
    }
  }

  async function confirmDeletePendingRow(medicosOptions) {
    const row = pendingDeleteRow;
    if (!row) return;

    const confirmBtn = document.getElementById("btnConfirmDeleteHistoria");
    const originalHtml = confirmBtn?.innerHTML || "";
    if (confirmBtn) {
      confirmBtn.disabled = true;
      confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Eliminando...';
    }

    try {
      const historiaId = row.dataset.historiaId || "";
      if (historiaId) {
        const ok = await deleteHistoria(historiaId);
        if (!ok) {
          showToast("No se pudo eliminar la historia.", "danger");
          return;
        }
      }

      row.remove();
      ensureModalHasAtLeastOneRow(medicosOptions);
      applyModalFilters();
      updateModalActionLabel();
      showToast("Fila eliminada correctamente.", "success");
      confirmDeleteModal?.hide();
    } catch (error) {
      console.error("Error eliminando fila del modal:", error);
      showToast("Ocurrió un error al eliminar la fila.", "danger");
    } finally {
      if (confirmBtn) {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = originalHtml || '<i class="bi bi-trash me-1"></i>Eliminar';
      }
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const dataScript = document.getElementById("registros-data");
    try {
      const rawJson = dataScript?.textContent?.trim() || "[]";
      allRegistros = JSON.parse(rawJson);
    } catch (error) {
      allRegistros = [];
      console.error("Error al parsear registros:", error);
    }

    filteredRegistros = allRegistros.slice();
    renderTable();

    const medicosOptions = document.getElementById("medicos-options-template")?.innerHTML || "";
    const modalEl = document.getElementById("registroHistoriasModal");
    if (modalEl && typeof bootstrap !== "undefined") {
      registroModal = bootstrap.Modal.getOrCreateInstance(modalEl);
    }
    const confirmDeleteModalEl = document.getElementById("confirmDeleteHistoriaModal");
    if (confirmDeleteModalEl && typeof bootstrap !== "undefined") {
      confirmDeleteModal = bootstrap.Modal.getOrCreateInstance(confirmDeleteModalEl);
    }

    document.getElementById("btnRegistrarHoy")?.addEventListener("click", () => {
      const todayDisplay = getTodayDisplayDate();
      const alreadyExists = allRegistros.some((item) => item.fecha === todayDisplay);
      if (alreadyExists) {
        showToast("La carpeta de hoy ya existe. Abrela desde el listado para seguir cargando historias.", "warning");
        return;
      }
      openRegistroModal(todayDisplay);
      clearModalRows(medicosOptions);
    });
    document.getElementById("btnModalAddRow")?.addEventListener("click", () => addModalRow(medicosOptions));
    document.getElementById("btnModalSaveRecords")?.addEventListener("click", () => saveFromModal(medicosOptions));
    document.getElementById("btnConfirmDeleteHistoria")?.addEventListener("click", () => confirmDeletePendingRow(medicosOptions));

    document.getElementById("modalFilterEspecialidad")?.addEventListener("change", applyModalFilters);
    document.getElementById("modalFilterTurno")?.addEventListener("change", applyModalFilters);
    document.getElementById("modalFilterEstado")?.addEventListener("change", applyModalFilters);
    document.getElementById("btnModalClearFilters")?.addEventListener("click", () => {
      resetModalFilters();
      applyModalFilters();
    });

    document.getElementById("searchDateInput")?.addEventListener("change", applySearchFilter);
    document.getElementById("searchDateInput")?.addEventListener("input", applySearchFilter);
    document.getElementById("searchDateInput")?.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      const dateInput = document.getElementById("searchDateInput");
      if (dateInput) dateInput.value = "";
      setQuickFilter("all");
    });
    document.getElementById("btnClearDateFilter")?.addEventListener("click", () => {
      const dateInput = document.getElementById("searchDateInput");
      if (dateInput) dateInput.value = "";
      applySearchFilter();
    });

    document.querySelectorAll(".quick-filter-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        setQuickFilter(btn.getAttribute("data-filter") || "all");
      });
    });

    document.addEventListener("click", (event) => {
      const status = event.target.closest(".js-toggle-status");
      if (status && status.closest("#registroHistoriasModal")) {
        toggleStatus(status);
        applyModalFilters();
        updateModalActionLabel();
      }

      const folderBtn = event.target.closest(".record-folder-btn");
      if (folderBtn) {
        const folderDate = folderBtn.getAttribute("data-fecha");
        if (folderDate) {
          openRegistroModal(folderDate);
          loadHistoriasForFecha(folderDate, medicosOptions);
        }
      }

      const deleteRowBtn = event.target.closest(".js-modal-delete-row");
      if (deleteRowBtn) {
        const row = deleteRowBtn.closest(".modal-record-row");
        if (!row) return;
        pendingDeleteRow = row;
        confirmDeleteModal?.show();
      }
    });

    document.addEventListener("input", (event) => {
      if (event.target.closest("#registroHistoriasModal")) {
        updateModalActionLabel();
      }
    });

    document.addEventListener("change", (event) => {
      if (!event.target.closest("#registroHistoriasModal")) return;
      if (event.target.classList.contains("medico-select")) {
        const row = event.target.closest(".modal-record-row");
        syncEspecialidadFromMedico(row);
      }
      if (event.target.classList.contains("medico-select") || event.target.classList.contains("turno-select")) {
        applyModalFilters();
      }
      updateModalActionLabel();
    });

    document.getElementById("registroHistoriasModal")?.addEventListener("hidden.bs.modal", () => {
      clearModalRows(medicosOptions);
      activeModalFecha = null;
      updateModalActionLabel();
    });
    document.getElementById("confirmDeleteHistoriaModal")?.addEventListener("hidden.bs.modal", () => {
      pendingDeleteRow = null;
    });

    updateModalActionLabel();
  });
})();

