import re
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from Aplicacion.Servicios.HistoriaService import HistoriaService
from Aplicacion.Servicios.AuthService import AuthService
from Aplicacion.Servicios.TokenService import TokenService
from Aplicacion.Servicios.NotificationService import NotificationService, NotificationConfigError
from Aplicacion.Servicios.SolanaBlockchainService import (
    SolanaBlockchainService,
    BlockchainConfigError,
    BlockchainWriteError,
)
from Persistencia.Repositorios.EspecialidadRepository import EspecialidadRepository
from Persistencia.Repositorios.MedicoRepository import MedicoRepository
from Persistencia.Repositorios.PasswordMetricRepository import PasswordMetricRepository
from Persistencia.Repositorios.UsuarioRepository import UsuarioRepository
from Persistencia.Repositorios.HistoriaRepository import HistoriaRepository
from Dominio.Entidades.Especialidad import Especialidad
from Dominio.Entidades.Medico import Medico
from Dominio.Entidades.Usuario import Usuario
from datetime import datetime
import pyodbc

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
historia_service = HistoriaService()
auth_service = AuthService()
especialidad_repo = EspecialidadRepository()
medico_repo = MedicoRepository()
usuario_repo = UsuarioRepository()
historia_repo = HistoriaRepository()
password_metric_repo = PasswordMetricRepository()
notification_service = NotificationService()


def _email_is_valid(email: str) -> bool:
    return bool(
        re.fullmatch(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            email or "",
        )
    )


def _password_policy_error(password: str):
    if len(password) < 8:
        return "La contraseña debe tener mínimo 8 caracteres."
    if not any(ch.isupper() for ch in password):
        return "La contraseña debe incluir al menos una mayúscula."
    if not any(ch.islower() for ch in password):
        return "La contraseña debe incluir al menos una minúscula."
    if not any(ch.isdigit() for ch in password):
        return "La contraseña debe incluir al menos un número."
    if not any(not ch.isalnum() for ch in password):
        return "La contraseña debe incluir al menos un carácter especial."
    return None


