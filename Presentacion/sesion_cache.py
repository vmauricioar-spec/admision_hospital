"""Evita historial engañoso (Atrás/Adelante) con páginas HTML cacheadas."""

from __future__ import annotations

from flask import Response, session, redirect, url_for


def redirect_al_panel_si_hay_sesion() -> Response | None:
    """Si el usuario ya tiene sesión, no mostrar login ni portada: ir al panel."""
    if not session.get("usuario_id"):
        return None
    role = session.get("usuario_role")
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "admission":
        return redirect(url_for("admission.dashboard"))
    return None


def aplicar_no_cache_privado(response: Response) -> Response:
    """Cabeceras para que el navegador no reutilice HTML/JSON sin volver a pedirlo al servidor."""
    ct = (response.headers.get("Content-Type") or "").lower()
    if "text/html" in ct or "application/json" in ct:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
