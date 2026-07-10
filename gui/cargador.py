"""Carga un libro Excel a una SesionProyecto usando los lectores existentes."""
from __future__ import annotations

import openpyxl

import excel
from protecciones import leer_protecciones_excel
from transformador import calcular_icc_transformador, icc_desde_tabla
from gui_core.sesion import SesionProyecto


def _leer_seguro(fn, *args, default=None):
    """Ejecuta un lector de hoja OPCIONAL sin dejar que un dato mal formado
    en esa hoja tumbe toda la carga: si `fn(*args)` lanza cualquier
    excepción, se ignora y se retorna `default` (la sección queda vacía,
    el resto de la carga continúa normalmente).
    """
    try:
        return fn(*args)
    except Exception:
        return default


def cargar_excel_a_sesion(ruta: str, sesion: SesionProyecto) -> dict:
    """Lee todas las hojas soportadas y las carga en la sesión.

    Retorna un resumen {"hojas": int, "error": str|None}. Nunca crashea.
    """
    try:
        circuitos = excel.leer_circuitos_excel(ruta)
    except Exception as e:
        return {"hojas": 0, "error": str(e)}

    try:
        libro = openpyxl.load_workbook(ruta, data_only=True)
    except Exception as e:
        return {"hojas": 0, "error": str(e)}

    trafo = _leer_seguro(excel.leer_transformador_excel, ruta)
    datos = {
        "circuitos": circuitos,
        "trafo": trafo,
        "protecciones": _leer_seguro(leer_protecciones_excel, libro, default={}) or {},
        "cadena": _leer_seguro(excel.leer_cadena_excel, libro, default=[]) or [],
        "balance_datos": _leer_seguro(excel.leer_balance_excel, libro, default={}) or {},
        "tableros": _leer_seguro(excel.leer_tableros_excel, libro, default={}) or {},
        "params_demanda": _leer_seguro(excel.leer_demanda_excel, libro, default={}) or {},
        "generador": _leer_seguro(excel.leer_generador_excel, libro),
        "ups": _leer_seguro(excel.leer_ups_excel, libro),
        "sts": _leer_seguro(excel.leer_sts_excel, libro),
        "ats": _leer_seguro(excel.leer_ats_excel, libro),
        "trafo_iso": _leer_seguro(excel.leer_trafo_iso_excel, libro),
    }
    perfil = _leer_seguro(excel.leer_perfil_excel, libro, default={}) or {}
    datos["proyecto"] = perfil.get("nombre_proyecto", "PROYECTO")
    datos["perfil"] = perfil.get("perfil", "industrial")

    # Impedancia y tensión de barra para el flujo nodal (derivadas del trafo).
    # Si el cálculo falla (p.ej. hoja "Transformador" en modo B sin kVA →
    # ZeroDivisionError, o datos incompletos/tipos inválidos) simplemente NO
    # se setean estas dos claves — el resto de la carga (circuitos,
    # protecciones, cadena, etc.) sigue funcionando normalmente.
    if trafo:
        try:
            vn = float(trafo.get("Vn_BT", 380))
            if str(trafo.get("modo", "B")).upper() == "A":
                _, zt, _ = calcular_icc_transformador(trafo["kVA"], vn, trafo["Ucc_pct"])
            else:
                _, ucc, _ = icc_desde_tabla(trafo["kVA"])
                zt = (ucc / 100.0) * (vn ** 2 / (trafo["kVA"] * 1000.0))
            datos["tension_sistema_v"] = vn
            datos["trafo_z_ohm"] = float(zt)
        except (ZeroDivisionError, KeyError, TypeError, ValueError):
            pass

    sesion.cargar({k: v for k, v in datos.items() if v is not None})
    hojas = sum(1 for k in ("circuitos", "trafo", "protecciones", "cadena", "tableros",
                             "balance_datos", "params_demanda", "generador", "ups",
                             "sts", "ats", "trafo_iso")
                if getattr(sesion, k, None))
    return {"hojas": hojas, "error": None}
