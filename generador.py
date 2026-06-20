import importlib
import math

from motores import calcular_corriente_arranque

# ============================================================
# CONSTANTES - clasificacion por origen
# TIPO A: parametro de proyecto - DEBE ser ingresado por usuario
# TIPO B: constante normada - no modificar sin cambiar norma
# TIPO C: criterio de diseno - cambiar solo con justificacion
# ============================================================

POTENCIAS_ESTANDAR_IEC_KVA = [
    20, 30, 45, 60, 75, 100, 125, 150, 175, 200,
    250, 300, 350, 400, 500, 600, 750, 1000,
    1250, 1500, 1750, 2000, 2500, 3000
]

XD_PP_DEFAULT = 20.0  # TIPO A - DEFAULT: verificar con ficha tecnica GE
XD_P_DEFAULT = 28.0  # TIPO A - DEFAULT: verificar con ficha tecnica GE
XD_DEFAULT = 120.0  # TIPO A - DEFAULT: verificar con ficha tecnica GE
R1_DEFAULT = 2.0  # TIPO A - DEFAULT: verificar con ficha tecnica GE
X0_DEFAULT = 5.0  # TIPO A - DEFAULT: verificar con ficha tecnica GE
C_MAX_BT = 1.05  # TIPO B - IEC 60909-0: factor de tension c_max para BT
C_MIN_BT = 0.95  # TIPO B - IEC 60909-0: factor de tension c_min para BT

XD_DEFAULT_PCT = 25.0  # TIPO A - DEFAULT: reactancia usada en evaluacion rapida
MARGEN_GE_DEFAULT = 1.25  # TIPO C - criterio conservador de diseno (+25%)
COS_PHI_GE_DEFAULT = 0.8  # TIPO C - valor tipico de alternador en generacion BT
DV_ARRANQUE_LIMITE_NORMAL = 15.0  # TIPO B - NCh 4-2003 12.28.8 referencia operativa
DV_ARRANQUE_LIMITE_CRITICO = 10.0  # TIPO C - umbral interno para cargas criticas

# Derrateo por altitud — ISO 8528-1:2018 §13.4 / IEC 60034-1 §3.5:
#   sin derrateo hasta 1500 msnm; -4% por cada 300 m adicionales
ALTITUD_BASE_DERRATEO_MSNM = 1500.0
ALTITUD_MAX_DERRATEO_MSNM = 4000.0
TASA_DERRATEO_POR_300M = 0.04  # 4 % / 300 m — ISO 8528-1 Tabla 3

# Autonomía mínima de emergencia — RIC N°08 §5.3.1 (SEC Chile):
#   grupos electrógenos de emergencia ≥ 6 h de autonomía a plena carga
AUTONOMIA_MINIMA_EMERGENCIA_HR = 6.0

def _curve_multiplier(curva: str) -> float:
    c = str(curva or "").strip().upper()
    if c == "MA":
        return 12.0
    if c == "D":
        return 15.0
    if c == "K":
        return 11.0
    if c == "C":
        return 10.0
    return 10.0


def _as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _norm_to_pu(x: float) -> float:
    v = float(x)
    if v > 10.0:
        return v / 100.0
    return v


def _norm_r_to_pu(x: float) -> float:
    v = float(x)
    if v > 1.0:
        return v / 100.0
    return v


def get_parametros_alternador(
    modelo: str,
    Vn_V: float,
    Sn_kVA: float = None
) -> dict:
    mod = str(modelo or "").strip().lower().replace("-", "_").replace(" ", "_")
    try:
        preset = importlib.import_module(f"presets.alternadores.{mod}")
        return preset.get_parametros(Vn_V=Vn_V, Sn_kVA=Sn_kVA)
    except (ImportError, AttributeError):
        return {
            "Xd_pp_pct": XD_PP_DEFAULT,
            "Xd_p_pct": XD_P_DEFAULT,
            "Xd_pct": XD_DEFAULT,
            "R1_pct": R1_DEFAULT,
            "X0_pct": X0_DEFAULT,
            "Rs_ohm": None,
            "Sn_base_kVA": None if Sn_kVA is None else float(Sn_kVA),
            "modelo": mod or "custom",
            "usa_defaults": True,
            "defaults_aplicados": ["Xd_pp_pct", "Xd_p_pct", "Xd_pct", "R1_pct", "X0_pct"],
            "modelo_no_encontrado": modelo,
        }


