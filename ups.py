# ============================================================
# CONSTANTES - clasificacion por origen
# TIPO A: parametro de proyecto - DEBE ser ingresado por usuario
# TIPO B: constante normada - no modificar sin cambiar norma
# TIPO C: criterio de diseno - cambiar solo con justificacion
# ============================================================

AUTONOMIA_MINIMA_MIN = {
    "tier1": 10,  # TIPO B - TIA-942 referencia minima por criticidad
    "tier2": 10,  # TIPO B - TIA-942 referencia minima por criticidad
    "tier3": 15,  # TIPO B - TIA-942 referencia minima por criticidad
    "tier4": 15,  # TIPO B - TIA-942 referencia minima por criticidad
    "critico": 15,  # TIPO B - ANSI/BICSI 002 criterio para infraestructura critica
    "general": 10,  # TIPO B - IEC 62040-4 referencia para aplicaciones generales
}

AUTONOMIA_ALERTA_MIN = 10  # TIPO C - umbral interno de alerta operativa
AUTONOMIA_WARNING_MIN = 15  # TIPO C - umbral interno de warning

TIPO_UPS = {
    "VFI": "Doble conversion - tension y frecuencia independientes",
    "VI": "Line-interactive - tension regulada",
    "VFD": "Standby - solo actua en falla",
}

ETA_UPS_DEFAULT = 0.94  # TIPO C - valor tipico de eficiencia UPS online
ETA_BAT_DEFAULT = 0.85  # TIPO C - valor tipico de eficiencia del banco
FACTOR_USO_MAX_UPS = 0.80  # TIPO C - criterio conservador de operacion continua

FACTOR_TEMP_BAT = {
    20: 1.03,
    25: 1.00,
    30: 0.97,
    35: 0.94,
    40: 0.90,
}


def _factor_temp_bat(temperatura: float) -> float:
    t = float(temperatura)
    keys = sorted(FACTOR_TEMP_BAT.keys())
    if t <= keys[0]:
        return FACTOR_TEMP_BAT[keys[0]]
    if t >= keys[-1]:
        return FACTOR_TEMP_BAT[keys[-1]]
    for i in range(len(keys) - 1):
        t0, t1 = keys[i], keys[i + 1]
        if t0 <= t <= t1:
            f0 = FACTOR_TEMP_BAT[t0]
            f1 = FACTOR_TEMP_BAT[t1]
            frac = (t - t0) / (t1 - t0)
            return round(f0 + (f1 - f0) * frac, 4)
    return FACTOR_TEMP_BAT[25]


def verificar_capacidad_ups(
    P_carga_kVA: float,
    P_ups_kVA: float,
    factor_uso_max: float = FACTOR_USO_MAX_UPS
) -> dict:
    p_carga = float(P_carga_kVA)
    p_ups = max(float(P_ups_kVA), 1e-9)
    uso_pct = (p_carga / p_ups) * 100.0
    limite_pct = float(factor_uso_max) * 100.0
    ok = uso_pct <= limite_pct
    margen = (p_ups * float(factor_uso_max)) - p_carga
    return {
        "uso_pct": round(uso_pct, 3),
        "margen_kVA": round(margen, 3),
        "ok": ok,
        "observacion": "OK" if ok else "Capacidad UPS excedida sobre limite operativo",
    }


def calcular_banco_baterias(
    n_baterias_serie: int,
    V_bat_unitaria: float,
    Ah_bat: float,
    n_strings: int,
    temperatura: float = 25.0,
    eta_bat: float = ETA_BAT_DEFAULT
) -> dict:
    n_serie = max(int(n_baterias_serie), 1)
    n_str = max(int(n_strings), 1)
    v_unit = float(V_bat_unitaria)
    ah = float(Ah_bat)
    eta = float(eta_bat)

    v_string = n_serie * v_unit
    ah_total = ah * n_str
    f_temp = _factor_temp_bat(temperatura)
    ah_ef = ah_total * f_temp * eta
    e_kwh = (v_string * ah_ef) / 1000.0

    return {
        "V_string": round(v_string, 3),
        "Ah_total": round(ah_total, 3),
        "Ah_efectivo": round(ah_ef, 3),
        "E_kWh": round(e_kwh, 3),
        "factor_temp": round(f_temp, 4),
    }


