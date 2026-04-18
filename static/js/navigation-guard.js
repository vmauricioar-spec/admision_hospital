(function () {
  if (window.__navGuardLoaded) {
    return;
  }
  window.__navGuardLoaded = true;

  function forceServerValidation() {
    window.location.reload();
  }

  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      forceServerValidation();
      return;
    }

    var navigationEntries = performance.getEntriesByType("navigation");
    if (
      navigationEntries &&
      navigationEntries.length > 0 &&
      navigationEntries[0].type === "back_forward"
    ) {
      forceServerValidation();
    }
  });
})();
