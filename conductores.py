# ============================================================
# conductores.py
# Responsabilidad: datos técnicos de conductores y sistemas
# Razón para cambiar: actualización de norma o tabla NEC/RIC
# ============================================================

# --- RESISTIVIDAD DE MATERIALES ---
RHO_CU = 0.0175   # cobre Ω·mm²/m
RHO_AL = 0.028    # aluminio Ω·mm²/m

# --- LÍMITE NORMATIVO DE CAÍDA DE TENSIÓN ---
# SEC RIC N°10 / IEC 60364 — circuito final
LIMITE_DV = 3.0   # porcentaje máximo permitido

# --- TENSIONES NOMINALES POR SISTEMA ---
TENSION_SISTEMA = {
    "3F": 380,   # trifásico — tensión de línea L-L
    "1F": 220,   # monofásico — tensión fase-neutro L-N
    "2F": 220,   # bifásico — tensión fase-neutro L-N
}

# --- FACTOR DE CAÍDA POR SISTEMA ---
# 3F usa √3 — corriente circula por 3 fases
# 1F y 2F usan 2 — corriente va y vuelve (ida + neutro)
FACTOR_SISTEMA = {
    "3F": 1.732,
    "1F": 2.0,
    "2F": 2.0,
}

# --- TABLA DE CONDUCTORES AWG/MCM ---
# Fuente: NEC Table 310.15 — XLPE/PVC 90°C en conduit
# Temperatura de referencia: 30°C
# Orden: de menor a mayor sección (crítico para sugerencia automática)
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
# Fuente: NEC Table 310.15(B)(1) — conductor XLPE 90°C
# A mayor temperatura ambiente → menor capacidad de corriente
FACTORES_TEMP = {
    25: 1.04,   # más frío que referencia → más capacidad
    30: 1.00,   # temperatura de referencia
    35: 0.96,   # reducción 4%
    40: 0.91,   # reducción 9%
    45: 0.87,   # reducción 13%
    50: 0.82,   # reducción 18%
}