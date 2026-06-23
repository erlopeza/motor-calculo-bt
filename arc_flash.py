# ============================================================
# arc_flash.py
# Responsabilidad: cálculo de energía incidente y frontera de arco
# Método: IEEE 1584-2002 (empírico, validado para 208V–15kV)
# Razón para cambiar: adoptar IEEE 1584-2018 (multi-régimen)
#
# LIMITACIÓN:
#   Se usa el modelo 2002 por su amplio uso en América Latina.
#   IEEE 1584-2018 mejora precisión en 208–600V y geometrías
#   específicas; migración futura cuando laboratorios lo validen.
# ============================================================

from __future__ import annotations

import math

import coordinacion


# ============================================================
# CONSTANTES NORMATIVAS
# ============================================================

# Factor de corrección voltaje — IEEE 1584-2002 §4.7
_CF_BT = 1.5   # V ≤ 1 kV
_CF_MT = 1.0   # V > 1 kV

# Distancia de referencia — IEEE 1584-2002 §4.8
_D_REF_MM = 610.0

# Exponente de distancia x por configuración — IEEE 1584-2002 Tabla 4 (≤1 kV)
#   open  : aire abierto / cable        → 2.000
#   box   : tablero/switchgear cerrado  → 1.473
# Debe ser coherente con K1 (que también depende de la configuración).
_X_DISTANCIA = {
    "open": 2.000,
    "box":  1.473,
}


def _exponente_x(config: str) -> float:
    return _X_DISTANCIA.get(config.lower(), _X_DISTANCIA["open"])

# Energía de inicio de quemadura 2° grado — IEEE 1584-2002 §4.10 / NFPA 70E
_EI_DEFAULT_CAL_CM2 = 1.2

# Umbrales de categoría PPE — NFPA 70E:2024 Tabla 130.5(G)
_CAT_PPE = [
    (1.2,  0),    # < 1.2 cal/cm²  → Cat 0 (no requiere PPE arco)
    (4.0,  1),    # 1.2–4.0        → Cat 1
    (8.0,  2),    # 4.0–8.0        → Cat 2
    (25.0, 3),    # 8.0–25.0       → Cat 3
    (40.0, 4),    # 25.0–40.0      → Cat 4
    # ≥ 40 → PELIGRO, sin categoría
]

_NORMA_CALCULO = "IEEE 1584-2002 / NFPA 70E:2024"


# ============================================================
# API PÚBLICA
# ============================================================

def calcular_corriente_arco(
    Ibf_kA: float,
    V_kV: float,
    G_mm: float,
    config: str = "open",
) -> dict:
    """Corriente de arco eléctrico por método empírico IEEE 1584-2002.

    Ecuación §4.2: log(Ia) = K + 0.662×log(Ibf) + 0.0966×V
                             + 0.000526×G + 0.5588×V×log(Ibf)
                             − 0.00304×G×log(Ibf)

    Parámetros:
        Ibf_kA : corriente de falla bolted en kA
        V_kV   : tensión de sistema en kV
        G_mm   : separación entre conductores en mm
        config : "open" (bus abierto) | "box" (gabinete)

    Retorna dict con Ia_kA, Ibf_kA, V_kV, G_mm, config, norma.
    """
    if float(Ibf_kA) <= 0:
        raise ValueError(f"Ibf_kA debe ser > 0, se recibió {Ibf_kA}")

    # K depende de configuración — IEEE 1584-2002 §4.2
    K = -0.153 if config.lower() == "open" else -0.097

    ibf = float(Ibf_kA)
    v = float(V_kV)
    g = float(G_mm)

    log_ia = (
        K
        + 0.662 * math.log10(ibf)
        + 0.0966 * v
        + 0.000526 * g
        + 0.5588 * v * math.log10(ibf)
        - 0.00304 * g * math.log10(ibf)
    )
    ia_kA = round(10 ** log_ia, 4)

    return {
        "Ia_kA":   ia_kA,
        "Ibf_kA":  ibf,
        "V_kV":    v,
        "G_mm":    g,
        "config":  config.lower(),
        "norma":   _NORMA_CALCULO,
    }


