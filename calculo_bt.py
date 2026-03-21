# ============================================================
# Motor de Cálculo BT — Fase 2: Listas y Diccionarios
# Proyecto: EDD PROJECT LEO - ARICA
# Sistema: 380V / 3P+N / 50Hz
# ============================================================

# --- CONSTANTES ---
V_NOMINAL = 380
RHO_CU    = 0.0175
LIMITE_DV = 3.0

# --- FUNCIONES (las mismas del bloque anterior) ---

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

# ============================================================
# LISTA DE DICCIONARIOS
# Cada circuito del unifilar E-01 Rev12 es un diccionario
# Todos los circuitos están en una lista llamada CIRCUITOS
# Para agregar un circuito nuevo: agrega un bloque {} a la lista
# ============================================================

CIRCUITOS = [
    {
        "nombre":    "CRAC Unit 1-A",
        "conductor": "6AWG",
        "S_mm2":     13.3,
        "I_diseno":  63,
        "cos_phi":   0.85,
        "L_m":       10,
    },
    {
        "nombre":    "CRAC Unit 1-B",
        "conductor": "6AWG",
        "S_mm2":     13.3,
        "I_diseno":  63,
        "cos_phi":   0.85,
        "L_m":       10,
    },
    {
        "nombre":    "Antenna Panel campo",
        "conductor": "2AWG",
        "S_mm2":     33.6,
        "I_diseno":  63,
        "cos_phi":   0.85,
        "L_m":       80,
    },
    {
        "nombre":    "STS Panel - BUS A",
        "conductor": "1/0AWG",
        "S_mm2":     53.5,
        "I_diseno":  63,
        "cos_phi":   0.90,
        "L_m":       20,
    },
    {
        "nombre":    "STS Panel - BUS B",
        "conductor": "1/0AWG",
        "S_mm2":     53.5,
        "I_diseno":  63,
        "cos_phi":   0.90,
        "L_m":       20,
    },
    {
        "nombre":    "Alimentación UPS 1 - BUS A",
        "conductor": "400MCM x4",
        "S_mm2":     203.0,
        "I_diseno":  500,
        "cos_phi":   0.90,
        "L_m":       15,
    },
    {
        "nombre":    "Alimentación UPS 2 - BUS B",
        "conductor": "400MCM x4",
        "S_mm2":     203.0,
        "I_diseno":  500,
        "cos_phi":   0.90,
        "L_m":       15,
    },
]

# ============================================================
# PROGRAMA PRINCIPAL
# El bucle for recorre cada circuito de la lista automáticamente
# c es cada diccionario en cada vuelta del bucle
# c["nombre"] accede al valor de la clave "nombre"
# ============================================================

print("=" * 55)
print("  VERIFICACIÓN BT — EDD PROJECT LEO ARICA")
print(f"  Total circuitos: {len(CIRCUITOS)}")
print("=" * 55)
print()

# Contadores para el resumen final
total_ok    = 0
total_falla = 0

for c in CIRCUITOS:

    # Extraer los datos del diccionario
    nombre    = c["nombre"]
    conductor = c["conductor"]
    I_diseno  = c["I_diseno"]
    cos_phi   = c["cos_phi"]
    L_m       = c["L_m"]
    S_mm2     = c["S_mm2"]

    # Calcular con las funciones
    P_watts      = calcular_potencia(I_diseno, cos_phi)
    dV_V, dV_pct = calcular_caida_tension(L_m, S_mm2, I_diseno)
    estado       = clasificar_caida(dV_pct)

    # Mostrar resultado
    print(f"  {nombre}")
    print(f"  Conductor : {conductor} | {I_diseno}A | {L_m}m")
    print(f"  Potencia  : {P_watts} W")
    print(f"  Caída ΔV  : {dV_V} V  ({dV_pct} %)  → {estado}")
    print()

    # Actualizar contadores
    if estado == "FALLA — redimensionar conductor":
        total_falla += 1
    else:
        total_ok += 1

# Resumen final
print("=" * 55)
print(f"  Circuitos OK    : {total_ok}")
print(f"  Circuitos FALLA : {total_falla}")
print("=" * 55)