# ============================================================
# demanda.py
# Responsabilidad: cálculo de demanda máxima y dimensionamiento
#                  de alimentador principal y transformador
# Normativa: RIC N°03 (SEC) / IEC 60076 / IEC 60364-4-41
# Razón para cambiar: nuevos factores de demanda o normativa
# ============================================================

import math

# ============================================================
# FACTORES DE DEMANDA — RIC N°03 + práctica SEC Chile
# Estructura: (tipo_instalacion, tipo_carga) → Fd
# ============================================================

FACTORES_DEMANDA = {
    # --- RESIDENCIAL ---
    ("residencial", "alumbrado"):      0.66,
    ("residencial", "tomacorriente"):  0.50,
    ("residencial", "climatizacion"):  1.00,
    ("residencial", "fuerza"):         1.00,
    ("residencial", "critica"):        1.00,

    # --- COMERCIAL ---
    ("comercial", "alumbrado"):        0.75,
    ("comercial", "iluminacion"):      0.75,
    ("comercial", "tomacorriente"):    0.60,
    ("comercial", "climatizacion"):    1.00,
    ("comercial", "hvac"):             0.85,
    ("comercial", "fuerza"):           0.85,
    ("comercial", "motor"):            0.75,
    ("comercial", "critica"):          1.00,

    # --- INDUSTRIAL ---
    ("industrial", "alumbrado"):       1.00,
    ("industrial", "iluminacion"):     1.00,
    ("industrial", "tomacorriente"):   0.50,
    ("industrial", "climatizacion"):   1.00,
    ("industrial", "hvac"):            1.00,
    ("industrial", "fuerza"):          1.00,
    ("industrial", "motor"):           0.75,
    ("industrial", "critica"):         1.00,

    # --- DATACENTER (cargas críticas 24/7) ---
    ("datacenter", "critica"):         1.00,
    ("datacenter", "hvac"):            1.00,
    ("datacenter", "iluminacion"):     1.00,
    ("datacenter", "alumbrado"):       1.00,
    ("datacenter", "tomacorriente"):   0.50,
    ("datacenter", "motor"):           1.00,
    ("datacenter", "ups"):             1.00,
}

# Fallback cuando no se encuentra la combinación exacta
FD_DEFAULT = 1.00   # criterio conservador

# Potencias nominales estándar de transformadores IEC 60076 (kVA)
POTENCIAS_TRAFO_IEC = [
    50, 100, 160, 200, 250, 315, 400,
    500, 630, 800, 1000, 1250, 1600, 2000,
    2500, 3150, 4000, 5000, 6300
]

# Umbral de uso operacional del transformador
USO_TRAFO_OPTIMO = 0.80   # 80% — recomendación operacional IEC 60076

# Corrientes Icc de empalme SEC por zona (kA) — tabla referencial SEC
ICC_EMPALME_SEC = {
    "urbana":    6.0,
    "suburbana": 4.0,
    "rural":     2.0,
}


# ============================================================
# FUNCIONES PRINCIPALES
# ============================================================

def obtener_fd(tipo_instalacion, tipo_carga):
    """
    Retorna el factor de demanda para una combinación
    de tipo de instalación y tipo de carga.

    Insensible a mayúsculas. Retorna FD_DEFAULT=1.0
    si la combinación no está en la tabla (conservador).

    Parámetros:
        tipo_instalacion : str — residencial/comercial/industrial/datacenter
        tipo_carga       : str — alumbrado/iluminacion/tomacorriente/
                                  hvac/motor/critica/fuerza/ups

    Retorna:
        float — factor de demanda entre 0 y 1
    """
    ti = str(tipo_instalacion).strip().lower()
    tc = str(tipo_carga).strip().lower()
    return FACTORES_DEMANDA.get((ti, tc), FD_DEFAULT)


def calcular_potencia_circuito(I_diseno, cos_phi, sistema, Vn):
    """
    Calcula potencia activa (kW) y aparente (kVA) de un circuito.

    Parámetros:
        I_diseno : float — corriente de diseño en A
        cos_phi  : float — factor de potencia
        sistema  : str   — "1F", "2F", "3F"
        Vn       : float — tensión nominal en V

    Retorna:
        (P_kw, S_kva) — tupla de floats
    """
    if sistema == "3F":
        P_w  = 1.732 * Vn * I_diseno * cos_phi
        S_va = 1.732 * Vn * I_diseno
    else:
        P_w  = Vn * I_diseno * cos_phi
        S_va = Vn * I_diseno

    return round(P_w / 1000, 3), round(S_va / 1000, 3)


