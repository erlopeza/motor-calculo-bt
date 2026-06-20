# ============================================================
# icc_punto.py
# Responsabilidad: corriente de cortocircuito en cada punto
# Método: impedancias IEC 60909
# Razón para cambiar: actualización de fórmulas o normativa
# ============================================================

import math
from conductores import RHO_CU, CONDUCTORES, TENSION_SISTEMA, get_reactancia_cable_ohm_km

RHO_CU_OHM_MM2_M = RHO_CU  # resistividad cobre a 20°C (Ω·mm²/m) — IEC 60228
C_MIN_IEC60909 = 0.95      # factor tension minima BT — IEC 60909 §4.3.1


def calcular_zt_cable(L_m, S_mm2, paralelos=1, rho=RHO_CU) -> float:
    """Resistencia del cable en Ω (componente real, sin reactancia).

    Mantiene firma y retorno originales para retrocompatibilidad con GUI y
    reportes que solo necesitan R. Para Icc usar calcular_zt_cable_complejo.
    """
    return round((rho * L_m) / (S_mm2 * paralelos), 6)


def calcular_zt_cable_complejo(L_m, S_mm2, paralelos=1, rho=RHO_CU) -> complex:
    """Impedancia compleja del cable Z = R + jX en Ω (IEC 60909-2 §B).

    R: resistencia (rho × L / (S × paralelos)).
    X: reactancia inductiva interpolada en tabla IEC 60909-2 Tabla B.1.

    Retorna complex para uso en calculos de Icc; usar abs() para magnitud.
    """
    r = (rho * L_m) / (S_mm2 * paralelos)
    x = get_reactancia_cable_ohm_km(S_mm2) * L_m / 1000.0 / paralelos
    return complex(r, x)

def calcular_icc_punto(Zt_trafo_ohm, L_m, S_mm2, paralelos, sistema="3F"):
    """Corriente de cortocircuito en un punto usando impedancia compleja R+jX.

    Modelo: Z_cable = R + jX (IEC 60909-2 Tabla B.1); Z_trafo = real.
    Icc = c_max × Vn / (√3 × |Z_total|) para 3F.
    Para 1F/2F: Icc = Vn / |Z_total + Z_retorno|.

    Retorna:
        Icc_kA   : float — corriente de cortocircuito en kA
        Zt_total : float — |Z_total| en Ω (magnitud, retrocompatible)
        Zt_cable : float — |Z_cable| en Ω (magnitud, retrocompatible)
    """
    V_nom = TENSION_SISTEMA.get(sistema, 380)

    Z_cable = calcular_zt_cable_complejo(L_m, S_mm2, paralelos)
    # trafo modelado como impedancia puramente resistiva (fase posterior: añadir X_trafo)
    Z_trafo = complex(float(Zt_trafo_ohm), 0.0)
    Z_total = Z_trafo + Z_cable

    if sistema == "3F":
        Icc_A = V_nom / (math.sqrt(3) * abs(Z_total))
    else:
        Z_retorno = Z_cable  # neutro mismo calibre que fase
        Icc_A = V_nom / abs(Z_total + Z_retorno)

    return round(Icc_A / 1000, 2), round(abs(Z_total), 6), round(abs(Z_cable), 6)

def calcular_icc_fase_neutro(
    Vn_V: float,
    Zt_fuente_ohm: float,
    L_m: float,
    S_mm2: float,
    norma: str = "MM2",
    c_min: float = C_MIN_IEC60909
) -> dict:
    """Icc mínima fase-neutro con impedancia compleja del cable (IEC 60364-4-41).

    Modelo: bucle fase + neutro (mismo conductor), Z = R + jX por tramo.
    Z_fuente tratada como puramente resistiva; mejora futura: añadir X_fuente.
    """
    vn = float(Vn_V)
    u0 = vn / math.sqrt(3.0)
    s = max(float(S_mm2), 1e-9)
    l = float(L_m)

    Z_fase = calcular_zt_cable_complejo(l, s, paralelos=1)
    Z_neutro = Z_fase  # mismo calibre
    x_cable = Z_fase.imag
    Z_fuente = complex(float(Zt_fuente_ohm), 0.0)
    Zs_compleja = Z_fuente + Z_fase + Z_neutro
    zs_mag = abs(Zs_compleja)

    icc_fn_a = (float(c_min) * u0) / max(zs_mag, 1e-9)
    z_fase_r = Z_fase.real  # componente resistiva (retrocompat)

    return {
        "Vn_V": vn,
        "U0_V": round(u0, 3),
        "Zt_fuente_ohm": round(float(Zt_fuente_ohm), 6),
        "Z_cable_fase_ohm": round(z_fase_r, 6),
        "Z_cable_neutro_ohm": round(z_fase_r, 6),
        "X_cable_ohm": round(x_cable, 6),
        "Zs_total_ohm": round(zs_mag, 6),
        "Icc_fn_A": round(icc_fn_a, 3),
        "Icc_fn_kA": round(icc_fn_a / 1000.0, 6),
        "c_min": float(c_min),
        "norma": str(norma).upper(),
        "norma_calculo": "IEC 60364-4-41 / IEC 60909 (modelo R+jX)",
    }

