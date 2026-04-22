"""Motor de comparacion y categorizacion de divergencias."""

from __future__ import annotations

import math
from typing import Any

from calculos import RHO_CU, calcular_caida_tension
from generador import calcular_icc_ge
from icc_punto import calcular_icc_punto


def _icc_trafo(sn_kva: float, ukr_pct: float, vn_v: float, c_max: float, c_min: float) -> dict:
    sn_va = float(sn_kva) * 1000.0
    zt_ohm = (float(ukr_pct) / 100.0) * (float(vn_v) ** 2 / sn_va)
    icc_nom_a = float(vn_v) / (math.sqrt(3.0) * zt_ohm)
    icc_max_a = float(c_max) * icc_nom_a
    icc_min_a = float(c_min) * icc_nom_a
    return {
        "Icc_nom_kA": round(icc_nom_a / 1000.0, 3),
        "Icc_max_kA": round(icc_max_a / 1000.0, 3),
        "Icc_min_kA": round(icc_min_a / 1000.0, 3),
        "Zt_ohm": round(zt_ohm, 6),
    }


def _dv_pct_temp(l_m: float, s_mm2: float, ib_a: float, vn_v: float, sistema: str, temp_c: float) -> float:
    # Ajuste simple de resistividad Cu respecto de 20C.
    alpha = 0.004
    rho_t = RHO_CU * (1.0 + alpha * (float(temp_c) - 20.0))
    factor = 1.732 if str(sistema).upper() == "3F" else 2.0
    dv_v = (factor * rho_t * float(l_m) * float(ib_a)) / max(float(s_mm2), 1e-9)
    return round((dv_v / float(vn_v)) * 100.0, 3)


def calcular_resultado_motor(escenario: dict) -> dict:
    """
    Ejecuta calculo Motor BT para el escenario dado.
    """
    modulo = escenario["modulo_motor"]
    p = dict(escenario.get("parametros_motor") or {})

    if modulo == "transformador":
        return _icc_trafo(
            sn_kva=p["Sn_kVA"],
            ukr_pct=p["Ukr_pct"],
            vn_v=p["Vn_V"],
            c_max=p.get("c_max", 1.1),
            c_min=p.get("c_min", 0.95),
        )

    if modulo == "icc_punto":
        base = _icc_trafo(
            sn_kva=p["Sn_kVA"],
            ukr_pct=p["Ukr_pct"],
            vn_v=p["Vn_V"],
            c_max=p.get("c_max", 1.1),
            c_min=0.95,
        )
        icc_kA, zt_total, zt_cable = calcular_icc_punto(
            Zt_trafo_ohm=base["Zt_ohm"],
            L_m=p["L_cable_m"],
            S_mm2=p["seccion_mm2"],
            paralelos=p.get("n_cables_paralelo", p.get("n_cables", 1)),
            sistema="3F",
        )
        icc_max = round(icc_kA * (p.get("c_max", 1.1) / 1.0), 3)
        return {
            "Icc_kA": round(icc_kA, 3),
            "Icc_max_kA": icc_max,
            "Zt_total_ohm": zt_total,
            "Zt_cable_ohm": zt_cable,
        }

    if modulo == "generador":
        icc = calcular_icc_ge(
            P_kVA=p["Sn_kVA"],
            V_nominal=p["Vn_V"],
            Xd_pp_pct=p.get("Xd_pp_pct", 20.0),
            Xd_p_pct=p.get("Xd_p_pct", 28.0),
            Xd_pct=p.get("Xd_pct", 120.0),
            R1_pct=p.get("R1_pct", 2.0) if p.get("R1_pct") is not None else 2.0,
            Rs_ohm=p.get("Rs_ohm"),
            X0_pct=p.get("X0_pct", 5.0),
            c_max=p.get("c_max", 1.05),
            c_min=p.get("c_min", 0.95),
        )
        return {
            "Icc_kA": icc["Ik3_pp_kA"],
            "Ik3_pp_kA": icc["Ik3_pp_kA"],
            "Ik3_p_kA": icc["Ik3_p_kA"],
            "Ik3_kA": icc["Ik3_kA"],
            "Ik1_pp_kA": icc["Ik1_pp_kA"],
        }

    if modulo == "calculos":
        if "tramos" in p:
            dv_sum = 0.0
            for tramo in p["tramos"]:
                _, dv = calcular_caida_tension(
                    L_m=tramo["L_m"],
                    S_mm2=tramo["seccion_mm2"],
                    I_diseno=tramo["Ib_A"],
                    paralelos=1,
                    sistema=p.get("sistema", "3F"),
                )
                dv_sum += float(dv)
            return {"sum_dv_pct": round(dv_sum, 3)}

        dv_t20 = _dv_pct_temp(
            l_m=p["L_m"],
            s_mm2=p["seccion_mm2"],
            ib_a=p["Ib_A"],
            vn_v=p["Vn_V"],
            sistema=p.get("sistema", "3F"),
            temp_c=p.get("T_conductor_C", 20),
        )
        dv_t60 = _dv_pct_temp(
            l_m=p["L_m"],
            s_mm2=p["seccion_mm2"],
            ib_a=p["Ib_A"],
            vn_v=p["Vn_V"],
            sistema=p.get("sistema", "3F"),
            temp_c=p.get("T_conductor_op_C", 60),
        )
        return {
            "dv_t20_pct": dv_t20,
            "dv_t60_pct": dv_t60,
            "dv_tramo_pct": dv_t60,
        }

    if modulo == "demanda":
        gi_sim = float(p.get("gi_simaris", 0.75))
        gi_real = float(p.get("gi_real_datacenter", 0.85))
        ib_sim = float((escenario.get("resultado_simaris") or {}).get("Ib_A") or 0.0)
        ib_base = ib_sim / max(gi_sim, 1e-9)
        ib_motor = ib_base * gi_real
        return {
            "Ib_A": round(ib_motor, 3),
            "Ib_base_A": round(ib_base, 3),
            "gi_real": gi_real,
            "gi_simaris": gi_sim,
        }

    raise ValueError(f"Modulo no soportado: {modulo}")


