import math

from calculos import calcular_caida_tension
from conductores import FACTORES_TEMP, get_tabla_conductores

# ============================================================
# CONSTANTES - clasificacion por origen
# TIPO A: parametro de proyecto - DEBE ser ingresado por usuario
# TIPO B: constante normada - no modificar sin cambiar norma
# TIPO C: criterio de diseno - cambiar solo con justificacion
# ============================================================


FACTORES_ARRANQUE_DEFAULT = {
    "directo": 6.0,  # TIPO A - DEFAULT: DOL tipico, verificar placa del motor
    "estrella_triangulo": 2.0,  # TIPO A - DEFAULT: verificar configuracion real
    "variador": 1.2,  # TIPO A - DEFAULT: verificar rampa del VFD
    "arranque_suave": 2.5,  # TIPO A - DEFAULT: verificar ajuste del softstarter
}

FACTORES_ARRANQUE_RANGO = {
    "directo": (5.0, 8.0),
    "estrella_triangulo": (1.5, 2.5),
    "variador": (1.0, 1.5),
    "arranque_suave": (1.5, 3.0),
}

FACTORES_NCH_1228 = {
    # NCh Elec 12/2003 (uso de motores): factores por régimen y duración de servicio.
    "breve": {5: 1.1, 15: 1.2, 30: 1.5, 60: 1.5, 999: 1.5},
    "intermitente": {5: 0.85, 15: 0.85, 30: 0.9, 60: 0.9, 999: 1.4},
    "periodico": {5: 0.85, 15: 0.9, 30: 0.95, 60: 0.95, 999: 1.4},
    "permanente": 1.25,
}

DV_ARRANQUE_LIMITE_NORMAL = 15.0  # TIPO B - NCh 4-2003 12.28.8 referencia de aceptacion
DV_ARRANQUE_LIMITE_CRITICO = 10.0  # TIPO C - umbral interno para cargas sensibles


def _normalizar_arranque(tipo_arranque: str) -> str:
    tipo = str(tipo_arranque).strip().lower()
    return tipo if tipo in FACTORES_ARRANQUE_DEFAULT else "directo"


def _resolver_periodo(periodo_min: int) -> int:
    p = int(periodo_min)
    if p <= 5:
        return 5
    if p <= 15:
        return 15
    if p <= 30:
        return 30
    if p <= 60:
        return 60
    return 999


def _factor_temperatura(temperatura: float) -> float:
    t = int(round(float(temperatura)))
    if t in FACTORES_TEMP:
        return FACTORES_TEMP[t]
    disponibles = sorted(FACTORES_TEMP.keys())
    mas_cercano = min(disponibles, key=lambda x: abs(x - t))
    return FACTORES_TEMP[mas_cercano]


def _buscar_por_mm2(tabla: dict, s_mm2: float):
    candidatos = sorted(tabla.items(), key=lambda item: item[1]["mm2"])
    for nombre, data in candidatos:
        if data["mm2"] >= float(s_mm2):
            return nombre, data
    return candidatos[-1]


def calcular_corriente_motor(
    P_kW: float,
    V_nominal: float,
    cos_phi: float,
    rendimiento: float,
    sistema: str = "3F"
) -> float:
    p_w = float(P_kW) * 1000.0
    v = max(float(V_nominal), 1e-9)
    fp = max(float(cos_phi), 1e-9)
    eta = max(float(rendimiento), 1e-9)

    if str(sistema).upper() == "3F":
        i_n = p_w / (math.sqrt(3.0) * v * fp * eta)
    else:
        i_n = p_w / (v * fp * eta)
    return round(i_n, 2)


def calcular_corriente_arranque(
    I_n: float,
    tipo_arranque: str,
    factor_arranque: float = None
) -> dict:
    tipo = _normalizar_arranque(tipo_arranque)
    rango = FACTORES_ARRANQUE_RANGO[tipo]

    if factor_arranque is None:
        factor = FACTORES_ARRANQUE_DEFAULT[tipo]
    else:
        factor = float(factor_arranque)

    en_rango = rango[0] <= factor <= rango[1]
    i_arr = round(float(I_n) * factor, 2)

    return {
        "I_arranque": i_arr,
        "factor_usado": round(factor, 3),
        "en_rango_tipico": en_rango,
        "rango_tipico": rango,
        "tipo_arranque": tipo,
    }


def calcular_dv_arranque(
    I_arranque: float,
    L_m: float,
    S_mm2: float,
    sistema: str,
    V_nominal: float
) -> dict:
    dv_v, _ = calcular_caida_tension(
        float(L_m),
        float(S_mm2),
        float(I_arranque),
        1,
        str(sistema).upper(),
    )
    dv_pct = round((dv_v / max(float(V_nominal), 1e-9)) * 100.0, 3)

    if dv_pct <= DV_ARRANQUE_LIMITE_CRITICO:
        estado = "OK"
        limite = DV_ARRANQUE_LIMITE_CRITICO
    elif dv_pct <= DV_ARRANQUE_LIMITE_NORMAL:
        estado = "PRECAUCION"
        limite = DV_ARRANQUE_LIMITE_NORMAL
    else:
        estado = "CRITICO"
        limite = DV_ARRANQUE_LIMITE_NORMAL

    return {
        "dv_V": round(dv_v, 3),
        "dv_pct": dv_pct,
        "estado": estado,
        "limite_aplicado": limite,
    }


