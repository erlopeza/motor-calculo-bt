"""P1 - Protocolo de continuidad de conductores."""

from __future__ import annotations

RHO_CU_20 = 0.01724
ALPHA_CU = 0.00393


def _factor_temperatura(temp_c: float) -> float:
    return 1.0 + ALPHA_CU * (float(temp_c) - 20.0)


def protocolo_continuidad(circuitos: list) -> dict:
    """
    Genera mediciones de continuidad esperadas por circuito.
    """
    mediciones = []
    for c in (circuitos or []):
        nombre = str(c.get("nombre") or c.get("circuito") or "SIN_NOMBRE")
        longitud = float(c.get("L_m") or c.get("longitud_m") or 0.0)
        s_mm2 = float(c.get("S_mm2") or c.get("seccion_mm2") or 1.0)
        s_pe = float(c.get("S_pe_mm2") or c.get("seccion_pe_mm2") or s_mm2)
        temp_c = float(c.get("temp_C") or c.get("temperatura_C") or 20.0)

        ft = _factor_temperatura(temp_c)
        r_max = (RHO_CU_20 * longitud / max(s_mm2, 1e-9)) * ft
        r_tierra_max = (RHO_CU_20 * longitud / max(s_pe, 1e-9)) * ft

        conductor = c.get("conductor")
        if not conductor:
            conductor = f"3x{round(s_mm2, 2)}mm2 CU"

        mediciones.append(
            {
                "circuito": nombre,
                "conductor": str(conductor),
                "longitud_m": round(longitud, 3),
                "R_max_ohm": round(r_max, 6),
                "R_tierra_max_ohm": round(r_tierra_max, 6),
                "criterio": f"R_medida <= {round(r_max, 6)} ohm",
                "resultado": "PENDIENTE",
            }
        )

    return {
        "protocolo": "P1 - Continuidad de conductores",
        "norma": "RIC N19 4.2 / IEC 60364-6",
        "instrumento": "Telurometro o multimetro de precision",
        "mediciones": mediciones,
        "total_circuitos": len(mediciones),
    }

