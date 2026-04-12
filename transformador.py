# ============================================================
# transformador.py
# Responsabilidad: cálculo de transformador e Icc en bornes BT
# Razón para cambiar: actualización de fórmulas o tabla típica
# Normativa: IEC 60909 / IEC 60076
# ============================================================

import math
from conductores import TENSION_SISTEMA

# --- TABLA DE VALORES TÍPICOS POR POTENCIA ---
# Fuente: IEC 60076 — transformadores de distribución
# Ucc% típico según rango de potencia
# Icc calculada a 380V trifásico
# Usar cuando no se tienen datos de placa del transformador

TABLA_TIPICA = {
    #  kVA : {"Ucc_pct": %, "Icc_kA": kA a 380V}
    100:  {"Ucc_pct": 4.0, "Icc_kA": 3.8},
    160:  {"Ucc_pct": 4.0, "Icc_kA": 6.1},
    250:  {"Ucc_pct": 4.0, "Icc_kA": 9.5},
    400:  {"Ucc_pct": 4.0, "Icc_kA": 15.2},
    630:  {"Ucc_pct": 4.0, "Icc_kA": 24.0},
    1000: {"Ucc_pct": 5.0, "Icc_kA": 30.4},
    1600: {"Ucc_pct": 6.0, "Icc_kA": 40.5},
    2000: {"Ucc_pct": 6.0, "Icc_kA": 50.6},
}

# ============================================================
# FACTORES IEC 60909 §4.3.1
# c_max : factor de tensión para Icc máxima (peor caso para
#         selección de protecciones y poder de corte)
# c_min : factor de tensión para Icc mínima (peor caso para
#         verificación de disparo de protecciones)
# ============================================================
C_MAX = 1.10   # IEC 60909 §4.3.1 — BT hasta 1000V
C_MIN = 0.95   # IEC 60909 §4.3.1 — BT hasta 1000V

# Tolerancia típica de impedancia de cortocircuito
# Fuente: IEC 60076-1 §11.4
# Positivo → %Z más alto → Icc más baja (conservador para Icc_min)
# Negativo → %Z más bajo → Icc más alta (conservador para Icc_max)
TOLERANCIA_UCC_PCT_DEFAULT = 7.5   # ±7.5% del valor nominal


def calcular_icc_transformador(kVA, Vn_BT, Ucc_pct,
                                tolerancia_ucc_pct=TOLERANCIA_UCC_PCT_DEFAULT):
    """
    Calcula las corrientes de cortocircuito en bornes BT.

    Implementa IEC 60909 con factores de tensión c_max/c_min
    y tolerancia de impedancia según IEC 60076-1.

    Fórmulas:
        Zt   = (Ucc% / 100) × (Vn² / Sn)
        Icc_nominal = Vn        / (√3 × Zt)         [base, sin c]
        Icc_max     = c_max × Vn / (√3 × Zt_min)    [peor caso protecciones]
        Icc_min     = c_min × Vn / (√3 × Zt_max)    [peor caso disparo]

    Donde:
        Zt_min = Zt × (1 - tolerancia/100)  → Icc_max
        Zt_max = Zt × (1 + tolerancia/100)  → Icc_min

    Parámetros:
        kVA               : potencia nominal del transformador en kVA
        Vn_BT             : tensión nominal BT en Voltios (ej: 380)
        Ucc_pct           : impedancia de cortocircuito en % (dato de placa)
        tolerancia_ucc_pct: tolerancia de %Z en % (default 7.5%)
                            Pasar 0 para ignorar tolerancia.

    Retorna:
        Icc_kA  : corriente de cortocircuito nominal en kA
                  (sin c_max, base para cálculos de Icc por punto)
        Zt_ohm  : impedancia nominal en Ohmios
        datos   : diccionario con todos los valores calculados
    """
    Sn_VA = kVA * 1000

    # Impedancia nominal
    Zt_ohm = (Ucc_pct / 100) * (Vn_BT ** 2 / Sn_VA)

    # Impedancias con tolerancia
    tol   = tolerancia_ucc_pct / 100
    Zt_min = Zt_ohm * (1 - tol)   # %Z mínimo → Icc máxima
    Zt_max = Zt_ohm * (1 + tol)   # %Z máximo → Icc mínima

    # Corriente nominal (sin c) — base para M2 Icc por punto
    Icc_A     = Vn_BT / (math.sqrt(3) * Zt_ohm)
    Icc_kA    = round(Icc_A / 1000, 2)

    # Icc máxima: c_max × Vn / (√3 × Zt_min) — IEC 60909
    # Usar para: selección poder de corte de protecciones
    Icc_max_A  = (C_MAX * Vn_BT) / (math.sqrt(3) * Zt_min)
    Icc_max_kA = round(Icc_max_A / 1000, 2)

    # Icc mínima: c_min × Vn / (√3 × Zt_max) — IEC 60909
    # Usar para: verificación de disparo (¿la protección alcanza a disparar?)
    Icc_min_A  = (C_MIN * Vn_BT) / (math.sqrt(3) * Zt_max)
    Icc_min_kA = round(Icc_min_A / 1000, 2)

    # Corriente nominal del transformador
    In_A = round(Sn_VA / (math.sqrt(3) * Vn_BT), 1)

    datos = {
        "kVA":              kVA,
        "Vn_BT":            Vn_BT,
        "Ucc_pct":          Ucc_pct,
        "tolerancia_pct":   tolerancia_ucc_pct,
        "Sn_VA":            Sn_VA,
        "Zt_ohm":           round(Zt_ohm, 6),
        "Zt_min_ohm":       round(Zt_min, 6),
        "Zt_max_ohm":       round(Zt_max, 6),
        "In_A":             In_A,
        # Nominal (sin c) — para cálculo de Icc por punto en M2
        "Icc_A":            round(Icc_A, 1),
        "Icc_kA":           Icc_kA,
        # Máxima con c_max — para poder de corte
        "Icc_max_A":        round(Icc_max_A, 1),
        "Icc_max_kA":       Icc_max_kA,
        # Mínima con c_min — para verificación disparo
        "Icc_min_A":        round(Icc_min_A, 1),
        "Icc_min_kA":       Icc_min_kA,
        "c_max":            C_MAX,
        "c_min":            C_MIN,
    }

    return Icc_kA, Zt_ohm, datos


