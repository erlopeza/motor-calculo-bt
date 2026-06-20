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
    "3F": 380,
    "1F": 220,
    "2F": 220,
}

# --- FACTOR DE CAÍDA POR SISTEMA ---
FACTOR_SISTEMA = {
    "3F": 1.732,
    "1F": 2.0,
    "2F": 2.0,
}

# --- TABLA AWG/MCM ---
# Fuente: NEC Table 310.15 — XLPE/PVC 90°C en conduit, 30°C
# Orden ascendente de sección (requerido por sugerencia automática)
CONDUCTORES_AWG = {
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

# --- TABLA mm² (RIC N°04 / IEC 60228) ---
# Fuente: SEC RIC N°04 Tabla 1 / IEC 60228 clase 2
# Capacidad: XLPE Cu en conduit, 30°C (IEC 60364-5-52 Método B2)
# Orden ascendente de sección (requerido por sugerencia automática)
CONDUCTORES_MM2 = {
    "1.5MM2":  {"mm2": 1.5,   "I_max": 15},
    "2.5MM2":  {"mm2": 2.5,   "I_max": 21},
    "4MM2":    {"mm2": 4.0,   "I_max": 28},
    "6MM2":    {"mm2": 6.0,   "I_max": 36},
    "10MM2":   {"mm2": 10.0,  "I_max": 50},
    "16MM2":   {"mm2": 16.0,  "I_max": 68},
    "25MM2":   {"mm2": 25.0,  "I_max": 89},
    "35MM2":   {"mm2": 35.0,  "I_max": 110},
    "50MM2":   {"mm2": 50.0,  "I_max": 134},
    "70MM2":   {"mm2": 70.0,  "I_max": 171},
    "95MM2":   {"mm2": 95.0,  "I_max": 207},
    "120MM2":  {"mm2": 120.0, "I_max": 239},
    "150MM2":  {"mm2": 150.0, "I_max": 275},
    "185MM2":  {"mm2": 185.0, "I_max": 314},
    "240MM2":  {"mm2": 240.0, "I_max": 370},
    "300MM2":  {"mm2": 300.0, "I_max": 421},
}

# --- SELECTOR DE TABLA POR NORMA ---
# Uso: get_tabla_conductores(perfil["norma"])
# Valores válidos: "AWG" | "MM2"
CONDUCTORES = {
    **CONDUCTORES_AWG,
    **CONDUCTORES_MM2,
    "AWG": CONDUCTORES_AWG,
    "MM2": CONDUCTORES_MM2,
}

def get_tabla_conductores(norma: str) -> dict:
    """
    Retorna tabla de conductores según norma del perfil.
    norma: "AWG" → NEC / "MM2" → RIC N°04 / IEC 60228
    """
    norma = norma.upper()
    if norma not in CONDUCTORES:
        raise ValueError(f"Norma '{norma}' no válida. Usar 'AWG' o 'MM2'.")
    return CONDUCTORES[norma]

# --- FACTORES DE CORRECCIÓN POR TEMPERATURA ---
# Fuente: NEC Table 310.15(B)(1) — conductor XLPE 90°C
FACTORES_TEMP = {
    25: 1.04,
    30: 1.00,
    35: 0.96,
    40: 0.91,
    45: 0.87,
    50: 0.82,
}

# --- REACTANCIA INDUCTIVA POR SECCIÓN — DATA-1 ---
# Fuente: IEC 60909-2:2008 Tabla B.1 / NEC Chapter 9 Table 9 (60 Hz × 5/6)
# Valores típicos para cables de Cu en instalación BT (conduit/bandeja) a 50 Hz.
# Unidades: Ω por kilómetro de cable (Ω/km).
# Para obtener X_ohm: X = REACTANCIA_CABLE_OHM_KM[S_mm2] * L_m / 1000 / paralelos
_REACTANCIA_CABLE_OHM_KM: dict[float, float] = {
    1.5:   0.090,
    2.5:   0.087,
    4.0:   0.085,
    6.0:   0.083,
    10.0:  0.080,
    16.0:  0.078,
    25.0:  0.076,
    35.0:  0.075,
    50.0:  0.073,
    70.0:  0.071,
    95.0:  0.070,
    120.0: 0.068,
    150.0: 0.067,
    185.0: 0.066,
    240.0: 0.065,
    300.0: 0.064,
    400.0: 0.063,
    500.0: 0.062,
}
_REACTANCIA_SECCIONES = sorted(_REACTANCIA_CABLE_OHM_KM.keys())


def get_reactancia_cable_ohm_km(S_mm2: float) -> float:
    """Reactancia inductiva del cable por kilómetro a 50 Hz (Ω/km).

    Interpola linealmente en la tabla IEC 60909-2 Tabla B.1.
    Para secciones fuera de rango extrapola con el valor extremo más próximo.
    """
    s = float(S_mm2)
    secciones = _REACTANCIA_SECCIONES
    if s <= secciones[0]:
        return _REACTANCIA_CABLE_OHM_KM[secciones[0]]
    if s >= secciones[-1]:
        return _REACTANCIA_CABLE_OHM_KM[secciones[-1]]
    for i in range(len(secciones) - 1):
        s0, s1 = secciones[i], secciones[i + 1]
        if s0 <= s <= s1:
            x0 = _REACTANCIA_CABLE_OHM_KM[s0]
            x1 = _REACTANCIA_CABLE_OHM_KM[s1]
            frac = (s - s0) / (s1 - s0)
            return round(x0 + (x1 - x0) * frac, 6)
    return _REACTANCIA_CABLE_OHM_KM[secciones[-1]]
