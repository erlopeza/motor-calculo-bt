# ============================================================
# coordinacion.py
# Responsabilidad: verificación de coordinación TCC
#                  selectividad y tiempos de disparo por cadena
# Normativa: IEC 60947-2 / IEC 60898-1 / IEC 60364-4-41
# Razón para cambiar: nuevos tipos de curva o criterios normativos
#
# LIMITACIÓN FASE 1:
#   La región térmica de curvas ETU (Ir×In < Icc < Isd×Ir×In)
#   no está modelada — datos propietarios Siemens.
#   En esa región la función retorna None con flag "VERIFICAR SIMARIS".
# ============================================================

import math

# ============================================================
# CONSTANTES DE CURVAS IEC 60898
# Constante k para la región térmica: t = k / (I/In)²
# Fuente: IEC 60898-1 Tabla 6 (valores aproximados)
# ============================================================

K_CURVA = {
    "B": 45,    # disparo magnético: 3–5×In
    "C": 80,    # disparo magnético: 5–10×In
    "D": 180,   # disparo magnético: 10–20×In
    "TM": 100,  # termomagnético IEC 60947-2 (aproximación)
}

# Umbrales de disparo magnético por curva (×In)
# (min, max) — se usa el promedio como punto de referencia
UMBRAL_MAGNETICO = {
    "B":  (3.0,  5.0),
    "C":  (5.0, 10.0),
    "D": (10.0, 20.0),
}

# Tiempo de disparo instantáneo (magnético o ETU instantáneo)
T_INSTANTANEO = 0.02   # segundos — IEC 60947-2

# ============================================================
# TIEMPOS MÁXIMOS IEC 60364-4-41
# Protección de personas contra choque eléctrico
# Sistema TN — BT 380/220V
# ============================================================
T_MAX_IEC_60364 = {
    "3F_380": 5.0,   # circuitos de distribución TN
    "1F_220": 0.4,   # circuitos terminales TN
    "TT":     0.2,   # cualquier circuito con diferencial
}


# ============================================================
# FUNCIÓN PRINCIPAL — TIEMPO DE DISPARO
# ============================================================