def dimensionar_conductor_motor(
    I_n: float,
    regimen: str,
    periodo_min: int,
    temperatura: float = 30.0,
    norma: str = "AWG"
) -> dict:
    reg = str(regimen).strip().lower()
    if reg == "permanente":
        factor_regimen = FACTORES_NCH_1228["permanente"]
    else:
        tabla_reg = FACTORES_NCH_1228.get(reg, FACTORES_NCH_1228["intermitente"])
        factor_regimen = tabla_reg[_resolver_periodo(periodo_min)]

    factor_temp = _factor_temperatura(temperatura)
    i_diseno = round(float(I_n) * factor_regimen * factor_temp, 2)

    tabla = get_tabla_conductores(str(norma).upper())
    candidatos = sorted(tabla.items(), key=lambda item: item[1]["mm2"])
    conductor = candidatos[-1]
    for nombre, data in candidatos:
        if data["I_max"] >= i_diseno:
            conductor = (nombre, data)
            break

    nombre, data = conductor
    return {
        "conductor": nombre,
        "S_mm2": data["mm2"],
        "I_max": data["I_max"],
        "I_diseño": i_diseno,
        "factor_regimen": round(factor_regimen, 3),
        "factor_temperatura": round(factor_temp, 3),
    }


def seleccionar_guardamotor(
    I_n: float
) -> dict:
    rangos = [
        (0.1, 0.16), (0.16, 0.25), (0.25, 0.4), (0.4, 0.63),
        (0.63, 1), (1, 1.6), (1.6, 2.5), (2.5, 4), (4, 6.3),
        (6.3, 10), (10, 16), (16, 25), (25, 40), (40, 63),
        (63, 100), (100, 160),
    ]
    i_n = float(I_n)
    rango = rangos[-1]
    for r in rangos:
        if r[0] <= i_n <= r[1]:
            rango = r
            break
    return {
        "rango_min": float(rango[0]),
        "rango_max": float(rango[1]),
        "ajuste": round(i_n, 2),
    }


def verificar_proteccion_arranque(
    I_arranque: float,
    proteccion_A: float,
    curva: str,
    Icc_punto: float = None
) -> dict:
    in_a = float(proteccion_A)
    c = str(curva).strip().upper()

    if c == "MA":
        im = 12.0 * in_a
    elif c == "D":
        im = 15.0 * in_a
    else:  # K
        im = 11.0 * in_a

    requerimiento = float(I_arranque) * 1.25
    ok = im > requerimiento
    margen = round(((im / max(requerimiento, 1e-9)) - 1.0) * 100.0, 2)

    margen_icc_ok = None
    if Icc_punto is not None:
        margen_icc_ok = im < float(Icc_punto)

    obs = "OK"
    if not ok:
        obs = "Proteccion puede disparar durante arranque"
    if margen_icc_ok is False:
        obs = "Im supera Icc de punto; revisar coordinacion"

    return {
        "ok": ok,
        "Im": round(im, 2),
        "margen_arranque_pct": margen,
        "margen_Icc_ok": margen_icc_ok,
        "observacion": obs,
    }


def calcular_motor(
    nombre: str,
    P_kW: float,
    V_nominal: float,
    cos_phi: float,
    rendimiento: float,
    sistema: str,
    tipo_arranque: str,
    regimen: str,
    periodo_min: int,
    L_m: float,
    S_mm2_conductor: float = None,
    proteccion_A: float = None,
    curva: str = "MA",
    factor_arranque: float = None,
    temperatura: float = 30.0,
    Icc_punto: float = None,
    norma: str = "AWG"
) -> dict:
    i_n = calcular_corriente_motor(P_kW, V_nominal, cos_phi, rendimiento, sistema)
    arranque = calcular_corriente_arranque(i_n, tipo_arranque, factor_arranque)

    cond_dimensionado = dimensionar_conductor_motor(
        i_n, regimen, periodo_min, temperatura=temperatura, norma=norma
    )

    tabla = get_tabla_conductores(str(norma).upper())
    if S_mm2_conductor is None:
        conductor = cond_dimensionado
    else:
        nombre_c, data_c = _buscar_por_mm2(tabla, S_mm2_conductor)
        factor_reg = cond_dimensionado["factor_regimen"]
        factor_temp = cond_dimensionado["factor_temperatura"]
        conductor = {
            "conductor": nombre_c,
            "S_mm2": data_c["mm2"],
            "I_max": data_c["I_max"],
            "I_diseño": round(i_n * factor_reg * factor_temp, 2),
            "factor_regimen": factor_reg,
            "factor_temperatura": factor_temp,
        }

    dv_nom = calcular_dv_arranque(i_n, L_m, conductor["S_mm2"], sistema, V_nominal)
    dv_arr = calcular_dv_arranque(arranque["I_arranque"], L_m, conductor["S_mm2"], sistema, V_nominal)

    guardamotor = seleccionar_guardamotor(i_n)
    proteccion_nominal = float(proteccion_A) if proteccion_A is not None else guardamotor["rango_max"]
    proteccion = verificar_proteccion_arranque(
        arranque["I_arranque"], proteccion_nominal, curva, Icc_punto=Icc_punto
    )

    return {
        "nombre": nombre,
        "P_kW": float(P_kW),
        "V_nominal": float(V_nominal),
        "cos_phi": float(cos_phi),
        "rendimiento": float(rendimiento),
        "sistema": str(sistema).upper(),
        "tipo_arranque": arranque["tipo_arranque"],
        "regimen": str(regimen).lower(),
        "periodo_min": int(periodo_min),
        "I_n": i_n,
        "arranque": arranque,
        "conductor": conductor,
        "dv_nominal": dv_nom,
        "dv_arranque": dv_arr,
        "guardamotor": guardamotor,
        "proteccion": {
            "curva": str(curva).upper(),
            "proteccion_A": round(proteccion_nominal, 2),
            **proteccion,
        },
        "Icc_punto": Icc_punto,
        "norma": str(norma).upper(),
    }