def calcular_autonomia(
    P_carga_kW: float,
    E_bat_kWh: float,
    eta_ups: float = ETA_UPS_DEFAULT,
    nivel_infraestructura: str = "critico"
) -> dict:
    p_carga = max(float(P_carga_kW), 1e-9)
    e_kwh = max(float(E_bat_kWh), 0.0)
    eta = max(float(eta_ups), 1e-9)

    p_bat = p_carga / eta
    t_hr = e_kwh / p_bat if p_bat > 0 else 0.0
    t_min = t_hr * 60.0

    nivel = str(nivel_infraestructura or "general").lower()
    t_minimo = AUTONOMIA_MINIMA_MIN.get(nivel, AUTONOMIA_MINIMA_MIN["general"])
    if nivel in ("tier3", "tier4", "tier2", "tier1"):
        norma = "TIA-942"
    elif nivel == "critico":
        norma = "ANSI/BICSI 002"
    else:
        norma = "IEC 62040-4"

    if t_min >= t_minimo:
        estado = "OK"
    elif t_min >= AUTONOMIA_ALERTA_MIN:
        estado = "WARNING"
    else:
        estado = "INSUFICIENTE"

    return {
        "P_baterias_kW": round(p_bat, 3),
        "t_min": round(t_min, 3),
        "t_minimo_normado": int(t_minimo),
        "estado": estado,
        "norma_aplicada": norma,
    }


def calcular_tiempo_recarga(
    Ah_efectivo: float,
    P_ups_kVA: float,
    V_string: float,
    eta_ups: float = ETA_UPS_DEFAULT
) -> dict:
    ah_ef = max(float(Ah_efectivo), 0.0)
    p_ups = max(float(P_ups_kVA), 1e-9)
    v_string = max(float(V_string), 1e-9)
    eta = max(float(eta_ups), 1e-9)

    i_carga = (p_ups * 1000.0 * eta) / v_string
    t_rec = (ah_ef * 10.0) / max(i_carga, 1e-9)
    ok = t_rec <= 12.0
    return {
        "I_carga_A": round(i_carga, 3),
        "t_recarga_hr": round(t_rec, 3),
        "ok": ok,
        "norma": "IEC 62040-4",
    }


def verificar_tipo_ups(
    tipo: str,
    tipo_carga: str
) -> dict:
    t = str(tipo or "").upper()
    tipo_desc = TIPO_UPS.get(t, "Tipo no identificado")
    carga = str(tipo_carga or "general").lower()

    if carga in ("it", "critico"):
        ok = t == "VFI"
    else:
        ok = t in TIPO_UPS

    obs = "OK" if ok else "Carga IT/critica requiere UPS VFI"
    return {
        "tipo_descripcion": tipo_desc,
        "ok_para_carga": ok,
        "observacion": obs,
    }


def calcular_ups(
    nombre: str,
    modelo_ups: str,
    tipo_ups: str,
    P_ups_kVA: float,
    V_nominal: float,
    P_carga_kW: float,
    cos_phi_carga: float,
    tipo_carga: str,
    nivel_infraestructura: str,
    n_baterias_serie: int,
    V_bat_unitaria: float,
    Ah_bat: float,
    n_strings: int,
    temperatura: float = 25.0,
    eta_ups: float = ETA_UPS_DEFAULT,
    eta_bat: float = ETA_BAT_DEFAULT
) -> dict:
    p_kva_carga = float(P_carga_kW) / max(float(cos_phi_carga), 1e-9)
    capacidad = verificar_capacidad_ups(p_kva_carga, P_ups_kVA, factor_uso_max=FACTOR_USO_MAX_UPS)
    banco = calcular_banco_baterias(
        n_baterias_serie=n_baterias_serie,
        V_bat_unitaria=V_bat_unitaria,
        Ah_bat=Ah_bat,
        n_strings=n_strings,
        temperatura=temperatura,
        eta_bat=eta_bat,
    )
    autonomia = calcular_autonomia(
        P_carga_kW=P_carga_kW,
        E_bat_kWh=banco["E_kWh"],
        eta_ups=eta_ups,
        nivel_infraestructura=nivel_infraestructura,
    )
    recarga = calcular_tiempo_recarga(
        Ah_efectivo=banco["Ah_efectivo"],
        P_ups_kVA=P_ups_kVA,
        V_string=banco["V_string"],
        eta_ups=eta_ups,
    )
    tipo = verificar_tipo_ups(tipo=tipo_ups, tipo_carga=tipo_carga)

    return {
        "nombre": str(nombre),
        "modelo_ups": str(modelo_ups),
        "tipo_ups": str(tipo_ups).upper(),
        "P_ups_kVA": float(P_ups_kVA),
        "V_nominal": float(V_nominal),
        "P_carga_kW": float(P_carga_kW),
        "P_carga_kVA": round(p_kva_carga, 3),
        "cos_phi_carga": float(cos_phi_carga),
        "tipo_carga": str(tipo_carga).lower(),
        "nivel_infraestructura": str(nivel_infraestructura).lower(),
        "n_baterias_serie": int(n_baterias_serie),
        "V_bat_unitaria": float(V_bat_unitaria),
        "Ah_bat": float(Ah_bat),
        "n_strings": int(n_strings),
        "temperatura": float(temperatura),
        "eta_ups": float(eta_ups),
        "eta_bat": float(eta_bat),
        "capacidad": capacidad,
        "banco_baterias": banco,
        "autonomia": autonomia,
        "recarga": recarga,
        "tipo_validacion": tipo,
    }
