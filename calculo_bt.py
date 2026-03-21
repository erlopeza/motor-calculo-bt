# ============================================================
# Motor de Cálculo BT — Bloque 4: Exportar reporte
# Proyecto: Herramienta para proyectos eléctricos
# Sistema: 380V / 3P+N / 50Hz
# ============================================================

# datetime permite obtener la fecha y hora actual
# Lo usaremos para el nombre del archivo y el encabezado del reporte
from datetime import datetime

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

def mostrar_conductores():
    """Muestra la tabla de conductores disponibles."""
    print("\n  Conductores disponibles:")
    print("  " + "-" * 40)
    for nombre, datos in CONDUCTORES.items():
        print(f"  {nombre:8} → {datos['mm2']:6} mm²  |  {datos['I_max']} A máx")
    print("  " + "-" * 40)

def ingresar_circuito(numero):
    """Solicita datos de un circuito por teclado."""
    print(f"\n  === CIRCUITO {numero} ===")
    nombre    = input("  Nombre del circuito : ").strip()
    mostrar_conductores()
    conductor = input("  Conductor (ej: 6AWG): ").strip().upper()
    while conductor not in CONDUCTORES:
        print(f"  ⚠ '{conductor}' no existe.")
        conductor = input("  Conductor           : ").strip().upper()
    I_diseno = float(input("  Corriente diseño (A): "))
    cos_phi  = float(input("  Factor de potencia  : "))
    L_m      = float(input("  Longitud cable (m)  : "))
    return {
        "nombre":    nombre,
        "conductor": conductor,
        "S_mm2":     CONDUCTORES[conductor]["mm2"],
        "I_max":     CONDUCTORES[conductor]["I_max"],
        "I_diseno":  I_diseno,
        "cos_phi":   cos_phi,
        "L_m":       L_m,
    }

# --- FUNCIÓN DE REPORTE ---
# Recibe la lista de circuitos y el nombre del proyecto
# Genera las líneas del reporte como texto
# Retorna una lista de líneas — así podemos mostrar Y guardar

def generar_reporte(nombre_proyecto, circuitos, fecha):
    """
    Genera el reporte completo como lista de líneas de texto.
    Retorna: lista de strings y contadores ok/falla.
    """
    lineas     = []   # lista vacía donde iremos agregando líneas
    total_ok   = 0
    total_falla = 0

    # Encabezado
    lineas.append("=" * 55)
    lineas.append(f"  REPORTE — {nombre_proyecto}")
    lineas.append(f"  Fecha  : {fecha}")
    lineas.append(f"  Sistema: {V_NOMINAL}V / 3P+N / 50Hz")
    lineas.append("=" * 55)

    # Una sección por cada circuito
    for c in circuitos:
        P_watts      = calcular_potencia(c["I_diseno"], c["cos_phi"])
        dV_V, dV_pct = calcular_caida_tension(c["L_m"], c["S_mm2"], c["I_diseno"])
        estado       = clasificar_caida(dV_pct)

        # Verificar corriente vs capacidad
        if c["I_diseno"] > c["I_max"]:
            alerta_I = f"⚠ SUPERA máx {c['I_max']}A"
        else:
            alerta_I = f"OK (máx {c['I_max']}A)"

        lineas.append("")
        lineas.append(f"  Circuito  : {c['nombre']}")
        lineas.append(f"  Conductor : {c['conductor']} ({c['S_mm2']} mm²)")
        lineas.append(f"  Corriente : {c['I_diseno']} A  → {alerta_I}")
        lineas.append(f"  Potencia  : {P_watts} W")
        lineas.append(f"  Caída ΔV  : {dV_V} V  ({dV_pct} %)  → {estado}")

        # Actualizar contadores
        if "FALLA" in estado:
            total_falla += 1
        else:
            total_ok += 1

    # Resumen final
    lineas.append("")
    lineas.append("=" * 55)
    lineas.append(f"  Circuitos OK    : {total_ok}")
    lineas.append(f"  Circuitos FALLA : {total_falla}")
    lineas.append("=" * 55)

    return lineas, total_ok, total_falla

def guardar_reporte(lineas, nombre_archivo):
    """
    Guarda la lista de líneas en un archivo .txt
    El archivo queda en la misma carpeta que el script.
    """
    # with garantiza que el archivo se cierra aunque haya error
    # "w" crea el archivo o sobreescribe si ya existe
    # encoding="utf-8" soporta tildes y caracteres especiales
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")   # \n = salto de línea

    print(f"\n  ✓ Reporte guardado: {nombre_archivo}")

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("=" * 55)
print("  MOTOR DE CÁLCULO BT")
print("  Herramienta para proyectos eléctricos")
print(f"  Sistema: {V_NOMINAL}V / 3P+N / 50Hz")
print("=" * 55)

# Fecha y hora actual — para el reporte y el nombre del archivo
# strftime define el formato: día/mes/año hora:minuto
ahora = datetime.now()
fecha = ahora.strftime("%d/%m/%Y %H:%M")

# Nombre del archivo usa fecha sin caracteres especiales
# Formato: REPORTE_PROYECTO_20260321_1430.txt
fecha_archivo = ahora.strftime("%Y%m%d_%H%M")

nombre_proyecto = input("\n  Nombre del proyecto: ").strip()
n_circuitos     = int(input("  ¿Cuántos circuitos? : "))

# Ingresar circuitos
circuitos = []
for i in range(n_circuitos):
    c = ingresar_circuito(i + 1)
    circuitos.append(c)

# Generar reporte
lineas, total_ok, total_falla = generar_reporte(
    nombre_proyecto, circuitos, fecha
)

# Mostrar en pantalla
print()
for linea in lineas:
    print(linea)

# Guardar en archivo
nombre_archivo = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.txt"
guardar_reporte(lineas, nombre_archivo)