def _defaults_icc_ge_aplicados(
    Xd_pp_pct: float,
    Xd_p_pct: float,
    Xd_pct: float,
    R1_pct: float,
    Rs_ohm: float,
    X0_pct: float
) -> list:
    defaults = []
    if abs(_norm_to_pu(Xd_pp_pct) - _norm_to_pu(XD_PP_DEFAULT)) < 1e-9:
        defaults.append("Xd_pp_pct")
    if abs(_norm_to_pu(Xd_p_pct) - _norm_to_pu(XD_P_DEFAULT)) < 1e-9:
        defaults.append("Xd_p_pct")
    if abs(_norm_to_pu(Xd_pct) - _norm_to_pu(XD_DEFAULT)) < 1e-9:
        defaults.append("Xd_pct")
    if Rs_ohm is None and abs(_norm_r_to_pu(R1_pct) - _norm_r_to_pu(R1_DEFAULT)) < 1e-9:
        defaults.append("R1_pct")
    if abs(_norm_to_pu(X0_pct) - _norm_to_pu(X0_DEFAULT)) < 1e-9:
        defaults.append("X0_pct")
    return defaults


def calcular_derrateo_altitud(altitud_msnm: float) -> float:
    alt = float(altitud_msnm)
    if alt > ALTITUD_MAX_DERRATEO_MSNM:
        raise ValueError(f"Altitud > {ALTITUD_MAX_DERRATEO_MSNM:.0f} msnm: consultar fabrica")
    if alt <= ALTITUD_BASE_DERRATEO_MSNM:
        return 1.0
    factor = 1.0 - (TASA_DERRATEO_POR_300M * ((alt - ALTITUD_BASE_DERRATEO_MSNM) / 300.0))
    return round(max(factor, 0.01), 4)


def calcular_potencia_minima_ge(
    P_demanda_kW: float,
    P_motor_max_kW: float,
    factor_arranque_motor: float = 6.0,
    altitud_msnm: float = 0.0,
    margen: float = MARGEN_GE_DEFAULT
) -> dict:
    p_dem = max(float(P_demanda_kW), 0.0)
    p_motor = max(float(P_motor_max_kW), 0.0)
    factor_arr = float(factor_arranque_motor)
    margen = float(margen)

    p_arranque = p_dem - p_motor + (p_motor * factor_arr)
    p_base = max(p_dem, p_arranque) * margen
    p_min_kva = p_base / COS_PHI_GE_DEFAULT

    factor_der = calcular_derrateo_altitud(altitud_msnm)
    p_min_efectivo = p_min_kva / max(factor_der, 1e-9)

    p_estandar = POTENCIAS_ESTANDAR_IEC_KVA[-1]
    for valor in POTENCIAS_ESTANDAR_IEC_KVA:
        if valor >= p_min_efectivo:
            p_estandar = valor
            break

    return {
        "P_minimo_kW": round(p_base, 3),
        "P_minimo_kVA": round(p_min_efectivo, 3),
        "P_estandar_kVA": int(p_estandar),
        "factor_derrateo": round(factor_der, 4),
        "altitud_msnm": float(altitud_msnm),
    }


def verificar_ge_seleccionado(
    modelo_ge: str,
    P_ge_kVA_prime: float,
    P_ge_kVA_emergencia: float,
    cos_phi_ge: float,
    P_demanda_kW: float,
    P_motor_max_kW: float,
    factor_arranque_motor: float,
    altitud_msnm: float,
    regimen_uso: str
) -> dict:
    reg = str(regimen_uso or "prime").strip().lower()
    if reg == "emergencia":
        p_ge_kva = float(P_ge_kVA_emergencia)
    else:
        p_ge_kva = float(P_ge_kVA_prime)

    factor_der = calcular_derrateo_altitud(altitud_msnm)
    p_ge_ef_kva = p_ge_kva * factor_der
    p_ge_ef_kw = p_ge_ef_kva * float(cos_phi_ge)

    requerido = calcular_potencia_minima_ge(
        P_demanda_kW=P_demanda_kW,
        P_motor_max_kW=P_motor_max_kW,
        factor_arranque_motor=factor_arranque_motor,
        altitud_msnm=altitud_msnm,
        margen=MARGEN_GE_DEFAULT,
    )

    p_min_kva = requerido["P_minimo_kVA"]
    margen_kva = p_ge_ef_kva - p_min_kva
    ok = margen_kva >= 0
    uso_pct = (float(P_demanda_kW) / max(p_ge_ef_kw, 1e-9)) * 100.0

    if ok:
        obs = (
            f"GE {modelo_ge} suficiente en {reg}: "
            f"margen {round(margen_kva, 2)} kVA."
        )
    else:
        obs = (
            f"GE {modelo_ge} insuficiente en {reg}: "
            f"deficit {round(abs(margen_kva), 2)} kVA."
        )

    return {
        "ok": ok,
        "P_ge_efectiva_kW": round(p_ge_ef_kw, 3),
        "P_ge_efectiva_kVA": round(p_ge_ef_kva, 3),
        "P_minimo_kVA": round(p_min_kva, 3),
        "margen_kVA": round(margen_kva, 3),
        "uso_pct": round(uso_pct, 3),
        "factor_derrateo": round(factor_der, 4),
        "observacion": obs,
    }


