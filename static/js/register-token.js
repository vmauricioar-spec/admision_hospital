(function () {
  function evaluatePassword(password) {
    var hasLength = password.length >= 8;
    var hasUpper = /[A-Z]/.test(password);
    var hasLower = /[a-z]/.test(password);
    var hasNumber = /\d/.test(password);
    var hasSpecial = /[^A-Za-z0-9]/.test(password);
    var score = 0;
    if (hasLength) score += 1;
    if (hasUpper) score += 1;
    if (hasLower) score += 1;
    if (hasNumber) score += 1;
    if (hasSpecial) score += 1;
    if (password.length >= 12) score += 1;

    var label = "Fragil";
    var width = 18;
    var className = "strength-fragil";
    if (score >= 5) {
      label = "Fuerte";
      width = 100;
      className = "strength-fuerte";
    } else if (score >= 3) {
      label = "Regular";
      width = 66;
      className = "strength-regular";
    }

    var valid = hasLength && hasUpper && hasLower && hasNumber && hasSpecial;
    return {
      valid: valid,
      label: label,
      width: width,
      className: className,
      rules: {
        length: hasLength,
        upper: hasUpper,
        lower: hasLower,
        number: hasNumber,
        special: hasSpecial,
      },
    };
  }

  function toggleRule(ruleEl, ok) {
    if (!ruleEl) return;
    ruleEl.classList.toggle("rule-ok", !!ok);
  }

  function secureRandomIndex(max) {
    if (max <= 0) return 0;
    if (window.crypto && window.crypto.getRandomValues) {
      var arr = new Uint32Array(1);
      window.crypto.getRandomValues(arr);
      return arr[0] % max;
    }
    return Math.floor(Math.random() * max);
  }

  function pickRandom(chars) {
    return chars.charAt(secureRandomIndex(chars.length));
  }

  function shuffleArray(items) {
    var arr = items.slice();
    for (var i = arr.length - 1; i > 0; i--) {
      var j = secureRandomIndex(i + 1);
      var temp = arr[i];
      arr[i] = arr[j];
      arr[j] = temp;
    }
    return arr;
  }

  function generateStrongSuggestion(length) {
    var upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
    var lower = "abcdefghijkmnopqrstuvwxyz";
    var digits = "23456789";
    var special = "!@#$%&*+-_=?";
    var all = upper + lower + digits + special;

    var chars = [
      pickRandom(upper),
      pickRandom(lower),
      pickRandom(digits),
      pickRandom(special),
    ];
    for (var i = chars.length; i < length; i++) {
      chars.push(pickRandom(all));
    }
    return shuffleArray(chars).join("");
  }

  function setupRegisterToken() {
    var form = document.querySelector("form[method='POST']");
    var nombreInput = document.querySelector("input[name='nombre_completo']");
    var usernameInput = document.querySelector("input[name='username']");
    var notificationTarget = document.getElementById("notificationTarget");
    var passwordInput = document.getElementById("passwordInput");
    if (!passwordInput) return;

    var toggleBtn = document.getElementById("btnTogglePassword");
    var bar = document.getElementById("passwordStrengthBar");
    var text = document.getElementById("passwordStrengthText");
    var passwordLockHint = document.getElementById("passwordLockHint");
    var generationField = document.getElementById("generationTimeMs");
    var suggestionsList = document.getElementById("passwordSuggestions");
    var refreshSuggestionsBtn = document.getElementById("btnRefreshSuggestions");
    var startAtMs = 0;

    var ruleLength = document.getElementById("ruleLength");
    var ruleUpper = document.getElementById("ruleUpper");
    var ruleLower = document.getElementById("ruleLower");
    var ruleNumber = document.getElementById("ruleNumber");
    var ruleSpecial = document.getElementById("ruleSpecial");
    var suggestionButtons = [];

    function applySuggestion(password) {
      if (!passwordInput || passwordInput.disabled) return;
      passwordInput.value = password;
      if (!startAtMs) startAtMs = Date.now();
      refreshMeter();
      passwordInput.focus();
    }

    function renderSuggestions() {
      if (!suggestionsList) return;
      var generated = {};
      var suggestions = [];
      while (suggestions.length < 3) {
        var candidate = generateStrongSuggestion(14);
        if (!generated[candidate]) {
          generated[candidate] = true;
          suggestions.push(candidate);
        }
      }

      suggestionButtons = [];
      suggestionsList.innerHTML = "";
      suggestions.forEach(function (pwd, idx) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "password-suggestion-item";
        btn.setAttribute("aria-label", "Usar sugerencia de contraseña " + (idx + 1));
        btn.textContent = pwd;
        btn.addEventListener("click", function () {
          applySuggestion(pwd);
        });
        suggestionsList.appendChild(btn);
        suggestionButtons.push(btn);
      });
    }

    function validateNotificationTarget() {
      if (!notificationTarget) return;
      var value = (notificationTarget.value || "").trim();

      if (!value) {
        notificationTarget.setCustomValidity("Debes ingresar un correo para enviar las credenciales.");
        return;
      }
      var emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
      if (!emailRegex.test(value)) {
        notificationTarget.setCustomValidity(
          "Correo inválido. Debe incluir dominio válido y terminar en .com, .co, .pe, etc."
        );
        return;
      }
      notificationTarget.setCustomValidity("");
    }

    function requiredFieldsReady() {
      var nombreOk = !!(nombreInput && nombreInput.value.trim());
      var usernameOk = !!(usernameInput && usernameInput.value.trim());
      if (!nombreOk || !usernameOk) return false;
      var targetValue = notificationTarget ? notificationTarget.value.trim() : "";
      return !!targetValue;
    }

    function refreshPasswordLockState() {
      var ready = requiredFieldsReady();
      passwordInput.disabled = !ready;
      if (!ready) {
        passwordInput.value = "";
        startAtMs = 0;
        if (generationField) generationField.value = "0";
      }
      if (passwordLockHint) {
        passwordLockHint.classList.toggle("d-none", ready);
      }
      if (toggleBtn) {
        toggleBtn.disabled = !ready;
      }
      if (refreshSuggestionsBtn) {
        refreshSuggestionsBtn.disabled = !ready;
      }
      suggestionButtons.forEach(function (btn) {
        btn.disabled = !ready;
      });
      refreshMeter();
    }

    function refreshMeter() {
      var state = evaluatePassword(passwordInput.value || "");
      if (bar) {
        bar.classList.remove("strength-fragil", "strength-regular", "strength-fuerte");
        bar.classList.add(state.className);
        bar.style.width = state.width + "%";
      }
      if (text) {
        text.textContent = "Fortaleza: " + state.label;
      }
      toggleRule(ruleLength, state.rules.length);
      toggleRule(ruleUpper, state.rules.upper);
      toggleRule(ruleLower, state.rules.lower);
      toggleRule(ruleNumber, state.rules.number);
      toggleRule(ruleSpecial, state.rules.special);

      if (!state.valid) {
        passwordInput.setCustomValidity(
          "La contraseña debe tener mínimo 8 caracteres y contener mayúscula, minúscula, número y carácter especial."
        );
      } else {
        passwordInput.setCustomValidity("");
      }
    }

    if (toggleBtn) {
      toggleBtn.addEventListener("click", function () {
        if (passwordInput.disabled) return;
        var isPassword = passwordInput.getAttribute("type") === "password";
        passwordInput.setAttribute("type", isPassword ? "text" : "password");
      });
    }

    if (refreshSuggestionsBtn) {
      refreshSuggestionsBtn.addEventListener("click", function () {
        if (passwordInput.disabled) return;
        renderSuggestions();
        refreshPasswordLockState();
      });
    }

    passwordInput.addEventListener("input", function () {
      if (!startAtMs && passwordInput.value.length > 0) {
        startAtMs = Date.now();
      }
      refreshMeter();
    });

    [nombreInput, usernameInput].forEach(
      function (el) {
        if (!el) return;
        el.addEventListener("input", refreshPasswordLockState);
        el.addEventListener("change", refreshPasswordLockState);
      }
    );

    if (notificationTarget) {
      notificationTarget.addEventListener("input", function () {
        validateNotificationTarget();
        refreshPasswordLockState();
      });
      notificationTarget.addEventListener("change", function () {
        validateNotificationTarget();
        refreshPasswordLockState();
      });
    }

    if (form) {
      form.addEventListener("submit", function () {
        refreshMeter();
        validateNotificationTarget();
        if (generationField && startAtMs) {
          generationField.value = String(Math.max(Date.now() - startAtMs, 0));
        }
      });
    }

    renderSuggestions();
    validateNotificationTarget();
    refreshPasswordLockState();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupRegisterToken);
  } else {
    setupRegisterToken();
  }
})();
