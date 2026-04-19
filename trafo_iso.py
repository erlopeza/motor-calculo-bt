import math


FACTOR_USO_MAX_TRAFO = 0.80
UCC_DEFAULT_PCT = 5.0
TOLERANCIA_UCC_PCT = 7.5


def verificar_capacidad_trafo(
    P_carga_kVA: float,
    P_trafo_kVA: float,
    factor_uso_max: float = FACTOR_USO_MAX_TRAFO
) -> dict:
    p_carga = float(P_carga_kVA)
    p_trafo = max(float(P_trafo_kVA), 1e-9)
    uso_pct = (p_carga / p_trafo) * 100.0
    limite_pct = float(factor_uso_max) * 100.0
    ok = uso_pct <= limite_pct
    margen = (p_trafo * float(factor_uso_max)) - p_carga
    return {
        "P_trafo_kVA": round(p_trafo, 3),
        "uso_pct": round(uso_pct, 3),
        "margen_kVA": round(margen, 3),
        "ok": ok,
        "observacion": "OK" if ok else "Capacidad de trafo de aislamiento excedida",
    }


def calcular_corriente_nominal(
    P_kVA: float,
    V_nominal: float,
    sistema: str = "3F"
) -> float:
    p = float(P_kVA) * 1000.0
    v = max(float(V_nominal), 1e-9)
    if str(sistema).upper() == "3F":
        i = p / (math.sqrt(3.0) * v)
    else:
        i = p / v
    return round(i, 3)


def calcular_icc_secundario(
    P_kVA: float,
    V_nominal: float,
    Ucc_pct: float = UCC_DEFAULT_PCT
) -> dict:
    i_nom = calcular_corriente_nominal(P_kVA, V_nominal, sistema="3F")
    ucc = max(float(Ucc_pct), 1e-9)
    i_cc_nom = i_nom / (ucc / 100.0)
    i_cc_max = i_cc_nom / (1.0 - (TOLERANCIA_UCC_PCT / 100.0))
    i_cc_min = i_cc_nom / (1.0 + (TOLERANCIA_UCC_PCT / 100.0))
    return {
        "Icc_nominal_kA": round(i_cc_nom / 1000.0, 3),
        "Icc_max_kA": round(i_cc_max / 1000.0, 3),
        "Icc_min_kA": round(i_cc_min / 1000.0, 3),
        "Ucc_pct": round(ucc, 3),
    }


def calcular_dv_trafo(
    P_carga_kVA: float,
    P_trafo_kVA: float,
    Ucc_pct: float = UCC_DEFAULT_PCT,
    cos_phi: float = 0.9
) -> dict:
    p_carga = float(P_carga_kVA)
    p_trafo = max(float(P_trafo_kVA), 1e-9)
    ucc = float(Ucc_pct)
    fp = float(cos_phi)
    dv_pct = (p_carga / p_trafo) * ucc * fp
    ok = dv_pct <= 3.0
    return {
        "dv_pct": round(dv_pct, 3),
        "ok": ok,
    }


def calcular_trafo_iso(
    nombre: str,
    P_trafo_kVA: float,
    V_primario: float,
    V_secundario: float,
    conexion: str,
    P_carga_kVA: float,
    cos_phi: float = 0.9,
    Ucc_pct: float = UCC_DEFAULT_PCT,
    n_trafos: int = 1,
    modo: str = "servicio"
) -> dict:
    n = max(int(n_trafos), 1)
    p_unit = float(P_trafo_kVA)
    p_ef = p_unit * n

    capacidad = verificar_capacidad_trafo(P_carga_kVA, p_ef, factor_uso_max=FACTOR_USO_MAX_TRAFO)
    i_nom_sec = calcular_corriente_nominal(p_ef, V_secundario, sistema="3F")
    icc = calcular_icc_secundario(p_ef, V_secundario, Ucc_pct=Ucc_pct)
    dv = calcular_dv_trafo(P_carga_kVA, p_ef, Ucc_pct=Ucc_pct, cos_phi=cos_phi)

    obs_cfg = "Unidad simple"
    if n > 1:
        obs_cfg = "Configuracion multiple (paralelo o redundancia)"

    return {
        "nombre": str(nombre),
        "P_trafo_kVA": p_unit,
        "P_total_kVA": round(p_ef, 3),
        "V_primario": float(V_primario),
        "V_secundario": float(V_secundario),
        "conexion": str(conexion),
        "P_carga_kVA": float(P_carga_kVA),
        "cos_phi": float(cos_phi),
        "Ucc_pct": float(Ucc_pct),
        "n_trafos": n,
        "modo": str(modo).lower(),
        "observacion_configuracion": obs_cfg,
        "capacidad": capacidad,
        "I_nominal_sec_A": i_nom_sec,
        "icc_secundario": icc,
        "dv_trafo": dv,
    }