def calcular_tiempo_disparo(Icc_A, In_A, curva,
                             Ir_xIn=1.0, Isd_xIr=None,
                             tsd_s=None, Ii_xIn=None):
    """
    Calcula el tiempo de disparo de una protección para una Icc dada.

    Parámetros:
        Icc_A    : float — corriente de cortocircuito en A
        In_A     : float — corriente nominal del dispositivo en A
        curva    : str   — ETU600 / ETU320 / TM / C / D / B
        Ir_xIn   : float — ajuste de carga (múltiplo de In), default 1.0
        Isd_xIr  : float — umbral tiempo corto (múltiplo de Ir×In), ETU
        tsd_s    : float — tiempo corto intencional en s, ETU
        Ii_xIn   : float — umbral instantáneo (múltiplo de In)

    Retorna:
        dict con:
            t_s      : float | None — tiempo de disparo en segundos
            region   : str  — "instantaneo" / "tiempo_corto" / "termico"
                              / "no_dispara" / "verificar_simaris"
            dispara  : bool
            nota     : str  — descripción del resultado
    """
    Ir_A  = Ir_xIn * In_A
    curva = curva.upper().replace("-", "").replace(" ", "")

    # --- REGIÓN INSTANTÁNEA ---
    if Ii_xIn is not None:
        Ii_A = Ii_xIn * In_A
        if Icc_A >= Ii_A:
            return {
                "t_s":    T_INSTANTANEO,
                "region": "instantaneo",
                "dispara": True,
                "nota":   f"Icc={Icc_A:.0f}A ≥ Ii={Ii_A:.0f}A → instantáneo"
            }
    else:
        # Curvas C/D/B: umbral magnético estándar IEC 60898
        if curva in UMBRAL_MAGNETICO:
            _, Ii_max = UMBRAL_MAGNETICO[curva]
            Ii_A = Ii_max * In_A
            if Icc_A >= Ii_A:
                return {
                    "t_s":    T_INSTANTANEO,
                    "region": "instantaneo",
                    "dispara": True,
                    "nota":   f"Icc={Icc_A:.0f}A ≥ Ii_max={Ii_A:.0f}A → instantáneo"
                }

    # --- REGIÓN TIEMPO CORTO (ETU) ---
    if curva in ("ETU600", "ETU320"):
        if Isd_xIr is not None and tsd_s is not None:
            Isd_A = Isd_xIr * Ir_A
            if Icc_A >= Isd_A:
                return {
                    "t_s":    tsd_s,
                    "region": "tiempo_corto",
                    "dispara": True,
                    "nota":   f"Icc={Icc_A:.0f}A ≥ Isd={Isd_A:.0f}A → tsd={tsd_s}s"
                }
        # Región térmica ETU — no modelada
        if Icc_A >= Ir_A:
            return {
                "t_s":    None,
                "region": "verificar_simaris",
                "dispara": None,
                "nota":   (
                    f"Icc={Icc_A:.0f}A en región térmica ETU "
                    f"(Ir={Ir_A:.0f}A < Icc < Isd) — "
                    f"curva propietaria Siemens, usar SIMARIS"
                )
            }

    # --- REGIÓN TÉRMICA (C / D / B / TM) ---
    if curva in K_CURVA:
        if Icc_A >= Ir_A:
            k = K_CURVA[curva]
            ratio = Icc_A / In_A
            if ratio > 0:
                t = k / (ratio ** 2)
                return {
                    "t_s":    round(t, 3),
                    "region": "termico",
                    "dispara": True,
                    "nota":   f"Icc={Icc_A:.0f}A → t={t:.3f}s (curva {curva})"
                }

    # --- NO DISPARA ---
    return {
        "t_s":    None,
        "region": "no_dispara",
        "dispara": False,
        "nota":   f"Icc={Icc_A:.0f}A < Ir={Ir_A:.0f}A → no dispara"
    }


# ============================================================
# VERIFICACIÓN DE SELECTIVIDAD ENTRE DOS NIVELES
# ============================================================

def verificar_selectividad_par(resultado_inferior, resultado_superior):
    """
    Verifica la selectividad entre dos protecciones adyacentes.

    Condición: la protección inferior dispara antes que la superior.

    Parámetros:
        resultado_inferior : dict — salida de calcular_tiempo_disparo()
        resultado_superior : dict — salida de calcular_tiempo_disparo()

    Retorna:
        dict con:
            selectividad : str  — "TOTAL" / "PARCIAL" / "NINGUNA" / "INDETERMINADA"
            t_inf        : float | None
            t_sup        : float | None
            nota         : str
    """
    t_inf = resultado_inferior["t_s"]
    t_sup = resultado_superior["t_s"]
    r_inf = resultado_inferior["region"]
    r_sup = resultado_superior["region"]

    # Alguna región no modelada
    if r_inf == "verificar_simaris" or r_sup == "verificar_simaris":
        return {
            "selectividad": "INDETERMINADA",
            "t_inf": t_inf,
            "t_sup": t_sup,
            "nota":  "Región térmica ETU no modelada — verificar con SIMARIS"
        }

    # Inferior no dispara
    if not resultado_inferior["dispara"]:
        return {
            "selectividad": "NINGUNA",
            "t_inf": None,
            "t_sup": t_sup,
            "nota":  "Dispositivo inferior no dispara ante esta Icc"
        }

    # Superior no dispara — selectividad total
    if resultado_superior["dispara"] is False:
        return {
            "selectividad": "TOTAL",
            "t_inf": t_inf,
            "t_sup": None,
            "nota":  f"Inferior dispara en {t_inf}s, superior no alcanza → TOTAL"
        }

    # Ambos disparan — comparar tiempos
    if t_inf is None or t_sup is None:
        return {
            "selectividad": "INDETERMINADA",
            "t_inf": t_inf,
            "t_sup": t_sup,
            "nota":  "No se puede determinar — tiempo indeterminado en algún nivel"
        }

    if t_inf < t_sup:
        margen = round(t_sup - t_inf, 3)
        return {
            "selectividad": "TOTAL",
            "t_inf": t_inf,
            "t_sup": t_sup,
            "nota":  f"t_inf={t_inf}s < t_sup={t_sup}s (margen {margen}s) → TOTAL"
        }
    elif abs(t_inf - t_sup) < 0.01:
        return {
            "selectividad": "PARCIAL",
            "t_inf": t_inf,
            "t_sup": t_sup,
            "nota":  f"t_inf={t_inf}s ≈ t_sup={t_sup}s → PARCIAL"
        }
    else:
        return {
            "selectividad": "NINGUNA",
            "t_inf": t_inf,
            "t_sup": t_sup,
            "nota":  f"t_inf={t_inf}s > t_sup={t_sup}s → NO SELECTIVA"
        }


