"""Registro declarativo de fases y módulos + derivación de estado."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from gui_core.estado import Estado
from gui_core.sesion import SesionProyecto

FASES = {
    0: "Datos",
    1: "Cálculo base",
    2: "Cortocircuito",
    3: "Protección",
    4: "Carga y red",
    5: "Emergencia",
    6: "Reporte",
}


@dataclass(frozen=True)
class Modulo:
    id: str
    nombre: str
    norma: str
    fase: int
    requiere: str
    prereq: Callable[[SesionProyecto], bool]


MODULOS: list[Modulo] = [
    Modulo("dv", "Caída de tensión ΔV", "NCh Elec 4/2003 · IEC 60364", 1,
           "circuitos", lambda s: s.tiene_circuitos),
    Modulo("capacidad", "Capacidad de conductor", "IEC 60364-5-52", 1,
           "circuitos", lambda s: s.tiene_circuitos),
    Modulo("sugerencia", "Sugerencia de sección", "SEC RIC N°04", 1,
           "circuitos", lambda s: s.tiene_circuitos),
    Modulo("icc_trafo", "Icc bornes transformador", "IEC 60909 · IEC 60076", 2,
           "transformador", lambda s: s.tiene_trafo),
    Modulo("icc_punto", "Icc por punto + fase-neutro", "IEC 60909-2 · IEC 60364-4-41", 2,
           "trafo + circuitos", lambda s: s.tiene_trafo and s.tiene_circuitos),
    Modulo("aporte_motores", "Aporte de motores al Icc", "IEC 60909-4:2021", 2,
           "trafo + circuitos", lambda s: s.tiene_trafo and s.tiene_circuitos),
    Modulo("protecciones", "Verificación de protecciones", "IEC 60947-2 · IEC 60364-4-41", 3,
           "Icc + protecciones", lambda s: s.tiene_icc and s.tiene_protecciones),
    Modulo("coordinacion", "Coordinación TCC / selectividad", "IEC 60947-2 (M7)", 3,
           "cadena", lambda s: s.tiene_cadena),
    Modulo("arc_flash", "Arc Flash", "IEEE 1584-2002 · NFPA 70E", 3,
           "Icc + protección", lambda s: s.tiene_icc and s.tiene_protecciones),
    Modulo("balance", "Balance por tablero", "NCh Elec 4/2003", 4,
           "circuitos + tableros", lambda s: s.tiene_circuitos and bool(s.tableros)),
    Modulo("demanda", "Demanda máxima (M6)", "RIC N°03 SEC · IEC 60076", 4,
           "circuitos", lambda s: s.tiene_circuitos),
    Modulo("flujo_nodal", "Flujo de carga nodal", "IEEE 399 · IEC 60909", 4,
           "cadena + trafo", lambda s: s.tiene_cadena and s.trafo_z_ohm > 0),
    Modulo("generador", "Grupo electrógeno + ATS + autonomía", "RIC N°08 SEC · ISO 8528", 5,
           "demanda/cargas", lambda s: s.generador is not None or s.tiene_circuitos),
    Modulo("trafo_iso", "Transformador de aislamiento", "IEC 61558 · IEEE C57.110", 5,
           "cargas", lambda s: s.trafo_iso is not None),
    Modulo("ups", "UPS", "IEC 62040", 5,
           "cargas críticas", lambda s: s.ups is not None),
    Modulo("sts", "STS", "IEC 62310", 5,
           "cargas", lambda s: s.sts is not None),
    Modulo("arranque", "Arranque de motores", "IEC 60947-4-1", 5,
           "motores", lambda s: s.tiene_circuitos),
    Modulo("reporte", "Memoria SEC (DOCX/PDF/JSON EPC)", "SEC RIC", 6,
           "cálculos hechos", lambda s: bool(s.resultados)),
]

_INDICE = {m.id: m for m in MODULOS}
_PRIORIDAD = {Estado.ALERTA: 3, Estado.CALCULADO: 2, Estado.LISTO: 1, Estado.SIN_DATOS: 0}


def buscar_modulo(modulo_id: str) -> Modulo | None:
    return _INDICE.get(modulo_id)


def modulos_de_fase(fase: int) -> list[Modulo]:
    return [m for m in MODULOS if m.fase == fase]


def estado_modulo(modulo: Modulo, sesion: SesionProyecto) -> Estado:
    if not modulo.prereq(sesion):
        return Estado.SIN_DATOS
    res = sesion.resultados.get(modulo.id)
    if res is None:
        return Estado.LISTO
    return Estado.ALERTA if res.get("alertas") else Estado.CALCULADO


def estado_fase(fase: int, sesion: SesionProyecto) -> Estado:
    estados = [estado_modulo(m, sesion) for m in modulos_de_fase(fase)]
    if not estados:
        return Estado.SIN_DATOS
    return max(estados, key=lambda e: _PRIORIDAD[e])


from gui_core import presentadores as _p

PRESENTADOR = {
    "dv": _p.presentar_dv,
    "capacidad": _p.presentar_capacidad,
    "sugerencia": _p.presentar_sugerencia,
    "aporte_motores": _p.presentar_aporte_motores,
    "icc_trafo": _p.presentar_icc_trafo,
    "icc_punto": _p.presentar_icc_punto,
    "protecciones": _p.presentar_protecciones,
    "coordinacion": _p.presentar_coordinacion,
    "arc_flash": _p.presentar_arc_flash,
    "balance": _p.presentar_balance,
    "demanda": _p.presentar_demanda,
    "flujo_nodal": _p.presentar_flujo_nodal,
}
