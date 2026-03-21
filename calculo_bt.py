# ============================================================
# Motor de Cálculo BT — Bloque 7: Sistema completo
# Soporte: 1F / 2F / 3F — Paralelos — Corrección temperatura
# Normativa: SEC RIC N°10 / NEC / IEC 60364
# ============================================================

from datetime import datetime
import openpyxl

# --- CONSTANTES ---
RHO_CU    = 0.0175   # resistividad cobre Ω·mm²/m
RHO_AL    = 0.028    # resistividad aluminio Ω·mm²/m
LIMITE_DV = 3.0      # límite normativo caída de tensión %

# --- TENSIONES NOMINALES POR SISTEMA ---
# Define la tensión de referencia para calcular % de caída
TENSION_SISTEMA = {
    "3F": 380,   # trifásico — tensión de línea
    "1F": 220,   # monofásico — tensión fase-neutro
    "2F": 220,   # bifásico — tensión fase-neutro
}

# --- FACTOR DE CAÍDA POR SISTEMA ---
# 3F usa √3 porque la corriente circula por 3 fases
# 1F y 2F usan 2 porque la corriente va y vuelve (ida + neutro)
FACTOR_SISTEMA = {
    "3F": 1.732,
    "1F": 2.0,
    "2F": 2.0,
}

# --- TABLA DE CONDUCTORES AWG/MCM ---
# I_max basado en NEC Table 310.15 — XLPE/PVC 90°C en conduit
# Temperatura de referencia: 30°C
CONDUCTORES = {
    "14AWG":  {"mm2": 2.08,  "I_max": 20},
    "12AWG":  {"mm2": 3.31,  "I_max": 25},
    "10AWG":  {"mm2": 5.26,  "I_max": 35},
    "8AWG":   {"mm2": 8.37,  "I_max": 50},
    "6AWG":   {"mm2": 13.3,  "I_max": 65},
    "4AWG":   {"mm2": 21.1,  "I_max": 85},
    "2AWG":   {"mm2": 33.6,  "I_max": 115},
    "1/0AWG": {"mm2": 53.5,  "I_max": 150},
    "2/0AWG": {"mm2": 67.4,  "I_max": 175},
    "4/0AWG": {"mm2": 107.0, "I_max": 230},
    "350MCM": {"mm2": 177.0, "I_max": 310},
    "400MCM": {"mm2": 203.0, "I_max": 335},
    "500MCM": {"mm2": 253.0, "I_max": 380},
}

# --- FACTORES DE CORRECCIÓN POR TEMPERATURA ---
# NEC Table 310.15(B)(1) — conductor XLPE 90°C
# A mayor temperatura ambiente, menor capacidad de corriente
FACTORES_TEMP = {
    25: 1.04,   # más frío que referencia → más capacidad
    30: 1.00,   # temperatura de referencia
    35: 0.96,   # reducción 4%
    40: 0.91,   # reducción 9%
    45: 0.87,   # reducción 13%
    50: 0.82,   # reducción 18%
}

# ============================================================
# FUNCIONES DE CÁLCULO
# ============================================================

def factor_temperatura(temp_amb):
    """
    Retorna el factor de corrección por temperatura.
    Si la temperatura no está en la tabla usa 1.00 (30°C).
    """
    return FACTORES_TEMP.get(int(temp_amb), 1.00)

def capacidad_corregida(I_max, paralelos, temp_amb):
    """
    Calcula la capacidad real del conjunto de conductores
    aplicando corrección por temperatura y cantidad de paralelos.
    Capacidad = I_max × paralelos × factor_temperatura
    """
    factor = factor_temperatura(temp_amb)
    return round(I_max * paralelos * factor, 1)

def calcular_potencia(I_diseno, cos_phi, sistema):
    """
    Calcula potencia activa según el tipo de sistema.
    3F: P = √3 × V × I × cosφ
    1F/2F: P = V × I × cosφ
    """
    V = TENSION_SISTEMA.get(sistema, 380)
    if sistema == "3F":
        P = 1.732 * V * I_diseno * cos_phi
    else:
        P = V * I_diseno * cos_phi
    return round(P)

