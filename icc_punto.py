# ============================================================
# icc_punto.py
# Responsabilidad: corriente de cortocircuito en cada punto
# Método: impedancias IEC 60909
# Razón para cambiar: actualización de fórmulas o normativa
# ============================================================

import math
from conductores import RHO_CU, CONDUCTORES, TENSION_SISTEMA

RHO_CU_OHM_MM2_M = RHO_CU  # resistividad cobre a 20°C (Ω·mm²/m) — IEC 60228
C_MIN_IEC60909 = 0.95      # factor tension minima BT — IEC 60909 §4.3.1

def calcular_zt_cable(L_m, S_mm2, paralelos=1, rho=RHO_CU):
    """
    Calcula la impedancia resistiva del cable en Ohmios.
    Fórmula: Zt_cable = (rho × L) / (S × paralelos)

    Parámetros:
        L_m       : longitud del cable en metros
        S_mm2     : sección del conductor en mm²
        paralelos : conductores en paralelo (default 1)
        rho       : resistividad del material (default cobre)

    Retorna:
        Zt_ohm : impedancia del cable en Ohmios
    """
    Zt_ohm = (rho * L_m) / (S_mm2 * paralelos)
    return round(Zt_ohm, 6)

def calcular_icc_punto(Zt_trafo_ohm, L_m, S_mm2, paralelos, sistema="3F"):
    """
    Calcula la corriente de cortocircuito en un punto del sistema.
    Suma la impedancia del transformador + impedancia del cable.

    Parámetros:
        Zt_trafo_ohm : impedancia del transformador en Ohmios
        L_m          : longitud del cable hasta el punto en metros
        S_mm2        : sección del conductor en mm²
        paralelos    : conductores en paralelo
        sistema      : "3F", "1F", "2F"

    Retorna:
        Icc_kA   : corriente de cortocircuito en el punto en kA
        Zt_total : impedancia total en Ohmios
        dIcc_pct : reducción respecto a la Icc del transformador en %
    """
    V_nom = TENSION_SISTEMA.get(sistema, 380)

    # Impedancia del cable hasta el punto
    Zt_cable = calcular_zt_cable(L_m, S_mm2, paralelos)

    # Impedancia total — transformador + cable
    Zt_total = Zt_trafo_ohm + Zt_cable

    # Icc en el punto
    if sistema == "3F":
        Icc_A = V_nom / (math.sqrt(3) * Zt_total)
    else:
        # Para 1F y 2F — circuito monofásico fase-neutro
        # Impedancia de retorno por neutro = misma sección
        Zt_retorno = Zt_cable   # neutro mismo calibre que fase
        Icc_A = V_nom / (Zt_total + Zt_retorno)

    Icc_kA = round(Icc_A / 1000, 2)

    return Icc_kA, round(Zt_total, 6), round(Zt_cable, 6)

def calcular_icc_fase_neutro(
    Vn_V: float,
    Zt_fuente_ohm: float,
    L_m: float,
    S_mm2: float,
    norma: str = "MM2",
    c_min: float = C_MIN_IEC60909
) -> dict:
    """
    Calcula Icc minima fase-neutro para verificacion de disparo.
    Metodo: IEC 60909 con c_min, bucle fase+neutro.
    """
    vn = float(Vn_V)
    u0 = vn / math.sqrt(3.0)
    z_fuente = float(Zt_fuente_ohm)
    z_fase = (RHO_CU_OHM_MM2_M * float(L_m)) / max(float(S_mm2), 1e-9)
    z_neutro = z_fase
    zs_total = z_fuente + z_fase + z_neutro
    icc_fn_a = (float(c_min) * u0) / max(zs_total, 1e-9)

    return {
        "Vn_V": vn,
        "U0_V": round(u0, 3),
        "Zt_fuente_ohm": round(z_fuente, 6),
        "Z_cable_fase_ohm": round(z_fase, 6),
        "Z_cable_neutro_ohm": round(z_neutro, 6),
        "Zs_total_ohm": round(zs_total, 6),
        "Icc_fn_A": round(icc_fn_a, 3),
        "Icc_fn_kA": round(icc_fn_a / 1000.0, 6),
        "c_min": float(c_min),
        "norma": str(norma).upper(),
        "norma_calculo": "IEC 60364-4-41 / IEC 60909",
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