def calcular_energia_incidente(
    Ia_kA: float,
    t_s: float,
    D_mm: float,
    V_kV: float,
    G_mm: float,
    config: str = "open",
) -> dict:
    """Energía incidente en cal/cm² — IEEE 1584-2002 §4.7.

    Pasos:
      1. En normalizada: log(En) = K1 + K2 + 1.081×log(Ia) + 0.0011×G
      2. E = 4.184 × Cf × En × (t / 0.2) × (610 / D)^x

    Parámetros:
        Ia_kA  : corriente de arco en kA
        t_s    : tiempo de despeje del arco en segundos
        D_mm   : distancia de trabajo en mm
        V_kV   : tensión del sistema en kV
        G_mm   : separación entre conductores en mm
        config : "open" | "box"
    """
    if float(Ia_kA) <= 0:
        raise ValueError(f"Ia_kA debe ser > 0, se recibió {Ia_kA}")
    if float(t_s) < 0:
        raise ValueError(f"t_s (tiempo de despeje) no puede ser negativo, se recibió {t_s}")
    if float(D_mm) <= 0:
        raise ValueError(f"D_mm (distancia de trabajo) debe ser > 0, se recibió {D_mm}")

    # K1 — IEEE 1584-2002 §4.5 (en función de configuración)
    K1 = -0.792 if config.lower() == "open" else -0.555
    # K2 — §4.5 (grounding; usamos neutro solidamente puesto a tierra como conservador)
    K2 = -0.113

    ia = float(Ia_kA)
    t = float(t_s)
    d = float(D_mm)
    g = float(G_mm)
    v = float(V_kV)

    Cf = _CF_BT if v <= 1.0 else _CF_MT
    x = _exponente_x(config)

    log_en = K1 + K2 + 1.081 * math.log10(ia) + 0.0011 * g
    En = 10 ** log_en  # cal/cm² a t=0.2s, D=610mm

    E = 4.184 * Cf * En * (t / 0.2) * (_D_REF_MM / d) ** x
    E = round(E, 4)

    return {
        "E_cal_cm2":   E,
        "En_cal_cm2":  round(En, 6),
        "Cf":          Cf,
        "x_distancia": x,
        "t_s":         t,
        "D_mm":        d,
        "Ia_kA":       ia,
        "norma":       _NORMA_CALCULO,
    }


def calcular_frontera_arco(
    Ia_kA: float,
    t_s: float,
    V_kV: float,
    G_mm: float,
    Ei_cal_cm2: float = _EI_DEFAULT_CAL_CM2,
    config: str = "open",
) -> dict:
    """Distancia de frontera de arco (AFB) en mm — IEEE 1584-2002 §4.9.

    AFB es la distancia a la que la energía incidente iguala Ei (umbral de
    quemadura de segundo grado). La distancia de trabajo debe ser ≥ AFB.

    D_afb = 610 × (4.184 × Cf × En × (t/0.2) / Ei)^(1/x)
    """
    if float(Ia_kA) <= 0:
        raise ValueError(f"Ia_kA debe ser > 0, se recibió {Ia_kA}")
    if float(Ei_cal_cm2) <= 0:
        raise ValueError(f"Ei_cal_cm2 (umbral) debe ser > 0, se recibió {Ei_cal_cm2}")

    ia = float(Ia_kA)
    t = float(t_s)
    v = float(V_kV)
    g = float(G_mm)
    ei = float(Ei_cal_cm2)

    K1 = -0.792 if config.lower() == "open" else -0.555
    K2 = -0.113
    Cf = _CF_BT if v <= 1.0 else _CF_MT
    x = _exponente_x(config)

    log_en = K1 + K2 + 1.081 * math.log10(ia) + 0.0011 * g
    En = 10 ** log_en

    argumento = 4.184 * Cf * En * (t / 0.2) / ei
    if argumento <= 0:
        D_afb = 0.0
    else:
        D_afb = _D_REF_MM * (argumento ** (1.0 / x))

    return {
        "D_afb_mm":    round(D_afb, 1),
        "Ia_kA":       ia,
        "t_s":         t,
        "Ei_cal_cm2":  ei,
        "norma":       _NORMA_CALCULO,
    }


def categoria_ppe(E_cal_cm2: float) -> dict:
    """Categoría de EPP (Equipo de Protección Personal) según NFPA 70E:2024.

    Retorna:
        categoria : int (0–4) | None (≥ 40 cal/cm² → PELIGRO)
        estado    : str
        E_cal_cm2 : float
        norma     : str
    """
    e = float(E_cal_cm2)

    if e < 1.2:
        return {
            "categoria":  0,
            "E_cal_cm2":  e,
            "estado":     "Cat 0 — riesgo mínimo (<1.2 cal/cm²)",
            "norma":      "NFPA 70E:2024 Tabla 130.5(G)",
        }

    for umbral, cat in _CAT_PPE[1:]:
        if e < umbral:
            return {
                "categoria":  cat,
                "E_cal_cm2":  e,
                "estado":     f"Cat {cat} — {e:.2f} cal/cm²",
                "norma":      "NFPA 70E:2024 Tabla 130.5(G)",
            }

    # ≥ 40 cal/cm²
    return {
        "categoria":  None,
        "E_cal_cm2":  e,
        "estado":     f"PELIGRO — {e:.2f} cal/cm² excede Cat 4 (40 cal/cm²); prohibido trabajar energizado",
        "norma":      "NFPA 70E:2024 Tabla 130.5(G)",
    }