def _password_strength_label(password: str) -> str:
    has_upper = any(ch.isupper() for ch in password)
    has_lower = any(ch.islower() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    has_special = any(not ch.isalnum() for ch in password)
    score = sum([has_upper, has_lower, has_digit, has_special])
    if len(password) >= 12:
        score += 1
    if score <= 2:
        return "Fragil"
    if score <= 4:
        return "Regular"
    return "Fuerte"

@admin_bp.before_request
def check_admin():
    if session.get('usuario_role') != 'admin':
        from flask import redirect, url_for
        return redirect(url_for('auth.login_admin'))

@admin_bp.route('/dashboard')
def dashboard():
    historias = historia_service.get_all_historias()
    cantidades = {
        'total_historias': len(historias),
        'pendientes': len([h for h in historias if h['estado'] == 'Pendiente']),
        'recibidas': len([h for h in historias if h['estado'] == 'Recibido'])
    }
    return render_template('admin/dashboard.html',
                           usuario_nombre=session.get('usuario_nombre'),
                           cantidades=cantidades)

@admin_bp.route('/generar-link', methods=['POST'])
def generar_link():
    token_service = TokenService()
    hours = int(request.form.get('hours', 24))
    token = token_service.generate_token(hours_valid=hours)
    link = request.host_url + 'registro/' + token
    return render_template('admin/generar_link.html', link=link, hours=hours)

@admin_bp.route('/usuarios', methods=['GET', 'POST'])
def usuarios():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        nombre_completo = (request.form.get('nombre_completo') or '').strip()
        email = (request.form.get('email') or '').strip()
        role = (request.form.get('role') or '').strip()
        generation_time_ms_raw = (request.form.get('generation_time_ms') or '0').strip()

        try:
            generation_time_ms = max(int(generation_time_ms_raw), 0)
        except ValueError:
            generation_time_ms = 0

        if not username or not password or not nombre_completo or not email:
            flash('Completa todos los campos obligatorios, incluido el correo.', 'danger')
            return redirect(url_for('admin.usuarios'))
        if role not in ('admin', 'admission'):
            flash('Rol inválido.', 'danger')
            return redirect(url_for('admin.usuarios'))
        if not _email_is_valid(email):
            flash('Debes ingresar un correo electrónico válido.', 'danger')
            return redirect(url_for('admin.usuarios'))
        if usuario_repo.get_by_email(email):
            flash('El correo electrónico ya está registrado.', 'warning')
            return redirect(url_for('admin.usuarios'))
        policy_error = _password_policy_error(password)
        if policy_error:
            flash(policy_error, 'danger')
            return redirect(url_for('admin.usuarios'))
        if usuario_repo.get_by_username(username):
            flash('El nombre de usuario ya existe.', 'warning')
            return redirect(url_for('admin.usuarios'))

        try:
            blockchain_service = SolanaBlockchainService()
            user_id, _, _, _ = auth_service.create_user_with_blockchain(
                username=username,
                password=password,
                nombre_completo=nombre_completo,
                role=role,
                blockchain_service=blockchain_service,
                email=email,
            )
            password_metric_repo.create(
                usuario_id=user_id,
                password_length=len(password),
                generation_time_ms=generation_time_ms,
                strength_label=_password_strength_label(password),
            )
            notification_service.send_email_credentials(email, username, password)
            flash('Usuario creado correctamente. Hash registrado en Solana y credenciales enviadas al correo.', 'success')
        except NotificationConfigError as exc:
            flash(f'Usuario creado, pero no se pudo enviar el correo: {exc}', 'warning')
        except BlockchainConfigError as exc:
            flash(f'No se pudo crear el usuario por configuración blockchain: {exc}', 'danger')
        except BlockchainWriteError as exc:
            flash(f'No se pudo registrar el hash en Solana: {exc}', 'danger')
        except pyodbc.Error:
            flash('No se pudo crear el usuario en la base de datos.', 'danger')
        except Exception as exc:
            flash(f'Ocurrió un error al crear el usuario: {exc}', 'danger')
        return redirect(url_for('admin.usuarios'))

    return render_template('admin/usuarios.html', usuarios=usuario_repo.get_all())

@admin_bp.route('/usuarios/<int:usuario_id>/editar', methods=['POST'])
def editar_usuario(usuario_id: int):
    usuario_actual = usuario_repo.get_by_id(usuario_id)
    if not usuario_actual:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('admin.usuarios'))

    username = (request.form.get('username') or '').strip()
    password = (request.form.get('password') or '').strip()
    nombre_completo = (request.form.get('nombre_completo') or '').strip()
    email = (request.form.get('email') or '').strip()
    role = (request.form.get('role') or '').strip()
    activo_raw = (request.form.get('activo') or '').strip().lower()
    activo = activo_raw in ('1', 'true', 'on', 'si', 'sí')

    if not username or not nombre_completo or not email:
        flash('Completa los campos obligatorios del usuario, incluido el correo.', 'danger')
        return redirect(url_for('admin.usuarios'))
    if role not in ('admin', 'admission'):
        flash('Rol inválido.', 'danger')
        return redirect(url_for('admin.usuarios'))
    if not _email_is_valid(email):
        flash('Debes ingresar un correo electrónico válido.', 'danger')
        return redirect(url_for('admin.usuarios'))
    if activo_raw not in ('1', '0', 'true', 'false', 'on', 'off', 'si', 'sí', 'no'):
        flash('Estado de usuario inválido.', 'danger')
        return redirect(url_for('admin.usuarios'))
    if session.get('usuario_id') == usuario_id and not activo:
        flash('No puedes desactivar tu propio usuario desde esta pantalla.', 'warning')
        return redirect(url_for('admin.usuarios'))

    existing = usuario_repo.get_by_username(username)
    if existing and existing.id != usuario_id:
        flash('El nombre de usuario ya existe.', 'warning')
        return redirect(url_for('admin.usuarios'))
    existing_email = usuario_repo.get_by_email(email)
    if existing_email and existing_email.id != usuario_id:
        flash('El correo electrónico ya está registrado.', 'warning')
        return redirect(url_for('admin.usuarios'))

    try:
        password_hash = usuario_actual.password_hash
        if password:
            policy_error = _password_policy_error(password)
            if policy_error:
                flash(policy_error, 'danger')
                return redirect(url_for('admin.usuarios'))
            password_hash = auth_service.hash_password(password)

        usuario_actualizado = Usuario(
            id=usuario_actual.id,
            username=username,
            password_hash=password_hash,
            nombre_completo=nombre_completo,
            email=email,
            role=role,
            activo=activo,
            fecha_creacion=usuario_actual.fecha_creacion
        )
        usuario_repo.update(usuario_actualizado)
        flash('Usuario actualizado correctamente.', 'success')
    except pyodbc.Error:
        flash('No se pudo actualizar el usuario.', 'danger')

    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/<int:usuario_id>/eliminar', methods=['POST'])
