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

def calcular_icc_transformador(kVA, Vn_BT, Ucc_pct):
    """
    Calcula la corriente de cortocircuito en bornes BT.
    Método: IEC 60909 — impedancia del transformador.

    Fórmula:
        Zt = (Ucc% / 100) × (Vn² / Sn)
        Icc = Vn / (√3 × Zt)

    Parámetros:
        kVA     : potencia nominal del transformador en kVA
        Vn_BT   : tensión nominal BT en Voltios (ej: 380)
        Ucc_pct : impedancia de cortocircuito en % (dato de placa)

    Retorna:
        Icc_kA  : corriente de cortocircuito en kA
        Zt_ohm  : impedancia total en Ohmios
        datos   : diccionario con todos los valores calculados
    """
    # Convertir kVA a VA
    Sn_VA = kVA * 1000

    # Impedancia del transformador en Ohmios
    # Zt = (Ucc/100) × (Vn² / Sn)
    Zt_ohm = (Ucc_pct / 100) * (Vn_BT ** 2 / Sn_VA)

    # Corriente de cortocircuito trifásica en bornes BT
    # Icc = Vn / (√3 × Zt)
    Icc_A  = Vn_BT / (math.sqrt(3) * Zt_ohm)
    Icc_kA = round(Icc_A / 1000, 2)

    # Corriente nominal del transformador
    # In = Sn / (√3 × Vn)
    In_A = Sn_VA / (math.sqrt(3) * Vn_BT)
    In_A = round(In_A, 1)

    datos = {
        "kVA":     kVA,
        "Vn_BT":   Vn_BT,
        "Ucc_pct": Ucc_pct,
        "Sn_VA":   Sn_VA,
        "Zt_ohm":  round(Zt_ohm, 6),
        "In_A":    In_A,
        "Icc_kA":  Icc_kA,
        "Icc_A":   round(Icc_A, 1),
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
    # Buscar el kVA más cercano en la tabla
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
    lineas.append("=" * 55)
    lineas.append("  TRANSFORMADOR — DATOS Y CORTOCIRCUITO EN BORNES BT")
    lineas.append("=" * 55)
    lineas.append(f"  Modo de cálculo : {'A — datos de placa' if modo == 'A' else 'B — valores típicos IEC 60076'}")
    lineas.append(f"  Potencia nominal: {datos['kVA']} kVA")
    lineas.append(f"  Tensión BT      : {datos['Vn_BT']} V")
    lineas.append(f"  Ucc%            : {datos['Ucc_pct']} %")
    lineas.append(f"  Corriente nominal: {datos['In_A']} A")
    lineas.append(f"  Impedancia Zt   : {datos['Zt_ohm']} Ω")
    lineas.append("-" * 55)
    lineas.append(f"  Icc en bornes BT: {Icc_kA} kA  ({datos['Icc_A']} A)")
    lineas.append(f"  Nivel Icc       : {clasificar_icc(Icc_kA)}")
    lineas.append("=" * 55)
    return lineas