# ============================================================
# VERIFICACIÓN IEC 60364-4-41
# ============================================================

def verificar_iec60364(t_disparo_s, sistema="3F_380"):
    """
    Verifica si el tiempo de disparo cumple IEC 60364-4-41.

    Parámetros:
        t_disparo_s : float | None — tiempo de disparo en s
        sistema     : str — "3F_380" / "1F_220" / "TT"

    Retorna:
        dict con cumple (bool), t_max, estado, nota
    """
    t_max = T_MAX_IEC_60364.get(sistema, 5.0)

    if t_disparo_s is None:
        return {
            "cumple": None,
            "t_max":  t_max,
            "estado": "INDETERMINADO",
            "nota":   "Tiempo no calculado — verificar con SIMARIS"
        }

    cumple = t_disparo_s <= t_max
    return {
        "cumple": cumple,
        "t_max":  t_max,
        "estado": "OK" if cumple else "FALLA",
        "nota":   (
            f"t={t_disparo_s}s ≤ t_max={t_max}s → OK"
            if cumple else
            f"t={t_disparo_s}s > t_max={t_max}s → NO CUMPLE IEC 60364-4-41"
        )
    }


# ============================================================
# VERIFICACIÓN DE CADENA COMPLETA
# ============================================================

def verificar_cadena(dispositivos, Icc_A, sistema="3F_380"):
    """
    Verifica la selectividad de una cadena jerárquica completa.

    Parámetros:
        dispositivos : lista de dicts ordenada de mayor a menor nivel
                       (índice 0 = cabecera, índice -1 = circuito final)
                       Cada dict requiere:
                           nombre, In_A, curva, Ir_xIn,
                           Isd_xIr (opt), tsd_s (opt), Ii_xIn (opt)
        Icc_A        : float — corriente de falla en A (en el punto más alejado)
        sistema      : str   — para verificación IEC 60364-4-41

    Retorna:
        dict con:
            resultados_disparo : lista por dispositivo
            selectividad_pares : lista por par adyacente
            iec60364_final     : verificación del dispositivo final
            selectividad_global: str — resultado global de la cadena
    """
    if not dispositivos:
        return {"error": "Cadena vacía"}

    # Calcular tiempo de disparo para cada dispositivo
    resultados_disparo = []
    for d in dispositivos:
        res = calcular_tiempo_disparo(
            Icc_A       = Icc_A,
            In_A        = d["In_A"],
            curva       = d["curva"],
            Ir_xIn      = d.get("Ir_xIn",  1.0),
            Isd_xIr     = d.get("Isd_xIr", None),
            tsd_s       = d.get("tsd_s",   None),
            Ii_xIn      = d.get("Ii_xIn",  None),
        )
        resultados_disparo.append({
            "nombre": d["nombre"],
            "nivel":  d.get("nivel", "?"),
            **res
        })

    # Verificar selectividad entre pares adyacentes
    # Orden: cabecera (0) → terminal (N)
    # Par: superior=i, inferior=i+1
    selectividad_pares = []
    for i in range(len(resultados_disparo) - 1):
        sup = resultados_disparo[i]
        inf = resultados_disparo[i + 1]
        sel = verificar_selectividad_par(inf, sup)
        selectividad_pares.append({
            "superior": sup["nombre"],
            "inferior": inf["nombre"],
            **sel
        })

    # Verificación IEC 60364-4-41 del dispositivo final (más cercano a la falla)
    final = resultados_disparo[-1]
    iec = verificar_iec60364(final["t_s"], sistema)

    # Resultado global
    estados = [p["selectividad"] for p in selectividad_pares]
    if all(s == "TOTAL" for s in estados):
        global_sel = "TOTAL"
    elif "NINGUNA" in estados:
        global_sel = "NINGUNA"
    elif "INDETERMINADA" in estados:
        global_sel = "INDETERMINADA"
    else:
        global_sel = "PARCIAL"

    return {
        "Icc_A":                Icc_A,
        "resultados_disparo":   resultados_disparo,
        "selectividad_pares":   selectividad_pares,
        "iec60364_final":       iec,
        "selectividad_global":  global_sel,
    }