def eliminar_usuario(usuario_id: int):
    if session.get('usuario_id') == usuario_id:
        flash('No puedes eliminar tu propio usuario desde esta pantalla.', 'warning')
        return redirect(url_for('admin.usuarios'))

    try:
        if not usuario_repo.get_by_id(usuario_id):
            flash('Usuario no encontrado.', 'danger')
        else:
            usuario_repo.delete(usuario_id)
            flash('Usuario eliminado correctamente.', 'success')
    except pyodbc.Error:
        flash('No se pudo eliminar el usuario.', 'danger')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/historias')
def historias():
    registros = historia_service.get_registros_agrupados_por_dia()
    especialidades = especialidad_repo.get_all()
    return render_template(
        'admin/historias.html',
        registros=registros,
        especialidades=especialidades,
    )


@admin_bp.route('/password-metrics')
def password_metrics():
    summary = password_metric_repo.get_summary()
    per_user = password_metric_repo.get_per_user()
    metrics = password_metric_repo.get_all()
    return render_template(
        'admin/password_metrics.html',
        summary=summary,
        per_user=per_user,
        metrics=metrics,
    )


@admin_bp.route('/historias_json/<fecha>')
def historias_json_admin(fecha):
    fecha_clean = fecha.replace('-', '/')
    try:
        fecha_dt = datetime.strptime(fecha_clean, '%d/%m/%Y').date()
        historias = historia_service.get_historias_por_fecha(fecha_dt)
        return jsonify({'status': 'success', 'historias': historias})
    except Exception as e:
        print(f'Error parsing date {fecha}: {e}')
        return jsonify({'status': 'error', 'historias': []}), 400

@admin_bp.route('/especialidades', methods=['GET', 'POST'])
def especialidades():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        descripcion = (request.form.get('descripcion') or '').strip()

        if not nombre:
            flash('El nombre de la especialidad es obligatorio.', 'danger')
            return redirect(url_for('admin.especialidades'))
        if especialidad_repo.get_by_nombre(nombre):
            flash('Ya existe una especialidad con ese nombre.', 'warning')
            return redirect(url_for('admin.especialidades'))

        try:
            especialidad_repo.create(Especialidad.create(nombre, descripcion))
            flash('Especialidad creada correctamente.', 'success')
        except pyodbc.Error:
            flash('No se pudo crear la especialidad.', 'danger')
        return redirect(url_for('admin.especialidades'))

    return render_template('admin/especialidades.html', especialidades=especialidad_repo.get_all())

@admin_bp.route('/especialidades/<int:especialidad_id>/editar', methods=['POST'])
def editar_especialidad(especialidad_id: int):
    especialidad_actual = especialidad_repo.get_by_id(especialidad_id)
    if not especialidad_actual:
        flash('Especialidad no encontrada.', 'danger')
        return redirect(url_for('admin.especialidades'))

    nombre = (request.form.get('nombre') or '').strip()
    descripcion = (request.form.get('descripcion') or '').strip()

    if not nombre:
        flash('El nombre de la especialidad es obligatorio.', 'danger')
        return redirect(url_for('admin.especialidades'))

    existing = especialidad_repo.get_by_nombre(nombre)
    if existing and existing.id != especialidad_id:
        flash('Ya existe una especialidad con ese nombre.', 'warning')
        return redirect(url_for('admin.especialidades'))

    try:
        especialidad_repo.update(Especialidad(id=especialidad_id, nombre=nombre, descripcion=descripcion))
        flash('Especialidad actualizada correctamente.', 'success')
    except pyodbc.Error:
        flash('No se pudo actualizar la especialidad.', 'danger')
    return redirect(url_for('admin.especialidades'))

