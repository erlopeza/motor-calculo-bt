"""P2 - Protocolo de prueba de motores."""

from __future__ import annotations


def protocolo_motores(resultados_motores: list) -> dict:
    """
    Genera protocolo de prueba para motores desde resultados de M8.
    """
    pruebas = []
    for r in (resultados_motores or []):
        nombre = str(r.get("nombre") or "MOTOR")
        i_nom = float(r.get("I_n") or 0.0)
        arr = r.get("arranque") or {}
        i_arr = float(arr.get("I_arranque") or 0.0)
        dv_arr = r.get("dv_arranque") or {}
        dv_pct = float(dv_arr.get("dv_pct") or 0.0)
        proteccion = r.get("proteccion") or {}

        i_arr_max = i_arr * 1.10
        i_arr_min = i_arr * 0.90
        i_nom_max = i_nom * 1.05
        t_arr_max_s = float(proteccion.get("t_arranque_max_s") or 10.0)

        pruebas.append(
            {
                "motor": nombre,
                "I_nominal_A": round(i_nom, 3),
                "I_nominal_max_A": round(i_nom_max, 3),
                "I_arranque_esperada_A": round(i_arr, 3),
                "I_arranque_min_A": round(i_arr_min, 3),
                "I_arranque_max_A": round(i_arr_max, 3),
                "dV_arranque_pct": round(dv_pct, 3),
                "dV_arranque_max_pct": 15.0,
                "t_arranque_max_s": round(t_arr_max_s, 3),
                "criterios": [
                    f"I_arranque_medida en [{round(i_arr_min, 2)}; {round(i_arr_max, 2)}] A",
                    "DeltaV_arranque_medido <= 15.0%",
                    f"Motor arranca en t <= {round(t_arr_max_s, 2)} s",
                    f"I_operacion_medida <= {round(i_nom_max, 2)} A",
                ],
                "resultado": "PENDIENTE",
            }
        )

    return {
        "protocolo": "P2 - Prueba de motores",
        "norma": "NCh 4-2003 12.28.8 / IEC 60034-1",
        "instrumento": "Pinza amperimetrica + analizador de red",
        "pruebas": pruebas,
        "total_motores": len(pruebas),
    }

