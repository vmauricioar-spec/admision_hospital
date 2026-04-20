(function () {
  var toggles = document.querySelectorAll("[data-toggle-password]");
  if (!toggles.length) return;

  toggles.forEach(function (btn) {
    var selector = btn.getAttribute("data-toggle-password");
    var target = selector ? document.querySelector(selector) : null;
    if (!target) return;

    btn.addEventListener("click", function () {
      var isPassword = target.getAttribute("type") === "password";
      target.setAttribute("type", isPassword ? "text" : "password");

      var icon = btn.querySelector("i");
      if (icon) {
        icon.classList.remove("bi-eye", "bi-eye-slash");
        icon.classList.add(isPassword ? "bi-eye-slash" : "bi-eye");
      }
    });
  });
})();