def calcular_demanda(circuitos, balance_datos, params_demanda):
    """
    Calcula la demanda máxima de la instalación aplicando
    factores de demanda según RIC N°03.

    Parámetros:
        circuitos      : lista de circuitos (de leer_circuitos_excel)
        balance_datos  : dict {nombre: {tablero, fase, tipo_carga}}
        params_demanda : dict con:
            tipo_instalacion : str
            cos_phi_global   : float
            factor_crecimiento: float
            tension_alim     : float
            sistema_alim     : str ("1F" o "3F")

    Retorna:
        dict con detalle por circuito y resumen total
    """
    from conductores import TENSION_SISTEMA

    tipo_inst   = params_demanda.get("tipo_instalacion", "industrial")
    cos_phi_gl  = params_demanda.get("cos_phi_global", 0.85)
    f_crec      = params_demanda.get("factor_crecimiento", 1.0)
    Vn_alim     = params_demanda.get("tension_alim", 380)
    sis_alim    = params_demanda.get("sistema_alim", "3F")

    # Índice de circuitos por nombre
    circ_idx = {c["nombre"]: c for c in circuitos}

    detalle     = []
    S_total_kva = 0.0
    P_total_kw  = 0.0

    for nombre, bd in balance_datos.items():
        if nombre not in circ_idx:
            continue

        c          = circ_idx[nombre]
        tipo_carga = bd.get("tipo_carga", "critica")
        Vn         = TENSION_SISTEMA.get(c["sistema"], 380)

        # Potencia instalada del circuito
        P_kw, S_kva = calcular_potencia_circuito(
            c["I_diseno"], c["cos_phi"], c["sistema"], Vn
        )

        # Factor de demanda según tipo de instalación y carga
        Fd = obtener_fd(tipo_inst, tipo_carga)

        # Demanda del circuito
        P_dem_kw  = round(P_kw  * Fd, 3)
        S_dem_kva = round(S_kva * Fd, 3)

        detalle.append({
            "nombre":      nombre,
            "sistema":     c["sistema"],
            "tipo_carga":  tipo_carga,
            "Fd":          Fd,
            "P_inst_kw":   P_kw,
            "S_inst_kva":  S_kva,
            "P_dem_kw":    P_dem_kw,
            "S_dem_kva":   S_dem_kva,
        })

        P_total_kw  = round(P_total_kw  + P_dem_kw,  3)
        S_total_kva = round(S_total_kva + S_dem_kva, 3)

    # Corriente del alimentador principal
    I_alim = calcular_corriente_alimentador(S_total_kva, Vn_alim, sis_alim)

    # Con factor de crecimiento
    S_futuro_kva = round(S_total_kva * f_crec, 2)
    I_futuro     = calcular_corriente_alimentador(S_futuro_kva, Vn_alim, sis_alim)

    return {
        "tipo_instalacion":  tipo_inst,
        "detalle":           detalle,
        "P_total_kw":        P_total_kw,
        "S_total_kva":       S_total_kva,
        "I_alim_A":          I_alim,
        "factor_crecimiento": f_crec,
        "S_futuro_kva":      S_futuro_kva,
        "I_futuro_A":        I_futuro,
        "Vn_alim":           Vn_alim,
        "sistema_alim":      sis_alim,
        "cos_phi_global":    cos_phi_gl,
    }


def calcular_corriente_alimentador(S_kva, Vn, sistema):
    """
    Calcula la corriente del alimentador principal.

    Parámetros:
        S_kva   : float — potencia aparente en kVA
        Vn      : float — tensión nominal en V
        sistema : str   — "1F" o "3F"

    Retorna:
        float — corriente en A, redondeada a 1 decimal
    """
    if S_kva <= 0 or Vn <= 0:
        return 0.0
    if sistema == "3F":
        I = (S_kva * 1000) / (1.732 * Vn)
    else:
        I = (S_kva * 1000) / Vn
    return round(I, 1)


def seleccionar_transformador(S_demanda_kva, factor_uso=USO_TRAFO_OPTIMO):
    """
    Selecciona el transformador estándar IEC 60076 mínimo
    que cubre la demanda con el margen de uso indicado.

    Parámetros:
        S_demanda_kva : float — demanda total en kVA
        factor_uso    : float — fracción de uso objetivo (default 0.80)

    Retorna:
        dict con kVA_minimo, kVA_seleccionado, uso_pct, estado
    """
    if S_demanda_kva <= 0:
        return {
            "kVA_minimo":      0,
            "kVA_seleccionado": POTENCIAS_TRAFO_IEC[0],
            "uso_pct":         0.0,
            "estado":          "Sin demanda calculada",
        }

    kVA_minimo = S_demanda_kva / factor_uso

    # Seleccionar el primer estándar IEC que supera el mínimo
    kVA_sel = None
    for kVA in POTENCIAS_TRAFO_IEC:
        if kVA >= kVA_minimo:
            kVA_sel = kVA
            break

    if kVA_sel is None:
        kVA_sel = POTENCIAS_TRAFO_IEC[-1]
        estado  = "FALLA — supera la tabla IEC. Consultar al fabricante."
    else:
        uso_pct = round(S_demanda_kva / kVA_sel * 100, 1)
        if uso_pct > 100:
            estado = "FALLA — supera capacidad nominal"
        elif uso_pct > 90:
            estado = "PRECAUCIÓN — sobre 90%"
        elif uso_pct > USO_TRAFO_OPTIMO * 100:
            estado = "PRECAUCIÓN — supera 80%"
        else:
            estado = "OK"

    uso_pct = round(S_demanda_kva / kVA_sel * 100, 1)

    return {
        "kVA_minimo":       round(kVA_minimo, 1),
        "kVA_seleccionado": kVA_sel,
        "uso_pct":          uso_pct,
        "estado":           estado,
    }