def calcular_icc_ge(
    P_kVA: float,
    V_nominal: float,
    Xd_pp_pct: float = XD_PP_DEFAULT,
    Xd_p_pct: float = XD_P_DEFAULT,
    Xd_pct: float = XD_DEFAULT,
    R1_pct: float = R1_DEFAULT,
    Rs_ohm: float = None,
    X0_pct: float = X0_DEFAULT,
    c_max: float = C_MAX_BT,
    c_min: float = C_MIN_BT
) -> dict:
    p_kva = max(float(P_kVA), 1e-9)
    v = max(float(V_nominal), 1e-9)
    xd_pp = max(_norm_to_pu(Xd_pp_pct), 1e-12)
    xd_p = max(_norm_to_pu(Xd_p_pct), 1e-12)
    xd = max(_norm_to_pu(Xd_pct), 1e-12)
    x0 = max(_norm_to_pu(X0_pct), 1e-12)

    zbase = (v ** 2) / (p_kva * 1000.0)
    if Rs_ohm is not None:
        r_ohm = max(float(Rs_ohm), 0.0)
        r_pu = r_ohm / max(zbase, 1e-12)
    else:
        r_pu = max(_norm_r_to_pu(R1_pct), 0.0)
        r_ohm = r_pu * zbase

    z1_pp = complex(r_pu, xd_pp) * zbase
    z1_p = complex(r_pu, xd_p) * zbase
    z1 = complex(r_pu, xd) * zbase
    z0 = complex(0.0, x0) * zbase

    z1_pp_abs = abs(z1_pp)
    z1_p_abs = abs(z1_p)
    z1_abs = abs(z1)
    z0_abs = abs(z0)

    ik3_pp = float(c_max) * v / (math.sqrt(3.0) * max(z1_pp_abs, 1e-12))
    ik3_p = float(c_max) * v / (math.sqrt(3.0) * max(z1_p_abs, 1e-12))
    ik3 = float(c_max) * v / (math.sqrt(3.0) * max(z1_abs, 1e-12))
    ik1_pp = float(c_max) * math.sqrt(3.0) * v / max((2.0 * z1_pp_abs + z0_abs), 1e-12)
    ik3_min = float(c_min) * v / (math.sqrt(3.0) * max(z1_pp_abs, 1e-12))

    defaults_aplicados = _defaults_icc_ge_aplicados(
        Xd_pp_pct=Xd_pp_pct,
        Xd_p_pct=Xd_p_pct,
        Xd_pct=Xd_pct,
        R1_pct=R1_pct,
        Rs_ohm=Rs_ohm,
        X0_pct=X0_pct,
    )
    usa_defaults = bool(defaults_aplicados)

    return {
        "Ik3_pp_kA": round(ik3_pp / 1000.0, 3),
        "Ik3_p_kA": round(ik3_p / 1000.0, 3),
        "Ik3_kA": round(ik3 / 1000.0, 3),
        "Ik1_pp_kA": round(ik1_pp / 1000.0, 3),
        "Ik3_min_kA": round(ik3_min / 1000.0, 3),
        "Zbase_ohm": round(zbase, 6),
        "Z1_pp_ohm": round(z1_pp_abs, 6),
        "Z0_ohm": round(z0_abs, 6),
        "Xd_pp_pct": round(xd_pp * 100.0, 3),
        "Xd_p_pct": round(xd_p * 100.0, 3),
        "Xd_pct": round(xd * 100.0, 3),
        "R1_pct": round(r_pu * 100.0, 3),
        "Rs_ohm": round(r_ohm, 6),
        "X0_pct": round(x0 * 100.0, 3),
        "usa_defaults": usa_defaults,
        "defaults_aplicados": defaults_aplicados,
        # Compatibilidad legado
        "Icc_nominal_kA": round(ik3_pp / 1000.0, 3),
        "Icc_max_kA": round((ik3_pp * 1.05) / 1000.0, 3),
        "Icc_min_kA": round((ik3_pp * 0.95) / 1000.0, 3),
        "Z_ge_ohm": round(z1_pp_abs, 6),
    }