def calcular_divergencia(
    resultado_motor: dict,
    resultado_simaris: dict,
    metrica: str
) -> float:
    """
    divergencia_pct = (motor - simaris) / simaris * 100
    """
    motor = float(resultado_motor.get(metrica) or 0.0)
    sim = float(resultado_simaris.get(metrica) or 0.0)
    if sim == 0:
        return 0.0
    return round(((motor - sim) / sim) * 100.0, 3)


def _justificacion_por_categoria(escenario: dict, categoria: str) -> tuple[str, str]:
    sid = escenario["id"]
    if sid == "S01":
        return (
            "SIMARIS usa c_min=0.90. IEC 60909 4.3 establece c_min=0.95 en BT; Motor BT usa criterio normativo.",
            "MANTENER",
        )
    if sid == "S03":
        return (
            "SIMARIS usa GE generico 650kVA/400V. El proyecto real usa Rivera 404kVA/380V con alternador Stamford.",
            "DOCUMENTAR",
        )
    if sid == "S04":
        return (
            "SIMARIS reporta DeltaV a 20C. Motor BT incorpora DeltaV operacional a 60C, mas representativo en servicio.",
            "MANTENER",
        )
    if sid == "S06":
        return (
            "SIMARIS usa gi=0.75. En datacenter critico, gi real suele ser alto y Motor BT considera 0.85 operacional.",
            "MANTENER",
        )

    if categoria == "ERROR_MOTOR":
        return ("Resultado inconsistente con el escenario de referencia.", "CORREGIR")
    if categoria in {"SUPUESTO_CONSERVADOR", "EQUIPO_DISTINTO"}:
        return ("Diferencia explicable por supuestos/modelo no equivalentes.", "DOCUMENTAR")
    if categoria == "VARIABLE_IGNORADA":
        return ("Motor BT incorpora una variable que mejora realismo operacional.", "MANTENER")
    return ("Requiere analisis adicional para justificar la divergencia.", "ANALIZAR")


def categorizar(
    escenario: dict,
    resultado_motor: dict,
    divergencia_pct: float
) -> dict:
    """
    Construye salida trazable por escenario.
    """
    metrica = escenario.get("metrica")
    simaris_val = (escenario.get("resultado_simaris") or {}).get(metrica)
    categoria = escenario.get("categoria_esperada") or "PENDIENTE"

    # Regla simple de guarda: divergencia extrema inesperada.
    if categoria != "EQUIPO_DISTINTO" and abs(divergencia_pct) > 200:
        categoria = "PENDIENTE"

    justificacion, accion = _justificacion_por_categoria(escenario, categoria)
    nota_tecnica = (escenario.get("nota_tecnica") or "").strip()
    if nota_tecnica:
        justificacion = f"{justificacion} Nota tecnica: {nota_tecnica}"
    return {
        "id": escenario["id"],
        "descripcion": escenario["descripcion"],
        "resultado_motor": resultado_motor.get(metrica),
        "resultado_simaris": simaris_val,
        "divergencia_pct": divergencia_pct,
        "categoria": categoria,
        "justificacion": justificacion,
        "accion": accion,
        "variable_analisis": escenario.get("variable_analisis"),
        "nota_tecnica": nota_tecnica,
        "parametros_motor": escenario.get("parametros_motor", {}),
        "parametros_simaris": escenario.get("parametros_simaris", {}),
        "metrica": metrica,
        "detalle_motor": resultado_motor,
    }


def analizar_todos(escenarios: list) -> list[dict]:
    """
    Ejecuta comparacion completa para todos los escenarios.
    """
    resultados: list[dict] = []
    for e in escenarios:
        res_motor = calcular_resultado_motor(e)
        div = calcular_divergencia(
            resultado_motor=res_motor,
            resultado_simaris=e.get("resultado_simaris") or {},
            metrica=e.get("metrica"),
        )
        resultados.append(categorizar(e, res_motor, div))
    return resultados
