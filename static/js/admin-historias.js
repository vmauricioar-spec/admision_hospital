(function () {
  const JSON_BASE = "/admin/historias_json/";
  let allRegistros = [];
  let filteredRegistros = [];
  let activeQuickFilter = "all";
  let adminModal = null;

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
    const selectedDateText = formatInputDateToDisplay(document.getElementById("adminSearchDateInput")?.value || "");

    let baseItems = applyQuickFilter(allRegistros);
    baseItems = baseItems.filter((item) => {
      const matchDate = !selectedDateText || item.fecha === selectedDateText;
      return matchDate;
    });

    filteredRegistros = baseItems;
    renderFolderGrid();
  }

  function renderFolderGrid() {
    const container = document.getElementById("adminRecordsContainer");
    const noRecords = document.getElementById("adminNoRecordsMessage");
    const summary = document.getElementById("adminRecordsSummary");

    if (filteredRegistros.length === 0) {
      container.innerHTML = "";
      noRecords.classList.remove("d-none");
      if (summary) {
        summary.innerHTML =
          '<span class="summary-pill summary-pill-muted"><i class="bi bi-info-circle me-1"></i>Sin carpetas con el filtro actual</span>';
      }
      return;
    }

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
      html += '<span class="record-open-label">Ver historias</span>';
      html += '<span class="record-open-icon"><i class="bi bi-chevron-right"></i></span>';
      html += "</div>";
      html += "</button>";
    });

    container.innerHTML = html;

    const n = filteredRegistros.length;
    if (summary) {
      summary.innerHTML = `
          <span class="summary-pill"><i class="bi bi-calendar3 me-1"></i><strong>${n}</strong> ${n === 1 ? "carpeta" : "carpetas"}</span>
          <span class="summary-pill"><i class="bi bi-journal-text me-1"></i><strong>${totalHistorias}</strong> historias</span>
          <span class="summary-pill summary-pill-warn"><i class="bi bi-hourglass-split me-1"></i><strong>${totalPend}</strong> pendientes</span>
          <span class="summary-pill summary-pill-ok"><i class="bi bi-check2-circle me-1"></i><strong>${totalRec}</strong> recibidas</span>
        `;
    }
  }

  function setQuickFilter(filterName) {
    activeQuickFilter = filterName;
    document.querySelectorAll(".quick-filter-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-filter") === filterName);
    });
    applySearchFilter();
  }

  function resetAdminModalFilters() {
    const fe = document.getElementById("adminModalFilterEspecialidad");
    const ft = document.getElementById("adminModalFilterTurno");
    const fs = document.getElementById("adminModalFilterEstado");
    if (fe) fe.value = "";
    if (ft) ft.value = "";
    if (fs) fs.value = "";
  }

  function applyAdminModalFilters() {
    const esp = document.getElementById("adminModalFilterEspecialidad")?.value || "";
    const turno = document.getElementById("adminModalFilterTurno")?.value || "";
    const estado = document.getElementById("adminModalFilterEstado")?.value || "";

    document.querySelectorAll(".admin-modal-row").forEach((row) => {
      const e = row.dataset.especialidad || "";
      const t = row.dataset.turno || "";
      const s = row.dataset.estado || "";
      const matchEsp = !esp || e === esp;
      const matchTurno = !turno || t === turno;
      const matchEstado = !estado || s === estado;
      row.style.display = matchEsp && matchTurno && matchEstado ? "" : "none";
    });
  }

  function openAdminModal(fechaDisplay) {
    const titleEl = document.getElementById("adminModalTitle");
    if (titleEl) titleEl.textContent = `Historias — ${fechaDisplay}`;
    resetAdminModalFilters();
    adminModal?.show();
    loadHistoriasReadOnly(fechaDisplay);
  }

  async function loadHistoriasReadOnly(fechaDisplay) {
    const tbody = document.getElementById("adminModalTbody");
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="text-muted py-4">Cargando…</td></tr>';

    const fechaUrl = fechaDisplay.replace(/\//g, "-");
    try {
      const response = await fetch(`${JSON_BASE}${encodeURIComponent(fechaUrl)}`);
      const result = await response.json().catch(() => ({}));
      const historias = Array.isArray(result.historias) ? result.historias : [];

      if (!response.ok || result.status !== "success") {
        tbody.innerHTML = '<tr><td colspan="7" class="text-danger">No se pudieron cargar las historias.</td></tr>';
        return;
      }

      if (!historias.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-muted">No hay registros para esta fecha.</td></tr>';
        return;
      }

      let rowsHtml = "";
      historias.forEach((h) => {
        const esp = normalizeEspecialidadLabel(h.especialidad);
        const estado = h.estado === "Recibido" ? "Recibido" : "Pendiente";
        const badgeClass = estado === "Recibido" ? "badge-estado--rec" : "badge-estado--pend";
        rowsHtml += `<tr class="admin-modal-row" data-especialidad="${escapeHtml(esp)}" data-turno="${escapeHtml((h.turno || "").trim().toUpperCase())}" data-estado="${escapeHtml(estado)}">`;
        rowsHtml += `<td>${escapeHtml(h.numero_historia)}</td>`;
        rowsHtml += `<td class="text-start">${escapeHtml(h.medico)}</td>`;
        rowsHtml += `<td class="text-start">${escapeHtml(esp)}</td>`;
        rowsHtml += `<td>${escapeHtml(h.turno)}</td>`;
        rowsHtml += `<td>${escapeHtml(h.responsable_triaje)}</td>`;
        rowsHtml += `<td><span class="badge-estado ${badgeClass}">${escapeHtml(estado)}</span></td>`;
        rowsHtml += `<td class="text-nowrap small">${escapeHtml(h.fecha_registro)}</td>`;
        rowsHtml += "</tr>";
      });
      tbody.innerHTML = rowsHtml;
      applyAdminModalFilters();
    } catch (err) {
      console.error(err);
      tbody.innerHTML = '<tr><td colspan="7" class="text-danger">Error de conexión.</td></tr>';
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const dataScript = document.getElementById("admin-registros-data");
    try {
      const rawJson = dataScript?.textContent?.trim() || "[]";
      allRegistros = JSON.parse(rawJson);
    } catch (e) {
      allRegistros = [];
      console.error("Error al parsear registros admin:", e);
    }

    filteredRegistros = allRegistros.slice();
    renderFolderGrid();

    const modalEl = document.getElementById("adminHistoriasModal");
    if (modalEl && typeof bootstrap !== "undefined") {
      adminModal = bootstrap.Modal.getOrCreateInstance(modalEl);
    }

    document.getElementById("adminSearchDateInput")?.addEventListener("change", applySearchFilter);
    document.getElementById("adminSearchDateInput")?.addEventListener("input", applySearchFilter);
    document.getElementById("adminSearchDateInput")?.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      const el = document.getElementById("adminSearchDateInput");
      if (el) el.value = "";
      setQuickFilter("all");
    });

    document.getElementById("adminBtnClearDateFilter")?.addEventListener("click", () => {
      const el = document.getElementById("adminSearchDateInput");
      if (el) el.value = "";
      applySearchFilter();
    });

    document.querySelectorAll(".quick-filter-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        setQuickFilter(btn.getAttribute("data-filter") || "all");
      });
    });

    document.addEventListener("click", (event) => {
      const folderBtn = event.target.closest(".record-folder-btn");
      if (folderBtn) {
        const folderDate = folderBtn.getAttribute("data-fecha");
        if (folderDate) openAdminModal(folderDate);
      }
    });

    document.getElementById("adminModalFilterEspecialidad")?.addEventListener("change", applyAdminModalFilters);
    document.getElementById("adminModalFilterTurno")?.addEventListener("change", applyAdminModalFilters);
    document.getElementById("adminModalFilterEstado")?.addEventListener("change", applyAdminModalFilters);
    document.getElementById("adminBtnModalClearFilters")?.addEventListener("click", () => {
      resetAdminModalFilters();
      applyAdminModalFilters();
    });

    document.getElementById("adminHistoriasModal")?.addEventListener("hidden.bs.modal", () => {
      resetAdminModalFilters();
      const tbody = document.getElementById("adminModalTbody");
      if (tbody) tbody.innerHTML = "";
    });
  });
})();
