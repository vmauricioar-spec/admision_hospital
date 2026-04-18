function copyLink() {
  const input = document.getElementById("linkInput");
  if (!input) return;

  navigator.clipboard.writeText(input.value).then(() => {
    alert("Enlace copiado al portapapeles");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnCopyLink")?.addEventListener("click", copyLink);
});

