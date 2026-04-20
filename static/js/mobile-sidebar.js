(function () {
  function setupMobileSidebar(sidebar) {
    if (!sidebar) return;
    var nav = sidebar.querySelector(".nav");
    var title = sidebar.querySelector("h5");
    if (!nav || !title) return;

    var toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.className = "sidebar-mobile-toggle";
    toggleBtn.setAttribute("aria-label", "Abrir o cerrar menu lateral");
    toggleBtn.setAttribute("aria-expanded", "false");
    toggleBtn.innerHTML = '<i class="bi bi-list"></i><span>Menu</span>';
    title.appendChild(toggleBtn);

    var mobileQuery = window.matchMedia("(max-width: 767.98px)");

    function setOpen(open) {
      sidebar.classList.toggle("is-open", !!open);
      toggleBtn.setAttribute("aria-expanded", open ? "true" : "false");
      toggleBtn.innerHTML = open
        ? '<i class="bi bi-x-lg"></i><span>Cerrar</span>'
        : '<i class="bi bi-list"></i><span>Menu</span>';
    }

    function syncMode() {
      if (!mobileQuery.matches) {
        sidebar.classList.remove("is-open");
        toggleBtn.setAttribute("aria-expanded", "false");
      }
    }

    toggleBtn.addEventListener("click", function () {
      if (!mobileQuery.matches) return;
      setOpen(!sidebar.classList.contains("is-open"));
    });

    nav.querySelectorAll("a.nav-link").forEach(function (link) {
      link.addEventListener("click", function () {
        if (mobileQuery.matches) {
          setOpen(false);
        }
      });
    });

    window.addEventListener("resize", syncMode);
    syncMode();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setupMobileSidebar(document.querySelector(".sidebar"));
    });
  } else {
    setupMobileSidebar(document.querySelector(".sidebar"));
  }
})();
