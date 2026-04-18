from Persistencia.Repositorios.HistoriaRepository import HistoriaRepository
from Persistencia.Repositorios.EspecialidadRepository import EspecialidadRepository
from Persistencia.Repositorios.MedicoRepository import MedicoRepository
from Persistencia.Repositorios.ResponsableTriajeRepository import ResponsableTriajeRepository
from Dominio.Entidades.Historia import Historia
from Dominio.Entidades.Especialidad import Especialidad
from Dominio.Entidades.Medico import Medico
from Dominio.Entidades.ResponsableTriaje import ResponsableTriaje
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date

class HistoriaService:
    def __init__(self):
        self.historia_repo = HistoriaRepository()
        self.especialidad_repo = EspecialidadRepository()
        self.medico_repo = MedicoRepository()
        self.responsable_repo = ResponsableTriajeRepository()

    def registrar_historia(self, numero_historia: str, medico_id: int,
                           turno: str, responsable_triaje_id: int,
                           usuario_registro_id: int,
                           fecha_registro: Optional[datetime] = None,
                           estado: str = "Pendiente") -> int:
        if estado not in ["Pendiente", "Recibido"]:
            raise ValueError("Estado de historia inválido")

        historia = Historia.create(
            numero_historia=numero_historia,
            medico_id=medico_id,
            turno=turno,
            responsable_triaje_id=responsable_triaje_id,
            usuario_registro_id=usuario_registro_id,
            fecha_registro=fecha_registro,
            estado=estado
        )
        return self.historia_repo.create(historia)

    def cambiar_estado(self, historia_id: int, nuevo_estado: str) -> bool:
        if nuevo_estado not in ["Pendiente", "Recibido"]:
            return False
        return self.historia_repo.update_estado(historia_id, nuevo_estado)

    def eliminar_historia(self, historia_id: int) -> bool:
        return self.historia_repo.delete(historia_id)

    def actualizar_historia(self, historia_id: int, numero_historia: str, medico_id: int,
                            turno: str, responsable_triaje_id: int, estado: str) -> bool:
        if estado not in ["Pendiente", "Recibido"]:
            return False

        historia = self.historia_repo.get_by_id(historia_id)
        if not historia:
            return False

        historia.numero_historia = numero_historia
        historia.medico_id = medico_id
        historia.turno = turno
        historia.responsable_triaje_id = responsable_triaje_id
        historia.estado = estado
        return self.historia_repo.update(historia)

    def get_historias_por_fecha(self, fecha: date) -> List[Dict]:
        return self.historia_repo.get_resumen_by_fecha(fecha)

    def get_historias_por_rango(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        all_historias = self.historia_repo.get_resumen_all()
        filtered = []
        for h in all_historias:
            fecha_registro = datetime.strptime(h['fecha_registro'], '%d/%m/%Y %H:%M').date()
            if fecha_inicio <= fecha_registro <= fecha_fin:
                filtered.append(h)
        return filtered

    def get_all_historias(self) -> List[Dict]:
        return self.historia_repo.get_resumen_all()

    def get_registros_agrupados_por_dia(self) -> List[Dict]:
        """Agrupa historias por día calendario (para carpetas tipo admisión / admin)."""
        historias = self.get_all_historias()
        if not historias:
            historias_base = self.historia_repo.get_all()
            historias = [
                {
                    'estado': h.estado,
                    'fecha_registro': h.fecha_registro.strftime('%d/%m/%Y %H:%M') if h.fecha_registro else ''
                }
                for h in historias_base
            ]

        registros_map: Dict[str, Dict] = {}

        def normalize_fecha_display(fecha_registro):
            if not fecha_registro:
                return None
            fecha_texto = str(fecha_registro).strip()
            fecha_base = fecha_texto.split(' ')[0]
            formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
            for fmt in formatos:
                try:
                    return datetime.strptime(fecha_base, fmt).strftime('%d/%m/%Y')
                except Exception:
                    continue
            return None

        for h in historias:
            fecha = normalize_fecha_display(h.get('fecha_registro'))
            if not fecha:
                continue
            if fecha not in registros_map:
                registros_map[fecha] = {
                    'fecha': fecha,
                    'total': 0,
                    'pendientes': 0,
                    'recibidas': 0
                }
            registros_map[fecha]['total'] += 1
            if h['estado'] == 'Recibido':
                registros_map[fecha]['recibidas'] += 1
            else:
                registros_map[fecha]['pendientes'] += 1

        def parse_date(d_str: str) -> datetime:
            try:
                return datetime.strptime(d_str, '%d/%m/%Y')
            except Exception:
                return datetime.min

        return sorted(
            registros_map.values(),
            key=lambda item: parse_date(item['fecha']),
            reverse=True
        )

    def _enrich_historias(self, historias: List[Historia]) -> List[Dict]:
        especialidades = {e.id: e.nombre for e in self.especialidad_repo.get_all()}
        medicos = {m.id: m for m in self.medico_repo.get_all()}
        responsables = {r.id: r.nombre for r in self.responsable_repo.get_all()}

        result = []
        for h in historias:
            medico = medicos.get(h.medico_id)
            especialidad_nombre = 'N/A'
            medico_nombre = 'N/A'
            if medico:
                medico_nombre = medico.nombre
                especialidad_nombre = especialidades.get(medico.especialidad_id, 'N/A')

            result.append({
                'id': h.id,
                'numero_historia': h.numero_historia,
                'especialidad': especialidad_nombre,
                'medico': medico_nombre,
                'turno': h.turno,
                'responsable_triaje': responsables.get(h.responsable_triaje_id, 'N/A'),
                'estado': h.estado,
                'fecha_registro': h.fecha_registro.strftime('%d/%m/%Y %H:%M')
            })
        return result

    def get_especialidades(self):
        return self.especialidad_repo.get_all()

    def get_medicos(self):
        return self.medico_repo.get_all()

    def get_responsables_triaje(self):
        return self.responsable_repo.get_all()

    def create_especialidad(self, nombre: str, descripcion: str = "") -> int:
        esp = Especialidad.create(nombre, descripcion)
        return self.especialidad_repo.create(esp)

    def create_medico(self, nombre: str, especialidad_id: int) -> int:
        med = Medico.create(nombre, especialidad_id)
        return self.medico_repo.create(med)

    def create_responsable(self, nombre: str, area: str = "") -> int:
        resp = ResponsableTriaje.create(nombre, area)
        return self.responsable_repo.create(resp)

    def get_or_create_responsable_id(self, nombre: str) -> int:
        nombre_normalizado = (nombre or "").strip()
        if not nombre_normalizado:
            raise ValueError("El nombre del responsable de triaje es obligatorio")

        existente = self.responsable_repo.get_by_nombre(nombre_normalizado)
        if existente:
            return existente.id

        return self.create_responsable(nombre_normalizado)

    def validar_duplicados_numero_historia_mismo_dia(
        self,
        fecha_dia_nuevas: date,
        historias: List[dict],
        actualizaciones: List[dict],
    ) -> Tuple[bool, str]:
        """
        Mismo día + mismo número de historia: no puede repetirse si comparten médico o turno.
        Solo se permite repetir número con médico distinto Y turno distinto.
        """

        def _norm_num(n) -> str:
            return (n or "").strip()

        def _norm_turno(t) -> str:
            return (t or "").strip().upper()

        def _choque(n1: str, med1: int, t1: str, n2: str, med2: int, t2: str) -> bool:
            if _norm_num(n1) != _norm_num(n2):
                return False
            return int(med1) == int(med2) or _norm_turno(t1) == _norm_turno(t2)

        def _post_update_triple(cid: int) -> Optional[Tuple[str, int, str]]:
            if cid not in update_new_by_id:
                return None
            nu, tu, mu = update_new_by_id[cid]
            return (nu, mu, tu)

        new_triples: List[Tuple[str, int, str]] = []
        for x in historias:
            n = _norm_num(x.get("numero_historia"))
            raw_med = x.get("medico_id")
            med = int(raw_med) if raw_med is not None and str(raw_med).strip() != "" else 0
            t = _norm_turno(x.get("turno"))
            new_triples.append((n, med, t))

        for i in range(len(new_triples)):
            n1, m1, t1 = new_triples[i]
            for j in range(i + 1, len(new_triples)):
                n2, m2, t2 = new_triples[j]
                if _choque(n1, m1, t1, n2, m2, t2):
                    return False, (
                        "Hay filas nuevas con el mismo número de historia que comparten médico o turno. "
                        "Solo puede repetirse el número el mismo día con otro médico y otro turno."
                    )

        update_rows: List[Tuple[int, str, str, date, int]] = []
        for item in actualizaciones:
            raw_id = item.get("id")
            if raw_id is None:
                continue
            hid = int(raw_id)
            ent = self.historia_repo.get_by_id(hid)
            if not ent:
                return False, f"No se encontró la historia con id {hid}."
            f_d = ent.fecha_registro.date() if ent.fecha_registro else date.today()
            nu = _norm_num(item.get("numero_historia"))
            tu = _norm_turno(item.get("turno"))
            raw_med = item.get("medico_id")
            med_u = int(raw_med) if raw_med is not None and str(raw_med).strip() != "" else 0
            update_rows.append((hid, nu, tu, f_d, med_u))

        update_new_by_id = {uid: (nu, tu, med_u) for uid, nu, tu, _, med_u in update_rows}

        for i in range(len(update_rows)):
            uid_a, n_a, t_a, f_a, m_a = update_rows[i]
            for j in range(i + 1, len(update_rows)):
                uid_b, n_b, t_b, f_b, m_b = update_rows[j]
                if f_a != f_b:
                    continue
                if _choque(n_a, m_a, t_a, n_b, m_b, t_b):
                    return False, (
                        "Las actualizaciones dejarían el mismo número de historia con el mismo médico "
                        "o el mismo turno en un mismo día."
                    )

        for n_n, m_n, t_n in new_triples:
            for uid_u, n_u, t_u, f_u, m_u in update_rows:
                if fecha_dia_nuevas != f_u:
                    continue
                if _choque(n_n, m_n, t_n, n_u, m_u, t_u):
                    return False, (
                        f"El número {n_n} choca con una fila que estás editando el {f_u.strftime('%d/%m/%Y')} "
                        "(mismo médico o mismo turno). Solo puede repetirse con otro médico y otro turno."
                    )

        def _bloqueado_por_fila_db(
            n_cand: str, m_cand: int, t_cand: str, f_cand: date, excluir_id: Optional[int]
        ) -> Tuple[bool, str]:
            for cid, m_r, t_r in self.historia_repo.list_id_medico_turno_por_numero_fecha(n_cand, f_cand):
                if excluir_id is not None and cid == excluir_id:
                    continue
                if not _choque(n_cand, m_cand, t_cand, n_cand, m_r, t_r):
                    continue
                post = _post_update_triple(cid)
                if post is not None:
                    n2, m2, t2 = post
                    if not _choque(n_cand, m_cand, t_cand, n2, m2, t2):
                        continue
                return True, (
                    f"Ya existe o quedaría un conflicto con el número {n_cand} el {f_cand.strftime('%d/%m/%Y')} "
                    "mientras comparta médico o turno con otro registro. "
                    "Solo puede repetirse el mismo día con otro médico y otro turno."
                )
            return False, ""

        for uid, n_new, t_new, f_d, m_new in update_rows:
            blocked, msg = _bloqueado_por_fila_db(n_new, m_new, t_new, f_d, excluir_id=uid)
            if blocked:
                return False, msg

        for n_n, m_n, t_n in new_triples:
            blocked, msg = _bloqueado_por_fila_db(n_n, m_n, t_n, fecha_dia_nuevas, excluir_id=None)
            if blocked:
                return False, msg

        return True, ""