def dimensionar_acometida_sec(S_demanda_kva, Vn, sistema, zona="urbana"):
    """
    Dimensiona la acometida SEC cuando no hay transformador propio.

    Parámetros:
        S_demanda_kva : float — demanda total en kVA
        Vn            : float — tensión nominal en V
        sistema       : str   — "1F" o "3F"
        zona          : str   — "urbana" / "suburbana" / "rural"

    Retorna:
        dict con corriente, Icc del empalme, protección mínima
    """
    I_alim  = calcular_corriente_alimentador(S_demanda_kva, Vn, sistema)
    Icc_kA  = ICC_EMPALME_SEC.get(zona, 6.0)

    # Protección mínima según RIC N°03 — 125% de la corriente de diseño
    I_prot_min = round(I_alim * 1.25, 1)

    return {
        "I_alim_A":    I_alim,
        "Icc_kA":      Icc_kA,
        "zona":        zona,
        "I_prot_min_A": I_prot_min,
        "nota": (
            f"Protección mínima {I_prot_min} A | "
            f"Poder de corte mínimo {Icc_kA} kA "
            f"(empalme SEC zona {zona})"
        ),
    }


def reporte_demanda(resultado_demanda, resultado_trafo=None,
                    resultado_sec=None):
    """
    Genera líneas del reporte de demanda.
    Retorna lista de strings.
    """
    lineas = []
    r = resultado_demanda

    lineas.append("=" * 60)
    lineas.append("  DEMANDA MÁXIMA Y DIMENSIONAMIENTO — M6")
    lineas.append(f"  Tipo de instalación : {r['tipo_instalacion'].upper()}")
    lineas.append(f"  Normativa           : RIC N°03 SEC / IEC 60076")
    lineas.append("=" * 60)

    # Tabla detallada
    lineas.append("")
    lineas.append("  DETALLE POR CIRCUITO")
    lineas.append("-" * 60)
    lineas.append(
        f"  {'Circuito':<25} {'Tipo':<15} {'Fd':>4} "
        f"{'P_inst':>8} {'P_dem':>8}"
    )
    lineas.append("-" * 60)

    for d in r["detalle"]:
        lineas.append(
            f"  {d['nombre']:<25} {d['tipo_carga']:<15} "
            f"{d['Fd']:>4.2f} "
            f"{d['P_inst_kw']:>7.2f}kW "
            f"{d['P_dem_kw']:>7.2f}kW"
        )

    lineas.append("-" * 60)
    lineas.append(f"  {'TOTAL':>45} {r['P_total_kw']:>7.2f}kW")
    lineas.append("")

    # Resumen ejecutivo
    lineas.append("  RESUMEN EJECUTIVO")
    lineas.append("-" * 60)
    lineas.append(f"  Demanda total      : {r['S_total_kva']} kVA "
                  f"({r['P_total_kw']} kW)")
    lineas.append(f"  Corriente alim.    : {r['I_alim_A']} A "
                  f"({r['sistema_alim']} / {r['Vn_alim']} V)")
    lineas.append(f"  Factor crecimiento : ×{r['factor_crecimiento']}")
    lineas.append(f"  Demanda futura     : {r['S_futuro_kva']} kVA "
                  f"→ {r['I_futuro_A']} A")

    # Transformador
    if resultado_trafo:
        lineas.append("")
        lineas.append("  SELECCIÓN TRANSFORMADOR")
        lineas.append("-" * 60)
        t = resultado_trafo
        lineas.append(f"  kVA mínimo requerido : {t['kVA_minimo']} kVA")
        lineas.append(f"  kVA seleccionado     : {t['kVA_seleccionado']} kVA "
                      f"(estándar IEC 60076)")
        lineas.append(f"  Uso del transformador: {t['uso_pct']}% "
                      f"→ {t['estado']}")

    # Acometida SEC
    if resultado_sec:
        lineas.append("")
        lineas.append("  ACOMETIDA SEC")
        lineas.append("-" * 60)
        s = resultado_sec
        lineas.append(f"  Corriente alimentador: {s['I_alim_A']} A")
        lineas.append(f"  Icc empalme SEC      : {s['Icc_kA']} kA "
                      f"(zona {s['zona']})")
        lineas.append(f"  Protección mínima    : {s['I_prot_min_A']} A "
                      f"(125% I_alim — RIC N°03)")

    lineas.append("=" * 60)
    return lineas
