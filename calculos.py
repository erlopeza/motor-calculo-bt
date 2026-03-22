# ============================================================
# calculos.py
# Responsabilidad: fórmulas de cálculo eléctrico
# Razón para cambiar: corrección o ampliación de fórmulas
# ============================================================

# Importa los datos que necesita desde conductores.py
# "from módulo import nombre" trae solo lo que necesitamos
from conductores import (
    RHO_CU, LIMITE_DV,
    TENSION_SISTEMA, FACTOR_SISTEMA,
    CONDUCTORES, FACTORES_TEMP
)

def factor_temperatura(temp_amb):
    """
    Retorna el factor de corrección por temperatura.
    Si la temperatura no está en la tabla usa 1.00 (30°C base).
    """
    return FACTORES_TEMP.get(int(temp_amb), 1.00)

def capacidad_corregida(I_max, paralelos, temp_amb):
    """
    Capacidad real del conjunto de conductores.
    Aplica corrección por temperatura y cantidad de paralelos.
    Fórmula: I_cap = I_max × paralelos × factor_temperatura
    """
    factor = factor_temperatura(temp_amb)
    return round(I_max * paralelos * factor, 1)

def calcular_potencia(I_diseno, cos_phi, sistema):
    """
    Potencia activa según tipo de sistema.
    3F: P = √3 × V × I × cosφ
    1F/2F: P = V × I × cosφ
    """
    V = TENSION_SISTEMA.get(sistema, 380)
    if sistema == "3F":
        return round(1.732 * V * I_diseno * cos_phi)
    return round(V * I_diseno * cos_phi)

def calcular_caida_tension(L_m, S_mm2, I_diseno, paralelos, sistema):
    """
    Caída de tensión según tipo de sistema y conductores en paralelo.
    Sección equivalente = S_mm2 × paralelos
    Fórmula: ΔV = (factor × ρ × L × I) / S_eq
    Retorna: (dV_voltios, dV_porcentaje)
    """
    S_eq   = S_mm2 * paralelos
    factor = FACTOR_SISTEMA.get(sistema, 1.732)
    V_nom  = TENSION_SISTEMA.get(sistema, 380)
    dV_V   = (factor * RHO_CU * L_m * I_diseno) / S_eq
    dV_pct = (dV_V / V_nom) * 100
    return round(dV_V, 3), round(dV_pct, 3)

def clasificar_caida(dV_pct):
    """
    Clasifica el estado normativo según SEC RIC N°10 / IEC 60364.
    Retorna: string con el estado
    """
    if dV_pct <= 1.5:
        return "ÓPTIMO"
    elif dV_pct <= 3.0:
        return "ACEPTABLE"
    elif dV_pct <= 5.0:
        return "PRECAUCIÓN"
    else:
        return "FALLA"

def sugerir_conductor(L_m, I_diseno, paralelos, sistema, temp_amb):
    """
    Busca el conductor mínimo que cumple simultáneamente:
    1. ΔV ≤ límite normativo (3%)
    2. I_cap ≥ corriente de diseño
    Recorre la tabla de menor a mayor sección.
    Retorna: (nombre_conductor, mm2, dv_pct) o (None, None, None)
    """
    for nombre, datos in CONDUCTORES.items():
        _, dV_pct = calcular_caida_tension(
            L_m, datos["mm2"], I_diseno, paralelos, sistema
        )
        I_cap = capacidad_corregida(datos["I_max"], paralelos, temp_amb)

        if dV_pct <= LIMITE_DV and I_cap >= I_diseno:
            return nombre, datos["mm2"], round(dV_pct, 3)

    return None, None, None