def calcular_dv_arranque_ge(
    P_motor_kW: float,
    factor_arranque: float,
    P_ge_kVA: float,
    V_nominal: float,
    cos_phi_motor: float = 0.85,
    rendimiento_motor: float = 0.92,
    Xd_pct: float = XD_DEFAULT_PCT
) -> dict:
    p_motor = float(P_motor_kW) * 1000.0
    v = max(float(V_nominal), 1e-9)
    fp = max(float(cos_phi_motor), 1e-9)
    eta = max(float(rendimiento_motor), 1e-9)

    i_n = p_motor / (math.sqrt(3.0) * v * fp * eta)
    arr = calcular_corriente_arranque(i_n, "directo", factor_arranque=float(factor_arranque))
    i_arr = arr["I_arranque"]

    z_ge = (float(Xd_pct) / 100.0) * ((v ** 2) / (float(P_ge_kVA) * 1000.0))
    dv_v = i_arr * z_ge * math.sqrt(3.0)
    dv_pct = (dv_v / v) * 100.0

    if dv_pct <= DV_ARRANQUE_LIMITE_CRITICO:
        estado = "OK_CRITICO"
        limite = DV_ARRANQUE_LIMITE_CRITICO
    elif dv_pct <= DV_ARRANQUE_LIMITE_NORMAL:
        estado = "OK"
        limite = DV_ARRANQUE_LIMITE_NORMAL
    else:
        estado = "CRITICO"
        limite = DV_ARRANQUE_LIMITE_NORMAL

    return {
        "I_arranque_A": round(i_arr, 3),
        "dv_V": round(dv_v, 3),
        "dv_pct": round(dv_pct, 3),
        "estado": estado,
        "limite_aplicado": float(limite),
    }


def calcular_autonomia(
    P_demanda_kW: float,
    P_ge_prime_kW: float,
    consumo_100_galhr: float,
    consumo_75_galhr: float,
    capacidad_tanque_gal: float,
    consumo_50_galhr: float = None
) -> dict:
    p_dem = max(float(P_demanda_kW), 0.0)
    p_prime = max(float(P_ge_prime_kW), 1e-9)
    uso_pct = (p_dem / p_prime) * 100.0

    c100 = float(consumo_100_galhr)
    c75 = float(consumo_75_galhr)
    c50 = None if consumo_50_galhr is None else float(consumo_50_galhr)

    if uso_pct >= 87.5:
        consumo = c75 + ((uso_pct - 75.0) / 25.0) * (c100 - c75)
    elif uso_pct >= 62.5 and c50 is not None:
        consumo = c50 + ((uso_pct - 50.0) / 25.0) * (c75 - c50)
    else:
        consumo = c75 + ((uso_pct - 75.0) / 25.0) * (c100 - c75)

    consumo = max(consumo, 1e-9)
    autonomia = float(capacidad_tanque_gal) / consumo

    return {
        "uso_pct": round(uso_pct, 3),
        "consumo_estimado_galhr": round(consumo, 3),
        "autonomia_hr": round(autonomia, 3),
        "autonomia_ok": autonomia >= AUTONOMIA_MINIMA_EMERGENCIA_HR,
    }


def verificar_protecciones_modo_ge(
    circuitos: list,
    Icc_ge_kA: float
) -> list:
    resultados = []
    icc_ge_a = float(Icc_ge_kA) * 1000.0

    for c in (circuitos or []):
        nombre = c.get("nombre", "SIN_NOMBRE")
        curva = str(c.get("curva", c.get("curva_proteccion", "D"))).strip().upper()

        proteccion_a = c.get("proteccion_A")
        if proteccion_a is None:
            proteccion_a = c.get("In_A")
        if proteccion_a is None:
            proteccion_a = c.get("proteccion", 0.0)
        in_a = _as_float(proteccion_a, 0.0)

        im = round(_curve_multiplier(curva) * in_a, 3)
        ok = im > icc_ge_a
        obs = "OK" if ok else "VERIFICAR"

        resultados.append({
            "nombre": nombre,
            "proteccion": f"{curva}{int(round(in_a))}A" if in_a > 0 else f"{curva}N/A",
            "Im": im,
            "Icc_ge_A": round(icc_ge_a, 3),
            "ok": ok,
            "observacion": obs,
        })

    return resultados


