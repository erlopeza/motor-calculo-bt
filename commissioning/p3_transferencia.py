"""P3 - Protocolos de transferencia ATS/STS."""

from __future__ import annotations


def _rango(valor: float, tol_pct: float) -> tuple[float, float]:
    v = float(valor)
    t = abs(float(tol_pct)) / 100.0
    return round(v * (1.0 - t), 3), round(v * (1.0 + t), 3)


def protocolo_transferencia(resultado_ats: dict) -> dict:
    """
    Protocolo de prueba para ATS/STS segun modo.
    """
    ats = resultado_ats or {}
    modo = str(ats.get("modo_transferencia") or "open").lower()
    tiempos = ats.get("tiempos") or {}
    t_total = float(tiempos.get("t_total_ms") or 0.0)
    t_det = float(ats.get("t_deteccion_ms") or 3000.0)
    t_arr = float(ats.get("t_arranque_ge_ms") or 10000.0)
    v_nom = float(ats.get("V_nominal_V") or ats.get("V_nominal") or 400.0)

    v_min, v_max = _rango(v_nom, 5.0)
    t_total_min, t_total_max = _rango(t_total, 10.0)

    pasos = [
        {"paso": 1, "accion": "Registrar V y f en RED", "criterio": f"V={v_nom}V +/-5%, f=50 +/-0.5Hz"},
        {"paso": 2, "accion": "Simular falla de red", "criterio": f"t_deteccion <= {round(t_det, 1)} ms"},
        {"paso": 3, "accion": "Verificar arranque GE", "criterio": f"t_arranque_GE <= {round(t_arr, 1)} ms"},
        {"paso": 4, "accion": "Verificar GE estabilizado", "criterio": f"V_GE [{v_min}-{v_max}] V, f 50 +/-0.5 Hz"},
        {"paso": 5, "accion": "Medir t_total transferencia", "criterio": f"t_total [{t_total_min}-{t_total_max}] ms"},
        {"paso": 6, "accion": "Restaurar red y verificar retransferencia", "criterio": "Sin disparos intempestivos"},
    ]

    if modo == "closed":
        pasos.insert(
            5,
            {
                "paso": 5.5,
                "accion": "Verificar sincronizacion entre fuentes",
                "criterio": "DeltaV<=5%, Deltaf<=0.2Hz, Deltafase<=5deg, t_paralelo<=200ms",
            },
        )
    elif modo == "sts":
        pasos = [
            {"paso": 1, "accion": "Simular falla de fuente 1", "criterio": "Conmutacion automatica"},
            {"paso": 2, "accion": "Medir t_conmutacion", "criterio": "t_conmutacion <= 4 ms"},
            {"paso": 3, "accion": "Verificar continuidad de carga", "criterio": "Sin interrupcion visible en UPS/carga"},
        ]

    return {
        "protocolo": "P3 - Prueba de transferencia ATS/STS",
        "norma": "IEC 60947-6-1 / RIC N8 3",
        "instrumento": "Analizador de red con registro temporal",
        "modo": modo,
        "equipo": ats.get("nombre") or "ATS/STS",
        "valores_esperados": {
            "t_total_ms_esperado": round(t_total, 3),
            "t_total_ms_tolerancia_pct": 10.0,
            "V_GE_esperado_V": round(v_nom, 3),
            "V_GE_rango_V": [v_min, v_max],
            "f_GE_esperado_Hz": 50.0,
            "f_GE_rango_Hz": [49.5, 50.5],
        },
        "pasos": pasos,
        "total_pasos": len(pasos),
    }


def protocolo_sts(resultado_sts: dict) -> dict:
    """
    Protocolo especifico para STS.
    """
    sts = resultado_sts or {}
    nombre = sts.get("nombre") or "STS"
    transferencia = sts.get("transferencia") or {}
    t_esp = float(transferencia.get("t_transferencia_ms") or sts.get("t_transferencia_ms") or 4.0)
    thd_lim = float(sts.get("thd_limite_pct") or 8.0)
    return {
        "protocolo": "P3-STS - Transferencia estatica",
        "norma": "IEC 62310-1",
        "instrumento": "Osciloscopio + analizador de calidad de energia",
        "equipo": nombre,
        "t_conmutacion_max_ms": 4.0,
        "t_conmutacion_esperada_ms": round(t_esp, 3),
        "thd_corriente_max_pct": round(thd_lim, 3),
        "pasos": [
            {"paso": 1, "accion": "Simular falla fuente 1", "criterio": "Transferencia inmediata"},
            {"paso": 2, "accion": "Medir t_conmutacion con osciloscopio", "criterio": "t <= 4 ms"},
            {"paso": 3, "accion": "Medir THD corriente", "criterio": f"THD <= {round(thd_lim, 2)}%"},
        ],
        "total_pasos": 3,
    }