# ============================================================
# REPORTE
# ============================================================

def reporte_coordinacion(resultado_cadena, nombre_cadena="Cadena"):
    """
    Genera líneas de reporte de coordinación TCC.
    Retorna lista de strings.
    """
    lineas = []
    r = resultado_cadena

    if "error" in r:
        lineas.append(f"  ERROR: {r['error']}")
        return lineas

    lineas.append("=" * 60)
    lineas.append(f"  COORDINACIÓN TCC — {nombre_cadena.upper()}")
    lineas.append(f"  Normativa: IEC 60947-2 / IEC 60898 / IEC 60364-4-41")
    lineas.append(f"  Icc en punto de falla: {r['Icc_A']} A")
    lineas.append("=" * 60)

    # Tiempos de disparo por dispositivo
    lineas.append("")
    lineas.append("  TIEMPOS DE DISPARO")
    lineas.append("-" * 60)
    lineas.append(
        f"  {'Dispositivo':<25} {'Nivel':>5} {'t_disparo':>12} {'Región':<20}"
    )
    lineas.append("-" * 60)

    for d in r["resultados_disparo"]:
        t_str = f"{d['t_s']:.3f} s" if d["t_s"] is not None else "—"
        lineas.append(
            f"  {d['nombre']:<25} {str(d['nivel']):>5} "
            f"{t_str:>12} {d['region']:<20}"
        )
        if d["region"] == "verificar_simaris":
            lineas.append(f"    ⚠  {d['nota']}")

    # Selectividad por par
    lineas.append("")
    lineas.append("  SELECTIVIDAD POR PAR")
    lineas.append("-" * 60)
    for p in r["selectividad_pares"]:
        icono = ("✓" if p["selectividad"] == "TOTAL" else
                 "~" if p["selectividad"] == "PARCIAL" else
                 "⚠" if p["selectividad"] == "INDETERMINADA" else "✗")
        lineas.append(
            f"  {icono} {p['inferior']:<20} vs {p['superior']:<20} "
            f"→ {p['selectividad']}"
        )
        lineas.append(f"    {p['nota']}")

    # IEC 60364-4-41
    iec = r["iec60364_final"]
    lineas.append("")
    lineas.append("  IEC 60364-4-41 — PROTECCIÓN DE PERSONAS")
    lineas.append("-" * 60)
    icono = "✓" if iec["cumple"] else ("⚠" if iec["cumple"] is None else "✗")
    lineas.append(f"  {icono} {iec['nota']}")

    # Resultado global
    lineas.append("")
    lineas.append("=" * 60)
    lineas.append(
        f"  SELECTIVIDAD GLOBAL : {r['selectividad_global']}"
    )
    lineas.append("=" * 60)

    return lineas