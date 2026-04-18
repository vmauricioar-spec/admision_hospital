from typing import Dict

class LoginViewModel:
    def __init__(self, username: str = "", error: str = ""):
        self.username = username
        self.error = error

class DashboardViewModel:
    def __init__(self, usuario_nombre: str, usuario_role: str, cantidades: Dict):
        self.usuario_nombre = usuario_nombre
        self.usuario_role = usuario_role
        self.cantidades = cantidades

class RegistroViewModel:
    def __init__(self, especialidades: list, medicos: list, responsables: list):
        self.especialidades = especialidades
        self.medicos = medicos
        self.responsables = responsables

class HistoriaListViewModel:
    def __init__(self, historias: list, total: int):
        self.historias = historias
        self.total = total
