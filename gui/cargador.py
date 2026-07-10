"""Carga un libro Excel a una SesionProyecto usando los lectores existentes."""
from __future__ import annotations

import openpyxl

import excel
from protecciones import leer_protecciones_excel
from transformador import calcular_icc_transformador, icc_desde_tabla
from gui_core.sesion import SesionProyecto


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

    trafo = excel.leer_transformador_excel(ruta)
    datos = {
        "circuitos": circuitos,
        "trafo": trafo,
        "protecciones": leer_protecciones_excel(libro) or {},
        "cadena": excel.leer_cadena_excel(libro) or [],
        "balance_datos": excel.leer_balance_excel(libro) or {},
        "tableros": excel.leer_tableros_excel(libro) or {},
        "params_demanda": excel.leer_demanda_excel(libro) or {},
        "generador": excel.leer_generador_excel(libro),
        "ups": excel.leer_ups_excel(libro),
        "sts": excel.leer_sts_excel(libro),
        "ats": excel.leer_ats_excel(libro),
        "trafo_iso": excel.leer_trafo_iso_excel(libro),
    }
    perfil = excel.leer_perfil_excel(libro) or {}
    datos["proyecto"] = perfil.get("nombre_proyecto", "PROYECTO")
    datos["perfil"] = perfil.get("perfil", "industrial")

    # Impedancia y tensión de barra para el flujo nodal (derivadas del trafo).
    if trafo:
        vn = float(trafo.get("Vn_BT", 380))
        datos["tension_sistema_v"] = vn
        if str(trafo.get("modo", "B")).upper() == "A":
            _, zt, _ = calcular_icc_transformador(trafo["kVA"], vn, trafo["Ucc_pct"])
        else:
            icc, ucc, kva_ref = icc_desde_tabla(trafo["kVA"])
            zt = (ucc / 100.0) * (vn ** 2 / (trafo["kVA"] * 1000.0))
        datos["trafo_z_ohm"] = float(zt)

    sesion.cargar({k: v for k, v in datos.items() if v is not None})
    hojas = sum(1 for k in ("circuitos", "trafo", "protecciones", "cadena", "tableros")
                if getattr(sesion, k, None))
    return {"hojas": hojas, "error": None}
