# ============================================================
# calculos.py
# Responsabilidad: fórmulas eléctricas de baja tensión
# Razón para cambiar: actualizar fórmulas o límites normativos
# ============================================================
# calculos.py — import actualizado
from conductores import (
    get_tabla_conductores, FACTOR_SISTEMA, TENSION_SISTEMA,
    LIMITE_DV, FACTORES_TEMP
)

# sugerir_conductor — firma actualizada
def sugerir_conductor(L_m, I_diseno, paralelos, sistema, temp_amb, norma="AWG"):
    tabla = get_tabla_conductores(norma)
    conductores_ordenados = sorted(tabla.items(), key=lambda x: x[1]["mm2"])
    # ... resto sin cambios
# ============================================================
# RESISTIVIDAD DEL COBRE
# ============================================================
RHO_CU = 0.0175   # Ω·mm²/m — cobre a 20°C (IEC 60228)


def calcular_potencia(I_diseno, cos_phi, sistema):
    """
    Calcula potencia activa en Watts.

    Parámetros:
        I_diseno : float — corriente de diseño en A
        cos_phi  : float — factor de potencia
        sistema  : str   — "1F", "2F" o "3F"

    Retorna:
        int — potencia en W
    """
    V = TENSION_SISTEMA[sistema]
    if sistema == "3F":
        return round(1.732 * V * I_diseno * cos_phi)
    return round(V * I_diseno * cos_phi)


def calcular_caida_tension(L_m, S_mm2, I_diseno, paralelos, sistema):
    """
    Calcula caída de tensión en un conductor.
    Fórmula: ΔV = (factor × ρ × L × I) / S_eq

    Parámetros:
        L_m      : float — longitud del tramo en metros
        S_mm2    : float — sección del conductor en mm²
        I_diseno : float — corriente de diseño en A
        paralelos: int   — número de conductores en paralelo
        sistema  : str   — "1F", "2F" o "3F"

    Retorna:
        (dV_V, dV_pct) — tupla (caída en V, caída en %)
    """
    factor = FACTOR_SISTEMA[sistema]   # 2 para 1F/2F, √3 para 3F
    S_eq   = S_mm2 * paralelos          # sección equivalente

    dV_V   = (factor * RHO_CU * L_m * I_diseno) / S_eq
    V_nom  = TENSION_SISTEMA[sistema]
    dV_pct = dV_V / V_nom * 100

    return round(dV_V, 3), round(dV_pct, 3)


def clasificar_caida(dV_pct):
    """
    Clasifica la caída de tensión según normativa SEC RIC N°10.

    Límites:
        ≤ 1.5% → ÓPTIMO
        ≤ 3.0% → ACEPTABLE
        ≤ 5.0% → PRECAUCIÓN
        > 5.0% → FALLA

    Retorna:
        str — clasificación
    """
    if dV_pct <= 1.5:
        return "ÓPTIMO"
    elif dV_pct <= LIMITE_DV:
        return "ACEPTABLE"
    elif dV_pct <= 5.0:
        return "PRECAUCIÓN"
    else:
        return "FALLA"


def capacidad_corregida(I_max, paralelos, temp_amb):
    """
    Calcula la capacidad de corriente corregida por temperatura
    y número de conductores en paralelo.

    Parámetros:
        I_max    : float — capacidad nominal del conductor en A
        paralelos: int   — número de conductores en paralelo
        temp_amb : float — temperatura ambiente en °C

    Retorna:
        float — capacidad corregida en A
    """
    factor_temp = FACTORES_TEMP.get(int(temp_amb), 1.0)
    return round(I_max * paralelos * factor_temp, 1)


def sugerir_conductor(L_m, I_diseno, paralelos, sistema, temp_amb, norma: str = "AWG"):
    """
    Busca el conductor mínimo que cumple ΔV ≤ LIMITE_DV
    y capacidad ≥ I_diseno.

    Parámetros:
        L_m      : float — longitud en metros
        I_diseno : float — corriente de diseño en A
        paralelos: int   — número de conductores en paralelo
        sistema  : str   — "1F", "2F" o "3F"
        temp_amb : float — temperatura ambiente en °C

    Retorna:
        (conductor, mm2, dV_pct) o (None, None, None) si no hay
    """
    tabla = get_tabla_conductores(norma)
    # Ordenar conductores de menor a mayor sección
    conductores_ordenados = sorted(
        tabla.items(),
        key=lambda x: x[1]["mm2"]
    )

    for nombre, datos in conductores_ordenados:
        S_mm2  = datos["mm2"]
        I_max  = datos["I_max"]
        I_cap  = capacidad_corregida(I_max, paralelos, temp_amb)

        if I_cap < I_diseno:
            continue

        _, dV_pct = calcular_caida_tension(
            L_m, S_mm2, I_diseno, paralelos, sistema
        )

        if dV_pct <= LIMITE_DV:
            return nombre, S_mm2, dV_pct

    return None, None, None