def verificar_disparo_proteccion(
    Icc_fn_A: float,
    Ia_A: float,
    U0_V: float,
    Zs_total_ohm: float
) -> dict:
    """
    Verifica condicion IEC 60364-4-41 §411.4.4: Zs x Ia <= U0.
    """
    icc = float(Icc_fn_A)
    ia = float(Ia_A)
    u0 = float(U0_V)
    zs = float(Zs_total_ohm)
    zs_x_ia = zs * ia

    return {
        "Icc_fn_A": round(icc, 3),
        "Ia_A": round(ia, 3),
        "U0_V": round(u0, 3),
        "Zs_total_ohm": round(zs, 6),
        "Zs_x_Ia": round(zs_x_ia, 3),
        "cumple_iec": zs_x_ia <= u0,
        "margen_A": round(icc - ia, 3),
        "dispara": icc >= ia,
        "norma": "IEC 60364-4-41 §411.4.4",
    }

def reduccion_icc(Icc_trafo_kA, Icc_punto_kA):
    """
    Calcula la reducción porcentual de Icc
    desde el transformador hasta el punto.
    Útil para evaluar si la protección puede disparar.
    """
    if Icc_trafo_kA == 0:
        return 0.0
    reduccion = (1 - Icc_punto_kA / Icc_trafo_kA) * 100
    return round(reduccion, 1)

def clasificar_icc_punto(Icc_kA):
    """
    Clasifica el nivel de Icc en el punto.
    Mismo criterio que en bornes del transformador.
    """
    if Icc_kA <= 1:
        return "MUY BAJO — verificar disparo de protección"
    elif Icc_kA <= 6:
        return "BAJO"
    elif Icc_kA <= 10:
        return "MEDIO"
    elif Icc_kA <= 25:
        return "ALTO"
    elif Icc_kA <= 50:
        return "MUY ALTO"
    else:
        return "EXTREMO"

def calcular_icc_con_aporte_motores(
    Icc_red_kA: float,
    aportes_motores_A: list,
) -> tuple:
    """Icc total = aporte de la red + aporte de motores (IEC 60909 §3.8).

    La suma es escalar (peor caso — aportes en fase).
    Aportes negativos se ignoran (no reducen Icc).

    Retorna:
        Icc_total_kA (float): corriente total en kA
        desglose (dict): Icc_red_kA, Icc_motores_kA, Icc_total_kA, n_motores
    """
    icc_red = float(Icc_red_kA)
    aportes_validos = [max(float(a), 0.0) for a in aportes_motores_A]
    icc_motores_kA = sum(aportes_validos) / 1000.0
    icc_total = icc_red + icc_motores_kA
    desglose = {
        "Icc_red_kA": round(icc_red, 4),
        "Icc_motores_kA": round(icc_motores_kA, 4),
        "Icc_total_kA": round(icc_total, 4),
        "n_motores": len(aportes_validos),
        "norma": "IEC 60909:2016 §3.8",
    }
    return round(icc_total, 4), desglose


def calcular_icc_todos_circuitos(Zt_trafo_ohm, circuitos):
    """
    Calcula la Icc en cada circuito del sistema.
    Agrega los resultados de Icc al diccionario de cada circuito.
    Retorna lista de circuitos con Icc calculada.
    """
    resultados = []

    for c in circuitos:
        Icc_kA, Zt_total, Zt_cable = calcular_icc_punto(
            Zt_trafo_ohm,
            c["L_m"],
            c["S_mm2"],
            c["paralelos"],
            c["sistema"]
        )

        # Agregar datos de Icc al circuito
        c_con_icc = dict(c)   # copia del diccionario original
        c_con_icc["Icc_kA"]   = Icc_kA
        c_con_icc["Zt_cable"]  = Zt_cable
        c_con_icc["Zt_total"]  = Zt_total
        c_con_icc["nivel_icc"] = clasificar_icc_punto(Icc_kA)

        resultados.append(c_con_icc)

    return resultados
