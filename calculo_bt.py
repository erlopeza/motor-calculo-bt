# ============================================================
# Motor de Cálculo BT — Bloque 3: Ingreso de datos
# Proyecto: Herramienta para proyectos nuevos
# Sistema: 380V / 3P+N / 50Hz
# ============================================================

# --- CONSTANTES DEL SISTEMA ---
V_NOMINAL = 380      # tensión del sistema en Voltios
RHO_CU    = 0.0175   # resistividad del cobre en Ω·mm²/m
LIMITE_DV = 3.0      # límite normativo de caída en %

# --- TABLA DE CONDUCTORES AWG ---
# Diccionario con sección en mm² y capacidad de corriente
# Clave: nombre del conductor
# Valor: diccionario con sus propiedades

CONDUCTORES = {
    "14AWG":  {"mm2": 2.08,   "I_max": 20},
    "12AWG":  {"mm2": 3.31,   "I_max": 25},
    "10AWG":  {"mm2": 5.26,   "I_max": 35},
    "8AWG":   {"mm2": 8.37,   "I_max": 50},
    "6AWG":   {"mm2": 13.3,   "I_max": 65},
    "4AWG":   {"mm2": 21.1,   "I_max": 85},
    "2AWG":   {"mm2": 33.6,   "I_max": 115},
    "1/0AWG": {"mm2": 53.5,   "I_max": 150},
    "2/0AWG": {"mm2": 67.4,   "I_max": 175},
    "4/0AWG": {"mm2": 107.0,  "I_max": 230},
    "350MCM": {"mm2": 177.0,  "I_max": 310},
    "400MCM": {"mm2": 203.0,  "I_max": 335},
    "500MCM": {"mm2": 253.0,  "I_max": 380},
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
    """
    Solicita al usuario los datos de un circuito por teclado.
    Retorna un diccionario con todos los datos ingresados.
    """
    print(f"\n  === CIRCUITO {numero} ===")

    # input() siempre devuelve texto
    # strip() elimina espacios accidentales al inicio y final
    nombre = input("  Nombre del circuito : ").strip()

    # Mostrar tabla antes de pedir el conductor
    mostrar_conductores()
    conductor = input("  Conductor (ej: 6AWG): ").strip().upper()

    # Verificar que el conductor existe en la tabla
    # Si no existe, pedir de nuevo
    while conductor not in CONDUCTORES:
        print(f"  ⚠ '{conductor}' no está en la tabla. Intenta de nuevo.")
        conductor = input("  Conductor (ej: 6AWG): ").strip().upper()

    # float() convierte el texto a número decimal
    I_diseno = float(input("  Corriente diseño (A): "))
    cos_phi  = float(input("  Factor de potencia (ej: 0.85): "))
    L_m      = float(input("  Longitud del cable (m): "))

    # Obtener S_mm2 automáticamente desde la tabla
    # No hay que ingresarlo — se saca del conductor elegido
    S_mm2 = CONDUCTORES[conductor]["mm2"]
    I_max = CONDUCTORES[conductor]["I_max"]

    # Retorna el diccionario completo del circuito
    return {
        "nombre":    nombre,
        "conductor": conductor,
        "S_mm2":     S_mm2,
        "I_max":     I_max,
        "I_diseno":  I_diseno,
        "cos_phi":   cos_phi,
        "L_m":       L_m,
    }

def calcular_y_mostrar(c):
    """Calcula y muestra el resultado de un circuito."""
    P_watts      = calcular_potencia(c["I_diseno"], c["cos_phi"])
    dV_V, dV_pct = calcular_caida_tension(c["L_m"], c["S_mm2"], c["I_diseno"])
    estado       = clasificar_caida(dV_pct)

    # Verificar si la corriente supera la capacidad del conductor
    if c["I_diseno"] > c["I_max"]:
        alerta_I = f"⚠ SUPERA capacidad máx {c['I_max']}A"
    else:
        alerta_I = f"OK (máx {c['I_max']}A)"

    print(f"\n  RESULTADO: {c['nombre']}")
    print(f"  Conductor : {c['conductor']} ({c['S_mm2']} mm²)")
    print(f"  Corriente : {c['I_diseno']} A  → {alerta_I}")
    print(f"  Potencia  : {P_watts} W")
    print(f"  Caída ΔV  : {dV_V} V  ({dV_pct} %)  → {estado}")

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("=" * 55)
print("  MOTOR DE CÁLCULO BT")
print("  Herramienta para proyectos eléctricos")
print(f"  Sistema: {V_NOMINAL}V / 3P+N / 50Hz")
print("=" * 55)

# Pedir nombre del proyecto
nombre_proyecto = input("\n  Nombre del proyecto: ").strip()
print(f"\n  Proyecto: {nombre_proyecto}")

# Preguntar cuántos circuitos tiene el proyecto
# int() convierte el texto a número entero
n_circuitos = int(input("  ¿Cuántos circuitos? : "))

# Lista vacía donde iremos guardando los circuitos
circuitos = []

# Bucle que se repite n_circuitos veces
# range(n) genera los números 0, 1, 2 ... n-1
# i+1 lo convierte en 1, 2, 3 ... n  (más legible)
for i in range(n_circuitos):
    c = ingresar_circuito(i + 1)
    circuitos.append(c)   # append() agrega un elemento al final de la lista

# Mostrar reporte final
print("\n")
print("=" * 55)
print(f"  REPORTE FINAL — {nombre_proyecto}")
print("=" * 55)

total_ok    = 0
total_falla = 0

for c in circuitos:
    calcular_y_mostrar(c)

    estado = clasificar_caida(
        calcular_caida_tension(c["L_m"], c["S_mm2"], c["I_diseno"])[1]
    )
    if "FALLA" in estado:
        total_falla += 1
    else:
        total_ok += 1

print("\n" + "=" * 55)
print(f"  Circuitos OK    : {total_ok}")
print(f"  Circuitos FALLA : {total_falla}")
print("=" * 55)