def icc_desde_tabla(kVA):
    """
    Modo B — sin datos de placa.
    Busca el valor más cercano en la tabla típica IEC 60076.
    Útil cuando no se tienen datos exactos del transformador.

    Retorna:
        Icc_kA   : corriente típica en kA
        Ucc_pct  : impedancia típica usada
        kVA_ref  : potencia de referencia usada
    """
    kVA_disponibles = list(TABLA_TIPICA.keys())
    kVA_ref = min(kVA_disponibles, key=lambda x: abs(x - kVA))

    datos_tipicos = TABLA_TIPICA[kVA_ref]
    Icc_kA  = datos_tipicos["Icc_kA"]
    Ucc_pct = datos_tipicos["Ucc_pct"]

    return Icc_kA, Ucc_pct, kVA_ref


def clasificar_icc(Icc_kA):
    """
    Clasifica el nivel de cortocircuito para orientar
    la selección del poder de corte de las protecciones.
    """
    if Icc_kA <= 6:
        return "BAJO — verificar protecciones 6kA"
    elif Icc_kA <= 10:
        return "MEDIO — protecciones 10kA mínimo"
    elif Icc_kA <= 25:
        return "ALTO — protecciones 25kA mínimo"
    elif Icc_kA <= 50:
        return "MUY ALTO — protecciones 50kA mínimo"
    else:
        return "EXTREMO — consultar fabricante"


def reporte_transformador(datos, modo, Icc_kA):
    """
    Genera líneas de reporte del transformador.
    Retorna lista de strings lista para mostrar o guardar.
    """
    lineas = []
    lineas.append("=" * 57)
    lineas.append("  TRANSFORMADOR — DATOS Y CORTOCIRCUITO EN BORNES BT")
    lineas.append("=" * 57)
    lineas.append(f"  Modo de cálculo : {'A — datos de placa' if modo == 'A' else 'B — valores típicos IEC 60076'}")
    lineas.append(f"  Potencia nominal: {datos['kVA']} kVA")
    lineas.append(f"  Tensión BT      : {datos['Vn_BT']} V")
    lineas.append(f"  Ucc%            : {datos['Ucc_pct']} %  (tolerancia ±{datos.get('tolerancia_pct', 0)}%)")
    lineas.append(f"  Corriente nominal: {datos['In_A']} A")
    lineas.append(f"  Impedancia Zt   : {datos['Zt_ohm']} Ω")
    lineas.append("-" * 57)
    lineas.append(f"  Icc nominal BT  : {Icc_kA} kA  ({datos['Icc_A']} A)")

    if "Icc_max_kA" in datos:
        lineas.append(f"  Icc máxima      : {datos['Icc_max_kA']} kA  "
                      f"(c={datos['c_max']} · %Z mín)  "
                      f"→ selección poder de corte")
        lineas.append(f"  Icc mínima      : {datos['Icc_min_kA']} kA  "
                      f"(c={datos['c_min']} · %Z máx)  "
                      f"→ verificación disparo")

    lineas.append(f"  Nivel Icc       : {clasificar_icc(Icc_kA)}")
    lineas.append(f"  Normativa       : IEC 60909 §4.3.1 / IEC 60076-1 §11.4")
    lineas.append("=" * 57)
    return lineas