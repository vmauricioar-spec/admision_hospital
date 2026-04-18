(function () {
  function initTableSearch() {
    const inputEl = document.querySelector("[data-search-input]");
    const tableEl = document.querySelector("[data-search-table]");
    if (!inputEl || !tableEl) return;

    const tbodyRows = Array.from(tableEl.querySelectorAll("tbody tr"));
    inputEl.addEventListener("input", () => {
      const query = inputEl.value.trim().toLowerCase();
      tbodyRows.forEach((row) => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    });
  }

  function initToasts() {
    document.querySelectorAll(".toast").forEach((toastEl) => {
      const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { autohide: false });
      toast.show();
      window.setTimeout(() => toast.hide(), 3000);
    });
  }

  function initConfirmModal() {
    const confirmModalEl = document.getElementById("confirmActionModal");
    const confirmMessageEl = document.getElementById("confirmActionMessage");
    const confirmActionBtn = document.getElementById("confirmActionBtn");

    if (!confirmModalEl || !confirmMessageEl || !confirmActionBtn) return;

    const confirmModal = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
    let pendingForm = null;

    document.querySelectorAll("form[data-confirm]").forEach((formEl) => {
      formEl.addEventListener("submit", (event) => {
        event.preventDefault();
        pendingForm = formEl;
        confirmMessageEl.textContent = formEl.getAttribute("data-confirm") || "¿Confirmar acción?";
        confirmModal.show();
      });
    });

    document.querySelectorAll(".js-delete-btn").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const formEl = buttonEl.closest("form[data-confirm]");
        if (!formEl) return;
        pendingForm = formEl;
        confirmMessageEl.textContent = formEl.getAttribute("data-confirm") || "¿Confirmar acción?";
        confirmModal.show();
      });
    });

    confirmActionBtn.addEventListener("click", () => {
      if (pendingForm) pendingForm.submit();
    });
  }

  function initAdminCreateUserPasswordLock() {
    const form = document.getElementById("adminCreateUserForm");
    if (!form) return;

    const nombreInput = document.getElementById("createNombreCompleto");
    const usernameInput = document.getElementById("createUsername");
    const emailInput = document.getElementById("createEmail");
    const roleInput = document.getElementById("createRole");
    const passwordInput = document.getElementById("createPassword");
    const passwordHint = document.getElementById("createPasswordHint");
    const generationField = document.getElementById("createGenerationTimeMs");

    if (!passwordInput) return;

    let startAtMs = 0;

    function isValidEmail(email) {
      return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email || "");
    }

    function requiredFieldsReady() {
      const nombreOk = !!(nombreInput && nombreInput.value.trim());
      const usernameOk = !!(usernameInput && usernameInput.value.trim());
      const emailOk = !!(emailInput && emailInput.value.trim()) && isValidEmail(emailInput.value.trim());
      const roleOk = !!(roleInput && roleInput.value.trim());
      return nombreOk && usernameOk && emailOk && roleOk;
    }

    function refreshPasswordLock() {
      const ready = requiredFieldsReady();
      passwordInput.disabled = !ready;
      if (!ready) {
        passwordInput.value = "";
        startAtMs = 0;
        if (generationField) generationField.value = "0";
      }
      if (passwordHint) {
        passwordHint.classList.toggle("d-none", ready);
      }
    }

    [nombreInput, usernameInput, emailInput, roleInput].forEach((el) => {
      if (!el) return;
      el.addEventListener("input", refreshPasswordLock);
      el.addEventListener("change", refreshPasswordLock);
    });

    passwordInput.addEventListener("focus", () => {
      if (!passwordInput.disabled && !startAtMs) {
        startAtMs = Date.now();
      }
    });

    passwordInput.addEventListener("input", () => {
      if (!passwordInput.disabled && !startAtMs && passwordInput.value.length > 0) {
        startAtMs = Date.now();
      }
    });

    form.addEventListener("submit", () => {
      if (generationField && startAtMs) {
        generationField.value = String(Math.max(Date.now() - startAtMs, 0));
      }
    });

    refreshPasswordLock();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTableSearch();
    initToasts();
    initConfirmModal();
    initAdminCreateUserPasswordLock();
  });
})();

