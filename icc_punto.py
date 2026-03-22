# ============================================================
# icc_punto.py
# Responsabilidad: corriente de cortocircuito en cada punto
# Método: impedancias IEC 60909
# Razón para cambiar: actualización de fórmulas o normativa
# ============================================================

import math
from conductores import RHO_CU, CONDUCTORES, TENSION_SISTEMA

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