def calcular_generador(
    nombre: str,
    modelo_ge: str,
    P_ge_kVA_prime: float,
    P_ge_kVA_emergencia: float,
    cos_phi_ge: float,
    V_nominal: float,
    regimen_uso: str,
    P_demanda_kW: float,
    P_motor_max_kW: float,
    factor_arranque_motor: float,
    altitud_msnm: float,
    Xd_pp_pct: float = XD_PP_DEFAULT,
    Xd_p_pct: float = XD_P_DEFAULT,
    Xd_pct: float = XD_DEFAULT,
    R1_pct: float = R1_DEFAULT,
    Rs_ohm: float = None,
    X0_pct: float = X0_DEFAULT,
    consumo_100_galhr: float = None,
    consumo_75_galhr: float = None,
    capacidad_tanque_gal: float = None,
    circuitos: list = None
) -> dict:
    p_calc = calcular_potencia_minima_ge(
        P_demanda_kW=P_demanda_kW,
        P_motor_max_kW=P_motor_max_kW,
        factor_arranque_motor=factor_arranque_motor,
        altitud_msnm=altitud_msnm,
        margen=MARGEN_GE_DEFAULT,
    )
    verif = verificar_ge_seleccionado(
        modelo_ge=modelo_ge,
        P_ge_kVA_prime=P_ge_kVA_prime,
        P_ge_kVA_emergencia=P_ge_kVA_emergencia,
        cos_phi_ge=cos_phi_ge,
        P_demanda_kW=P_demanda_kW,
        P_motor_max_kW=P_motor_max_kW,
        factor_arranque_motor=factor_arranque_motor,
        altitud_msnm=altitud_msnm,
        regimen_uso=regimen_uso,
    )

    reg = str(regimen_uso or "prime").strip().lower()
    p_kva_sel = float(P_ge_kVA_emergencia if reg == "emergencia" else P_ge_kVA_prime)
    icc = calcular_icc_ge(
        P_kVA=p_kva_sel,
        V_nominal=V_nominal,
        Xd_pp_pct=Xd_pp_pct,
        Xd_p_pct=Xd_p_pct,
        Xd_pct=Xd_pct,
        R1_pct=R1_pct,
        Rs_ohm=Rs_ohm,
        X0_pct=X0_pct,
        c_max=C_MAX_BT,
        c_min=C_MIN_BT,
    )
    dv = calcular_dv_arranque_ge(
        P_motor_kW=P_motor_max_kW,
        factor_arranque=factor_arranque_motor,
        P_ge_kVA=p_kva_sel,
        V_nominal=V_nominal,
        Xd_pct=Xd_pct,
    )

    autonomia = None
    if (
        consumo_100_galhr is not None
        and consumo_75_galhr is not None
        and capacidad_tanque_gal is not None
    ):
        autonomia = calcular_autonomia(
            P_demanda_kW=P_demanda_kW,
            P_ge_prime_kW=float(P_ge_kVA_prime) * float(cos_phi_ge),
            consumo_100_galhr=consumo_100_galhr,
            consumo_75_galhr=consumo_75_galhr,
            capacidad_tanque_gal=capacidad_tanque_gal,
            consumo_50_galhr=None,
        )

    protecciones = verificar_protecciones_modo_ge(
        circuitos or [],
        icc["Icc_nominal_kA"],
    )

    i_nom_ge = (p_kva_sel * 1000.0) / (math.sqrt(3.0) * max(float(V_nominal), 1e-9))
    defaults_aplicados = list(icc.get("defaults_aplicados", []))

    return {
        "nombre": nombre,
        "modelo_ge": modelo_ge,
        "regimen_uso": reg,
        "V_nominal": float(V_nominal),
        "cos_phi_ge": float(cos_phi_ge),
        "altitud_msnm": float(altitud_msnm),
        "factor_arranque_motor": float(factor_arranque_motor),
        "P_demanda_kW": float(P_demanda_kW),
        "P_motor_max_kW": float(P_motor_max_kW),
        "P_ge_kVA_prime": float(P_ge_kVA_prime),
        "P_ge_kVA_emergencia": float(P_ge_kVA_emergencia),
        "P_ge_kVA_seleccionado": round(p_kva_sel, 3),
        "I_ge_nominal_A": round(i_nom_ge, 3),
        "potencia_requerida": p_calc,
        "verificacion_ge": verif,
        "icc_ge": icc,
        "dv_arranque_ge": dv,
        "autonomia": autonomia,
        "protecciones_modo_ge": protecciones,
        "usa_defaults": bool(defaults_aplicados),
        "defaults_aplicados": defaults_aplicados,
    }
