# ============================================================
# Motor de Cálculo BT — Bloque 5: Leer desde Excel
# Proyecto: Herramienta para proyectos eléctricos
# Sistema: 380V / 3P+N / 50Hz
# ============================================================

from datetime import datetime
import openpyxl   # librería para leer/escribir archivos Excel

# --- CONSTANTES ---
V_NOMINAL = 380
RHO_CU    = 0.0175
LIMITE_DV = 3.0

# --- TABLA DE CONDUCTORES ---
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

# --- FUNCIONES DE CÁLCULO ---

def calcular_potencia(I_diseno, cos_phi):
    """Calcula potencia activa trifásica en Watts."""
    return round(1.732 * V_NOMINAL * I_diseno * cos_phi)

def calcular_caida_tension(L_m, S_mm2, I_diseno):
    """Calcula caída de tensión trifásica en V y %."""
    dV_V   = (1.732 * RHO_CU * L_m * I_diseno) / S_mm2
    dV_pct = (dV_V / V_NOMINAL) * 100
    return round(dV_V, 3), round(dV_pct, 3)

def clasificar_caida(dV_pct):
    """Clasifica estado normativo según caída de tensión."""
    if dV_pct <= 1.5:
        return "ÓPTIMO"
    elif dV_pct <= 3.0:
        return "ACEPTABLE"
    elif dV_pct <= 5.0:
        return "PRECAUCIÓN"
    else:
        return "FALLA — redimensionar conductor"

# --- FUNCIÓN DE LECTURA EXCEL ---

def leer_circuitos_excel(nombre_archivo):
    """
    Lee los circuitos desde un archivo Excel.
    Estructura esperada:
        Columna A → nombre
        Columna B → conductor
        Columna C → I_diseno
        Columna D → cos_phi
        Columna E → L_m
    La fila 1 es el encabezado — se omite.
    Retorna lista de diccionarios con los datos de cada circuito.
    """
    circuitos = []   # lista vacía donde guardaremos los circuitos
    errores   = []   # lista para registrar filas con problemas

    # Abrir el archivo Excel
    # data_only=True lee los valores calculados, no las fórmulas
    libro = openpyxl.load_workbook(nombre_archivo, data_only=True)

    # Seleccionar la primera hoja del libro
    hoja = libro.active

    print(f"\n  Leyendo: {nombre_archivo}")
    print(f"  Filas encontradas: {hoja.max_row - 1} circuitos")
    print()

    # Recorrer filas desde la 2 (fila 1 es encabezado)
    # hoja.iter_rows() recorre fila por fila
    # min_row=2 salta el encabezado
    # values_only=True devuelve solo los valores, no objetos de celda
    for fila in hoja.iter_rows(min_row=2, values_only=True):

        # Cada fila es una tupla con los valores de cada columna
        nombre    = fila[0]   # columna A
        conductor = fila[1]   # columna B
        I_diseno  = fila[2]   # columna C
        cos_phi   = fila[3]   # columna D
        L_m       = fila[4]   # columna E

        # Saltar filas vacías — puede haber filas vacías al final
        if nombre is None:
            continue

        # Convertir conductor a mayúsculas para coincidir con la tabla
        conductor = str(conductor).strip().upper()

        # Verificar que el conductor existe en la tabla
        if conductor not in CONDUCTORES:
            errores.append(f"  ⚠ Fila '{nombre}': conductor '{conductor}' no existe")
            continue

        # Agregar el circuito a la lista
        circuitos.append({
            "nombre":    str(nombre).strip(),
            "conductor": conductor,
            "S_mm2":     CONDUCTORES[conductor]["mm2"],
            "I_max":     CONDUCTORES[conductor]["I_max"],
            "I_diseno":  float(I_diseno),
            "cos_phi":   float(cos_phi),
            "L_m":       float(L_m),
        })

    # Mostrar errores si los hay
    if errores:
        print("  ADVERTENCIAS:")
        for e in errores:
            print(e)
        print()

    return circuitos

# --- FUNCIONES DE REPORTE ---

def generar_reporte(nombre_proyecto, circuitos, fecha):
    """Genera reporte como lista de líneas."""
    lineas      = []
    total_ok    = 0
    total_falla = 0

    lineas.append("=" * 55)
    lineas.append(f"  REPORTE — {nombre_proyecto}")
    lineas.append(f"  Fecha  : {fecha}")
    lineas.append(f"  Sistema: {V_NOMINAL}V / 3P+N / 50Hz")
    lineas.append(f"  Total circuitos: {len(circuitos)}")
    lineas.append("=" * 55)

    for c in circuitos:
        P_watts      = calcular_potencia(c["I_diseno"], c["cos_phi"])
        dV_V, dV_pct = calcular_caida_tension(c["L_m"], c["S_mm2"], c["I_diseno"])
        estado       = clasificar_caida(dV_pct)

        if c["I_diseno"] > c["I_max"]:
            alerta_I = f"SUPERA max {c['I_max']}A"
        else:
            alerta_I = f"OK (max {c['I_max']}A)"

        lineas.append("")
        lineas.append(f"  Circuito  : {c['nombre']}")
        lineas.append(f"  Conductor : {c['conductor']} ({c['S_mm2']} mm2)")
        lineas.append(f"  Corriente : {c['I_diseno']} A  -> {alerta_I}")
        lineas.append(f"  Potencia  : {P_watts} W")
        lineas.append(f"  Caida dV  : {dV_V} V  ({dV_pct} %)  -> {estado}")

        if "FALLA" in estado:
            total_falla += 1
        else:
            total_ok += 1

    lineas.append("")
    lineas.append("=" * 55)
    lineas.append(f"  Circuitos OK    : {total_ok}")
    lineas.append(f"  Circuitos FALLA : {total_falla}")
    lineas.append("=" * 55)

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

print("=" * 55)
print("  MOTOR DE CALCULO BT")
print("  Herramienta para proyectos electricos")
print(f"  Sistema: {V_NOMINAL}V / 3P+N / 50Hz")
print("=" * 55)

# Fecha para el reporte y nombre del archivo
ahora         = datetime.now()
fecha         = ahora.strftime("%d/%m/%Y %H:%M")
fecha_archivo = ahora.strftime("%Y%m%d_%H%M")

# Pedir nombre del proyecto y archivo Excel
nombre_proyecto = input("\n  Nombre del proyecto : ").strip()
archivo_excel   = input("  Archivo Excel       : ").strip()

# Verificar que el archivo termina en .xlsx
if not archivo_excel.endswith(".xlsx"):
    archivo_excel = archivo_excel + ".xlsx"

# Leer circuitos desde Excel
try:
    # try/except captura errores sin romper el programa
    # Si el archivo no existe, muestra mensaje claro
    circuitos = leer_circuitos_excel(archivo_excel)
except FileNotFoundError:
    print(f"\n  ERROR: no se encontro el archivo '{archivo_excel}'")
    print("  Verifica que el archivo esta en la carpeta motor-calculo-bt")
    exit()   # detiene el programa

if len(circuitos) == 0:
    print("  ERROR: no se encontraron circuitos validos en el archivo")
    exit()

# Generar reporte
lineas, total_ok, total_falla = generar_reporte(
    nombre_proyecto, circuitos, fecha
)

# Mostrar en pantalla
for linea in lineas:
    print(linea)

# Guardar en archivo
nombre_archivo = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.txt"
guardar_reporte(lineas, nombre_archivo)