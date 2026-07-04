"""Estado de sesión del proyecto: única fuente de verdad de la GUI."""
from __future__ import annotations

from dataclasses import dataclass, field

_CLAVES_DATOS = (
    "circuitos", "trafo", "protecciones", "cadena", "balance_datos",
    "tableros", "params_demanda", "generador", "ups", "sts", "ats",
    "trafo_iso", "proyecto", "perfil", "trafo_z_ohm", "tension_sistema_v",
)


@dataclass
class SesionProyecto:
    circuitos: list = field(default_factory=list)
    trafo: dict | None = None
    protecciones: dict = field(default_factory=dict)
    cadena: list = field(default_factory=list)
    balance_datos: dict = field(default_factory=dict)
    tableros: dict = field(default_factory=dict)
    params_demanda: dict = field(default_factory=dict)
    generador: dict | None = None
    ups: dict | None = None
    sts: dict | None = None
    ats: dict | None = None
    trafo_iso: dict | None = None
    proyecto: str = ""
    perfil: str = ""
    trafo_z_ohm: float = 0.0
    tension_sistema_v: float = 380.0
    resultados: dict = field(default_factory=dict)

    def cargar(self, datos: dict) -> None:
        for clave in _CLAVES_DATOS:
            if clave in datos and datos[clave] is not None:
                setattr(self, clave, datos[clave])

    def registrar(self, modulo_id: str, resultado, alertas: list | None = None) -> None:
        self.resultados[modulo_id] = {"resultado": resultado, "alertas": list(alertas or [])}

    @property
    def tiene_circuitos(self) -> bool:
        return bool(self.circuitos)

    @property
    def tiene_trafo(self) -> bool:
        return self.trafo is not None

    @property
    def tiene_protecciones(self) -> bool:
        return bool(self.protecciones)

    @property
    def tiene_cadena(self) -> bool:
        return bool(self.cadena)

    @property
    def tiene_icc(self) -> bool:
        return "icc_punto" in self.resultados