def calcular_arc_flash_completo(
    Ibf_kA: float,
    V_kV: float,
    G_mm: float,
    t_s: float,
    D_mm: float,
    config: str = "open",
    Ei_cal_cm2: float = _EI_DEFAULT_CAL_CM2,
) -> dict:
    """Cálculo completo de Arc Flash en un paso.

    Ejecuta: corriente_arco → energía_incidente → frontera → categoría_PPE.

    Retorna dict consolidado con todos los resultados.
    """
    ia_res = calcular_corriente_arco(Ibf_kA, V_kV, G_mm, config)
    Ia = ia_res["Ia_kA"]

    e_res = calcular_energia_incidente(Ia, t_s, D_mm, V_kV, G_mm, config)
    E = e_res["E_cal_cm2"]

    afb_res = calcular_frontera_arco(Ia, t_s, V_kV, G_mm, Ei_cal_cm2, config)
    ppe_res = categoria_ppe(E)

    return {
        "Ibf_kA":       float(Ibf_kA),
        "Ia_kA":        Ia,
        "E_cal_cm2":    E,
        "En_cal_cm2":   e_res["En_cal_cm2"],
        "D_afb_mm":     afb_res["D_afb_mm"],
        "t_s":          float(t_s),
        "D_mm":         float(D_mm),
        "Cf":           e_res["Cf"],
        "categoria_ppe": ppe_res["categoria"],
        "estado_ppe":   ppe_res["estado"],
        "norma":        _NORMA_CALCULO,
    }


def arc_flash_desde_proteccion(
    Ibf_kA: float,
    V_kV: float,
    In_A: float,
    curva: str,
    *,
    G_mm: float = 32.0,
    D_mm: float = 455.0,
    config: str = "box",
    t_techo_s: float = 2.0,
) -> dict:
    """Arc Flash con tiempo de despeje evaluado en la corriente de arco Ia.

    La corriente de arco Ia es menor que la de falla franca Ibf, por lo que la
    protección puede tardar más en despejar (IEEE 1584 exige evaluar en Ia).

    Resolución del tiempo según la región de disparo a Ia:
      instantaneo / termico / tiempo_corto / idmt -> t del dispositivo
      verificar_simaris (ETU propietaria)          -> t_techo + bandera verificar_simaris
      no_dispara / t indefinido                    -> t_techo + bandera despeje_incierto

    Defaults G/D/config: típicos IEEE 1584-2002 para tablero BT cerrado.
    """
    ia_res = calcular_corriente_arco(Ibf_kA, V_kV, G_mm, config)
    Ia_kA = ia_res["Ia_kA"]

    disp = coordinacion.calcular_tiempo_disparo(Ia_kA * 1000.0, In_A, curva)
    region = disp["region"]
    despeje_incierto = False
    verificar_simaris = False

    if region in ("instantaneo", "termico", "tiempo_corto", "idmt"):
        t = disp["t_s"]
    elif region == "verificar_simaris":
        t = t_techo_s
        verificar_simaris = True
    else:  # no_dispara u otro
        t = t_techo_s
        despeje_incierto = True

    if t is None:  # dispara pero sin tiempo determinado (defensivo)
        t = t_techo_s
        despeje_incierto = True

    af = calcular_arc_flash_completo(
        Ibf_kA, V_kV, G_mm, t_s=float(t), D_mm=D_mm, config=config
    )

    return {
        "Ibf_kA":            float(Ibf_kA),
        "Ia_kA":             Ia_kA,
        "t_despeje_s":       round(float(t), 4),
        "region_despeje":    region,
        "E_cal_cm2":         af["E_cal_cm2"],
        "D_afb_mm":          af["D_afb_mm"],
        "categoria_ppe":     af["categoria_ppe"],
        "estado_ppe":        af["estado_ppe"],
        "despeje_incierto":  despeje_incierto,
        "verificar_simaris": verificar_simaris,
        "norma":             af["norma"],
    }
