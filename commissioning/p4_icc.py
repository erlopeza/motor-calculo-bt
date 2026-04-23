"""P4 - Protocolo de verificacion de Icc en punto."""

from __future__ import annotations

import math


def _z_lazo_esperado(vn_v: float, icc_kA: float) -> float:
    icc_a = max(float(icc_kA) * 1000.0, 1e-9)
    return float(vn_v) / (math.sqrt(3.0) * icc_a)


def protocolo_icc(circuitos: list, resultados_icc: dict) -> dict:
    """
    Genera protocolo de verificacion Icc usando medicion de Z_lazo.
    """
    puntos = []
    vn_v = float((resultados_icc or {}).get("Vn_V") or 400.0)

    puntos_obligatorios = []
    if resultados_icc:
        if resultados_icc.get("trafo_sec_kA") is not None:
            puntos_obligatorios.append(("Bornes trafo sec", float(resultados_icc["trafo_sec_kA"])))
        if resultados_icc.get("bus_principal_kA") is not None:
            puntos_obligatorios.append(("Bus principal SWG", float(resultados_icc["bus_principal_kA"])))

    for nombre, icc in puntos_obligatorios:
        z_esp = _z_lazo_esperado(vn_v, icc)
        puntos.append(
            {
                "punto": nombre,
                "Icc_calculado_kA": round(icc, 3),
                "Icc_min_aceptable_kA": round(icc * 0.90, 3),
                "Icc_max_aceptable_kA": round(icc * 1.10, 3),
                "Z_lazo_esperado_ohm": round(z_esp, 6),
                "criterio": "Icc_medido en rango +/-10%",
                "resultado": "PENDIENTE",
            }
        )

    for c in (circuitos or []):
        nombre = str(c.get("nombre") or "SIN_NOMBRE")
        icc = float(c.get("icc_ka") or c.get("Icc_kA") or 0.0)
        if icc <= 0:
            continue
        z_esp = _z_lazo_esperado(vn_v, icc)
        puntos.append(
            {
                "punto": f"Entrada {nombre}",
                "Icc_calculado_kA": round(icc, 3),
                "Icc_min_aceptable_kA": round(icc * 0.90, 3),
                "Icc_max_aceptable_kA": round(icc * 1.10, 3),
                "Z_lazo_esperado_ohm": round(z_esp, 6),
                "criterio": "Icc_medido en rango +/-10%",
                "resultado": "PENDIENTE",
            }
        )

    if circuitos:
        mas_alejado = max(circuitos, key=lambda x: float(x.get("L_m") or 0.0))
        icc = float(mas_alejado.get("icc_ka") or mas_alejado.get("Icc_kA") or 0.0)
        if icc > 0:
            z_esp = _z_lazo_esperado(vn_v, icc)
            puntos.append(
                {
                    "punto": f"Punto mas alejado {mas_alejado.get('nombre')}",
                    "Icc_calculado_kA": round(icc, 3),
                    "Icc_min_aceptable_kA": round(icc * 0.90, 3),
                    "Icc_max_aceptable_kA": round(icc * 1.10, 3),
                    "Z_lazo_esperado_ohm": round(z_esp, 6),
                    "criterio": "Icc_medido en rango +/-10%",
                    "resultado": "PENDIENTE",
                }
            )

    return {
        "protocolo": "P4 - Verificacion Icc en punto",
        "norma": "IEC 60364-6 61.3 / RIC N19 4.3",
        "instrumento": "Analizador de lazo de tierra / impedancimetro",
        "metodo": "Icc_medido = Vn / (sqrt(3) * Z_lazo_medido)",
        "puntos": puntos,
        "total_puntos": len(puntos),
    }