def calcular_caida_tension(L_m, S_mm2, I_diseno, paralelos, sistema):
    """
    Calcula caída de tensión según el tipo de sistema.
    Incorpora conductores en paralelo aumentando la sección equivalente.
    Retorna caída en V y en %.
    """
    # Sección equivalente total con paralelos
    # Más paralelos = más sección = menos caída
    S_eq   = S_mm2 * paralelos

    # Factor según sistema (1.732 para 3F, 2.0 para 1F/2F)
    factor = FACTOR_SISTEMA.get(sistema, 1.732)

    # Tensión nominal para calcular el porcentaje
    V_nom  = TENSION_SISTEMA.get(sistema, 380)

    # Fórmula de caída de tensión
    dV_V   = (factor * RHO_CU * L_m * I_diseno) / S_eq
    dV_pct = (dV_V / V_nom) * 100

    return round(dV_V, 3), round(dV_pct, 3)

def clasificar_caida(dV_pct):
    """Clasifica estado normativo según SEC RIC N°10 / IEC 60364."""
    if dV_pct <= 1.5:
        return "ÓPTIMO"
    elif dV_pct <= 3.0:
        return "ACEPTABLE"
    elif dV_pct <= 5.0:
        return "PRECAUCIÓN — supera 3% circuito final"
    else:
        return "FALLA — supera 5% total instalación"

# ============================================================
# LECTURA EXCEL
# ============================================================

def leer_circuitos_excel(nombre_archivo):
    """
    Lee circuitos desde Excel.
    Estructura esperada (fila 1 = encabezados):
        A: nombre | B: sistema | C: conductor | D: paralelos
        E: I_diseno | F: cos_phi | G: L_m | H: temp_amb
    """
    circuitos = []
    errores   = []

    libro = openpyxl.load_workbook(nombre_archivo, data_only=True)
    hoja  = libro.active

    print(f"\n  Leyendo: {nombre_archivo}")
    print(f"  Circuitos encontrados: {hoja.max_row - 1}")

    for fila in hoja.iter_rows(min_row=2, values_only=True):
        nombre    = fila[0]
        sistema   = fila[1]
        conductor = fila[2]
        paralelos = fila[3]
        I_diseno  = fila[4]
        cos_phi   = fila[5]
        L_m       = fila[6]
        temp_amb  = fila[7]

        # Saltar filas vacías
        if nombre is None:
            continue

        # Normalizar texto
        sistema   = str(sistema).strip().upper()
        conductor = str(conductor).strip().upper()

        # Validar sistema
        if sistema not in FACTOR_SISTEMA:
            errores.append(f"'{nombre}': sistema '{sistema}' inválido (usar 1F, 2F o 3F)")
            continue

        # Validar conductor
        if conductor not in CONDUCTORES:
            errores.append(f"'{nombre}': conductor '{conductor}' no existe en tabla")
            continue

        circuitos.append({
            "nombre":    str(nombre).strip(),
            "sistema":   sistema,
            "conductor": conductor,
            "S_mm2":     CONDUCTORES[conductor]["mm2"],
            "I_max":     CONDUCTORES[conductor]["I_max"],
            "paralelos": int(paralelos),
            "I_diseno":  float(I_diseno),
            "cos_phi":   float(cos_phi),
            "L_m":       float(L_m),
            "temp_amb":  float(temp_amb),
        })

    # Mostrar advertencias sin detener el programa
    if errores:
        print("\n  ADVERTENCIAS:")
        for e in errores:
            print(f"  ⚠ {e}")

    return circuitos

# ============================================================
# GENERACIÓN DE REPORTE
# ============================================================