@admin_bp.route('/especialidades/<int:especialidad_id>/eliminar', methods=['POST'])
def eliminar_especialidad(especialidad_id: int):
    try:
        if not especialidad_repo.get_by_id(especialidad_id):
            flash('Especialidad no encontrada.', 'danger')
        else:
            especialidad_repo.delete(especialidad_id)
            flash('Especialidad eliminada correctamente.', 'success')
    except pyodbc.Error:
        flash('No se puede eliminar la especialidad porque está en uso.', 'warning')
    return redirect(url_for('admin.especialidades'))

@admin_bp.route('/medicos', methods=['GET', 'POST'])
def medicos():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        especialidad_id_raw = (request.form.get('especialidad_id') or '').strip()

        if not nombre or not especialidad_id_raw:
            flash('Completa todos los campos del médico.', 'danger')
            return redirect(url_for('admin.medicos'))

        try:
            especialidad_id = int(especialidad_id_raw)
        except ValueError:
            flash('Especialidad inválida.', 'danger')
            return redirect(url_for('admin.medicos'))

        if not especialidad_repo.get_by_id(especialidad_id):
            flash('La especialidad seleccionada no existe.', 'danger')
            return redirect(url_for('admin.medicos'))

        try:
            medico_repo.create(Medico.create(nombre, especialidad_id))
            flash('Médico creado correctamente.', 'success')
        except pyodbc.Error:
            flash('No se pudo crear el médico.', 'danger')
        return redirect(url_for('admin.medicos'))

    especialidades = especialidad_repo.get_all()
    especialidades_map = {esp.id: esp.nombre for esp in especialidades}
    return render_template(
        'admin/medicos.html',
        medicos=medico_repo.get_all(),
        especialidades=especialidades,
        especialidades_map=especialidades_map
    )

@admin_bp.route('/medicos/<int:medico_id>/editar', methods=['POST'])
def editar_medico(medico_id: int):
    medico_actual = medico_repo.get_by_id(medico_id)
    if not medico_actual:
        flash('Médico no encontrado.', 'danger')
        return redirect(url_for('admin.medicos'))

    nombre = (request.form.get('nombre') or '').strip()
    especialidad_id_raw = (request.form.get('especialidad_id') or '').strip()

    if not nombre or not especialidad_id_raw:
        flash('Completa todos los campos del médico.', 'danger')
        return redirect(url_for('admin.medicos'))

    try:
        especialidad_id = int(especialidad_id_raw)
    except ValueError:
        flash('Especialidad inválida.', 'danger')
        return redirect(url_for('admin.medicos'))

    if not especialidad_repo.get_by_id(especialidad_id):
        flash('La especialidad seleccionada no existe.', 'danger')
        return redirect(url_for('admin.medicos'))

    try:
        medico_repo.update(
            Medico(
                id=medico_id,
                nombre=nombre,
                especialidad_id=especialidad_id
            )
        )
        flash('Médico actualizado correctamente.', 'success')
    except pyodbc.Error:
        flash('No se pudo actualizar el médico.', 'danger')

    return redirect(url_for('admin.medicos'))

@admin_bp.route('/medicos/<int:medico_id>/eliminar', methods=['POST'])
def eliminar_medico(medico_id: int):
    try:
        if not medico_repo.get_by_id(medico_id):
            flash('Médico no encontrado.', 'danger')
        elif historia_repo.count_by_medico(medico_id) > 0:
            flash('No se puede eliminar el médico porque tiene historias registradas en admisión.', 'warning')
        else:
            medico_repo.delete(medico_id)
            flash('Médico eliminado correctamente.', 'success')
    except pyodbc.Error:
        flash('No se puede eliminar el médico porque está en uso.', 'warning')
    return redirect(url_for('admin.medicos'))
