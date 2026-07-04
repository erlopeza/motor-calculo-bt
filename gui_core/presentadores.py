"""Presentadores: orquestan los motores existentes desde una SesionProyecto.

Cada presentador devuelve un dict con datos estructurados + 'alertas' (lista).
No importan tkinter. La sesión guarda el resultado vía registrar().
"""
from __future__ import annotations

from calculos import calcular_caida_tension, clasificar_caida, capacidad_corregida, sugerir_conductor
from transformador import calcular_icc_transformador, icc_desde_tabla
from icc_punto import calcular_icc_punto, calcular_icc_con_aporte_motores
from motores import calcular_aporte_icc_motor
from conductores import TENSION_SISTEMA
from arc_flash import arc_flash_desde_proteccion
from protecciones import verificar_circuito_completo
from coordinacion import calcular_tiempo_disparo
from balance import calcular_balance_tableros
from demanda import calcular_demanda
from red_desde_cadena import construir_red
from flujo_nodal import calcular_flujo_nodal
from gui_core.sesion import SesionProyecto


def _zt_trafo(sesion: SesionProyecto) -> float:
    t = sesion.trafo or {}
    if not t:
        return 0.0
    if str(t.get("modo", "B")).upper() == "A":
        _, zt, _ = calcular_icc_transformador(t["kVA"], t["Vn_BT"], t["Ucc_pct"])
    else:
        icc, ucc, _ = icc_desde_tabla(t["kVA"])
        vn = float(t.get("Vn_BT", 380))
        zt = (ucc / 100.0) * (vn ** 2 / (t["kVA"] * 1000.0))
    return float(zt)


def presentar_dv(sesion: SesionProyecto) -> dict:
    filas, alertas = [], []
    for c in sesion.circuitos:
        dv_v, dv_pct = calcular_caida_tension(
            c["L_m"], c["S_mm2"], c["I_diseno"], c["paralelos"], c["sistema"]
        )
        estado = clasificar_caida(dv_pct)
        if str(estado).upper() == "FALLA":
            alertas.append(c["nombre"])
        filas.append({"nombre": c["nombre"], "dv_v": dv_v, "dv_pct": dv_pct, "estado": estado})
    return {"filas": filas, "alertas": alertas}


def presentar_capacidad(sesion: SesionProyecto) -> dict:
    filas, alertas = [], []
    for c in sesion.circuitos:
        cap = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
        ok = c["I_diseno"] <= cap
        if not ok:
            alertas.append(c["nombre"])
        filas.append({"nombre": c["nombre"], "I_diseno": c["I_diseno"], "cap_A": cap, "ok": ok})
    return {"filas": filas, "alertas": alertas}


def presentar_icc_trafo(sesion: SesionProyecto) -> dict:
    t = sesion.trafo or {}
    if str(t.get("modo", "B")).upper() == "A":
        icc, zt, info = calcular_icc_transformador(t["kVA"], t["Vn_BT"], t["Ucc_pct"])
    else:
        icc, ucc, kva_ref = icc_desde_tabla(t["kVA"])
        zt = _zt_trafo(sesion)
    return {"Icc_kA": round(float(icc), 2), "Zt_ohm": round(float(zt), 6), "alertas": []}


def presentar_icc_punto(sesion: SesionProyecto) -> dict:
    zt = _zt_trafo(sesion)
    filas, alertas = [], []
    for c in sesion.circuitos:
        icc, zt_total, zt_cable = calcular_icc_punto(
            zt, c["L_m"], c["S_mm2"], c["paralelos"], c["sistema"]
        )
        filas.append({"nombre": c["nombre"], "Icc_kA": icc, "Zt_total": zt_total})
    return {"filas": filas, "alertas": alertas}


def presentar_protecciones(sesion: SesionProyecto) -> dict:
    zt = _zt_trafo(sesion)
    filas, alertas = [], []
    for c in sesion.circuitos:
        prot = sesion.protecciones.get(c["nombre"])
        if not prot:
            continue
        icc, _, _ = calcular_icc_punto(zt, c["L_m"], c["S_mm2"], c["paralelos"], c["sistema"])
        vn = TENSION_SISTEMA.get(c["sistema"], 380)
        r = verificar_circuito_completo(
            c["nombre"], prot["In_A"], prot["curva"],
            prot.get("poder_corte_kA", 0), icc, vn,
        )
        if str(r.get("estado", "")).upper() != "OK":
            alertas.append(c["nombre"])
        filas.append({"nombre": c["nombre"], "estado": r.get("estado"), "Icc_kA": icc})
    return {"filas": filas, "alertas": alertas}