def generar_reporte(nombre_proyecto, circuitos, fecha):
    """Genera reporte completo como lista de líneas."""
    lineas      = []
    total_ok    = 0
    total_falla = 0

    # Encabezado
    lineas.append("=" * 60)
    lineas.append(f"  REPORTE — {nombre_proyecto}")
    lineas.append(f"  Fecha          : {fecha}")
    lineas.append(f"  Normativa      : SEC RIC N10 / NEC / IEC 60364")
    lineas.append(f"  Limite caida   : {LIMITE_DV}% circuito final / 5% total")
    lineas.append(f"  Total circuitos: {len(circuitos)}")
    lineas.append("=" * 60)

    for c in circuitos:
        # Calcular
        I_cap        = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
        P_watts      = calcular_potencia(c["I_diseno"], c["cos_phi"], c["sistema"])
        dV_V, dV_pct = calcular_caida_tension(
                           c["L_m"], c["S_mm2"], c["I_diseno"],
                           c["paralelos"], c["sistema"]
                       )
        estado       = clasificar_caida(dV_pct)

        # Verificar corriente con capacidad corregida
        if c["I_diseno"] > I_cap:
            alerta_I = f"SUPERA capacidad {I_cap}A"
        else:
            alerta_I = f"OK (cap. {I_cap}A)"

        # Descripción del sistema
        V_nom = TENSION_SISTEMA[c["sistema"]]
        desc_sistema = f"{c['sistema']} / {V_nom}V"

        # Descripción del conductor con paralelos
        if c["paralelos"] > 1:
            desc_conductor = f"{c['paralelos']}x{c['conductor']} ({c['S_mm2']}mm2 c/u = {c['S_mm2']*c['paralelos']}mm2 total)"
        else:
            desc_conductor = f"{c['conductor']} ({c['S_mm2']} mm2)"

        lineas.append("")
        lineas.append(f"  Circuito   : {c['nombre']}")
        lineas.append(f"  Sistema    : {desc_sistema} | Temp: {c['temp_amb']}C")
        lineas.append(f"  Conductor  : {desc_conductor}")
        lineas.append(f"  Corriente  : {c['I_diseno']}A diseño -> {alerta_I}")
        lineas.append(f"  Potencia   : {P_watts} W")
        lineas.append(f"  Caida dV   : {dV_V} V  ({dV_pct}%)  -> {estado}")

        if "FALLA" in estado or "SUPERA" in alerta_I:
            total_falla += 1
        else:
            total_ok += 1

    # Resumen
    lineas.append("")
    lineas.append("=" * 60)
    lineas.append(f"  Circuitos OK    : {total_ok}")
    lineas.append(f"  Circuitos FALLA : {total_falla}")
    lineas.append("=" * 60)

    return lineas, total_ok, total_falla

def guardar_reporte(lineas, nombre_archivo):
    """Guarda reporte en archivo txt."""
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")
    print(f"\n  Reporte guardado: {nombre_archivo}")

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("=" * 60)
print("  MOTOR DE CALCULO BT")
print("  Soporte: 1F / 2F / 3F | Paralelos | Temp. ambiente")
print("  Normativa: SEC RIC N10 / NEC / IEC 60364")
print("=" * 60)

ahora         = datetime.now()
fecha         = ahora.strftime("%d/%m/%Y %H:%M")
fecha_archivo = ahora.strftime("%Y%m%d_%H%M")

nombre_proyecto = input("\n  Nombre del proyecto : ").strip()
archivo_excel   = input("  Archivo Excel       : ").strip()

if not archivo_excel.endswith(".xlsx"):
    archivo_excel += ".xlsx"

try:
    circuitos = leer_circuitos_excel(archivo_excel)
except FileNotFoundError:
    print(f"\n  ERROR: no se encontro '{archivo_excel}'")
    print("  Verifica que el archivo esta en la carpeta del proyecto")
    exit()

if len(circuitos) == 0:
    print("  ERROR: no se encontraron circuitos validos")
    exit()

# Generar y mostrar reporte
lineas, total_ok, total_falla = generar_reporte(
    nombre_proyecto, circuitos, fecha
)

print()
for linea in lineas:
    print(linea)

# Guardar reporte
nombre_archivo = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.txt"
guardar_reporte(lineas, nombre_archivo)