def presentar_coordinacion(sesion: SesionProyecto) -> dict:
    if not sesion.tiene_cadena:
        return {"filas": [], "alertas": []}
    filas, alertas = [], []
    for d in sesion.cadena:
        r = calcular_tiempo_disparo(
            (d.get("Icc_kA", 0) or 0) * 1000.0, d.get("In_A", 0), d.get("curva", "C"),
        )
        if r["region"] == "verificar_simaris":
            alertas.append(d.get("nombre", "?"))
        filas.append({"nombre": d.get("nombre"), "t_s": r["t_s"], "region": r["region"]})
    return {"filas": filas, "alertas": alertas}


def presentar_arc_flash(sesion: SesionProyecto) -> dict:
    zt = _zt_trafo(sesion)
    filas, alertas = [], []
    for c in sesion.circuitos:
        prot = sesion.protecciones.get(c["nombre"])
        if not prot:
            continue
        icc, _, _ = calcular_icc_punto(zt, c["L_m"], c["S_mm2"], c["paralelos"], c["sistema"])
        vn_kv = TENSION_SISTEMA.get(c["sistema"], 380) / 1000.0
        r = arc_flash_desde_proteccion(icc, vn_kv, prot["In_A"], prot["curva"])
        if r["despeje_incierto"] or (r["categoria_ppe"] is None):
            alertas.append(c["nombre"])
        filas.append({
            "nombre": c["nombre"], "E_cal_cm2": r["E_cal_cm2"],
            "D_afb_mm": r["D_afb_mm"], "categoria_ppe": r["categoria_ppe"],
        })
    return {"filas": filas, "alertas": alertas}


def presentar_balance(sesion: SesionProyecto) -> dict:
    if not (sesion.tiene_circuitos and sesion.tableros):
        return {"tableros": {}, "alertas": []}
    kva = float((sesion.trafo or {}).get("kVA", 0) or 0)
    r = calcular_balance_tableros(sesion.circuitos, sesion.balance_datos, sesion.tableros, kva)
    return {"resultado": r, "tableros": r.get("tableros", {}), "alertas": []}


def presentar_demanda(sesion: SesionProyecto) -> dict:
    if not sesion.tiene_circuitos:
        return {"resultado": None, "alertas": []}
    r = calcular_demanda(sesion.circuitos, sesion.balance_datos, sesion.params_demanda)
    return {"resultado": r, "alertas": []}


def presentar_flujo_nodal(sesion: SesionProyecto) -> dict:
    if not (sesion.tiene_cadena and sesion.trafo_z_ohm > 0):
        return {"buses": [], "convergido": False, "perdidas_kW": 0.0, "alertas": []}
    red = construir_red(sesion.cadena, sesion.trafo_z_ohm, sesion.circuitos,
                        vn_v=sesion.tension_sistema_v)
    if not red.ramas:
        return {"buses": [], "convergido": False, "perdidas_kW": 0.0,
                "alertas": ["sin nodos con Icc válida"]}
    res = calcular_flujo_nodal(red)
    alertas = [] if res["convergido"] else ["no convergió"]
    buses = [{"id": b, "V_pu": r["V_pu"], "V_kV": r["V_kV"], "P_kW": r["P_kW"]}
             for b, r in res["buses"].items()]
    return {"buses": buses, "convergido": res["convergido"],
            "perdidas_kW": res["perdidas_totales_kW"], "alertas": alertas}


def presentar_sugerencia(sesion: SesionProyecto) -> dict:
    filas, alertas = [], []
    for c in sesion.circuitos:
        norma = str(c.get("norma", "MM2"))
        cond, cap, dv = sugerir_conductor(
            c["L_m"], c["I_diseno"], c["paralelos"], c["sistema"], c["temp_amb"], norma
        )
        if cond is None:  # ningún conductor cumple ΔV/capacidad → hallazgo
            alertas.append(c["nombre"])
        filas.append({"nombre": c["nombre"], "sugerido": cond, "cap_A": cap, "dv_pct": dv})
    return {"filas": filas, "alertas": alertas}


def presentar_aporte_motores(sesion: SesionProyecto) -> dict:
    motores_circ = [
        c for c in sesion.circuitos
        if str(c.get("tipo_carga", "")).lower() == "motor" and c.get("P_kW")
    ]
    if not motores_circ:
        return {"filas": [], "Icc_red_kA": 0.0, "Icc_total_kA": 0.0, "alertas": []}
    filas, aportes = [], []
    for c in motores_circ:
        vn = TENSION_SISTEMA.get(c["sistema"], 380)
        ap = calcular_aporte_icc_motor(float(c["P_kW"]), vn, sistema=c["sistema"])
        aportes.append(ap["I_aporte_A"])
        filas.append({"nombre": c["nombre"], "P_kW": float(c["P_kW"]), "I_aporte_A": ap["I_aporte_A"]})
    icc_red = presentar_icc_trafo(sesion)["Icc_kA"] if sesion.tiene_trafo else 0.0
    icc_total, _ = calcular_icc_con_aporte_motores(icc_red, aportes)
    return {"filas": filas, "Icc_red_kA": icc_red, "Icc_total_kA": icc_total, "alertas": []}
