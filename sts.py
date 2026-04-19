T_TRANSFER_MAX_MS = {
    "it": 8.0,
    "hvac": 20.0,
    "iluminacion": 100.0,
    "ups": 0.0,
    "general": 20.0,
}

OVERLOAD_CURVA = {
    125: 60.0,
    150: 10.0,
    200: 1.0,
}

FACTOR_USO_MAX = 0.80
FACTOR_NO_LINEAL_ALERTA = 0.80
FACTOR_CRESTA_IT = 3.0


def verificar_capacidad_sts(
    P_carga_kVA: float,
    P_modulo_kVA: float,
    n_modulos: int = 1,
    factor_uso_max: float = FACTOR_USO_MAX
) -> dict:
    p_carga = float(P_carga_kVA)
    p_total = max(float(P_modulo_kVA) * int(n_modulos), 1e-9)
    uso_pct = (p_carga / p_total) * 100.0
    limite_pct = float(factor_uso_max) * 100.0
    ok = uso_pct <= limite_pct
    margen = (p_total * float(factor_uso_max)) - p_carga

    return {
        "P_sts_total_kVA": round(p_total, 3),
        "uso_pct": round(uso_pct, 3),
        "margen_kVA": round(margen, 3),
        "ok": ok,
        "observacion": "OK" if ok else "Capacidad STS excedida sobre limite operativo",
    }


def verificar_transferencia(
    t_transferencia_ms: float,
    tipo_carga: str
) -> dict:
    tipo = str(tipo_carga or "general").strip().lower()
    t = float(t_transferencia_ms)
    t_max = float(T_TRANSFER_MAX_MS.get(tipo, 20.0))

    if tipo == "ups":
        return {
            "ok": True,
            "t_transferencia_ms": round(t, 3),
            "t_max_ms": t_max,
            "margen_ms": round(t_max - t, 3),
            "norma": "IEC 62040-3 / ITIC",
            "observacion": "transparente",
        }

    margen = t_max - t
    ok = margen >= 0
    return {
        "ok": ok,
        "t_transferencia_ms": round(t, 3),
        "t_max_ms": t_max,
        "margen_ms": round(margen, 3),
        "norma": "IEC 60947-6-1 / ITIC",
        "observacion": "OK" if ok else "Transferencia supera tiempo maximo admisible",
    }


def verificar_overload(
    P_carga_kVA: float,
    P_sts_total_kVA: float,
    t_sobrecarga_seg: float = 0.0
) -> dict:
    p_total = max(float(P_sts_total_kVA), 1e-9)
    p_carga = float(P_carga_kVA)
    t = float(t_sobrecarga_seg)
    pct = (p_carga / p_total) * 100.0

    if pct <= 100.0:
        return {
            "sobrecarga_pct": round(pct, 3),
            "t_max_permitido_seg": float("inf"),
            "ok": True,
            "nivel": "normal",
            "observacion": "Sin sobrecarga",
        }

    if pct <= 125.0:
        t_max = OVERLOAD_CURVA[125]
        nivel = "leve"
    elif pct <= 150.0:
        t_max = OVERLOAD_CURVA[150]
        nivel = "moderada"
    else:
        t_max = OVERLOAD_CURVA[200]
        nivel = "severa"

    ok = t <= t_max
    return {
        "sobrecarga_pct": round(pct, 3),
        "t_max_permitido_seg": float(t_max),
        "ok": ok,
        "nivel": nivel,
        "observacion": "OK" if ok else "Sobrecarga excede tiempo permitido",
    }


def verificar_redundancia_2N(
    P_carga_total_kVA: float,
    P_modulo_kVA: float,
    n_modulos: int = 1,
    n_sts: int = 2
) -> dict:
    p_carga = float(P_carga_total_kVA)
    p_unit = max(float(P_modulo_kVA) * int(n_modulos), 1e-9)
    n = max(int(n_sts), 1)

    uso_normal = (p_carga / (p_unit * n)) * 100.0
    uso_falla = (p_carga / p_unit) * 100.0
    limite = FACTOR_USO_MAX * 100.0

    ok_normal = uso_normal <= limite
    ok_falla = uso_falla <= limite
    if ok_normal and ok_falla:
        obs = "Redundancia 2N cumple en operacion normal y falla de bus"
    elif ok_normal and not ok_falla:
        obs = "Cumple en normal, no cumple ante falla de bus"
    else:
        obs = "No cumple criterio 2N"

    return {
        "P_sts_unit_kVA": round(p_unit, 3),
        "uso_normal_pct": round(uso_normal, 3),
        "uso_falla_pct": round(uso_falla, 3),
        "ok_normal": ok_normal,
        "ok_falla": ok_falla,
        "observacion": obs,
    }


def verificar_carga_no_lineal(
    P_total_kVA: float,
    P_no_lineal_kVA: float,
    factor_cresta_requerido: float = FACTOR_CRESTA_IT
) -> dict:
    p_total = float(P_total_kVA)
    p_nl = float(P_no_lineal_kVA)
    pct = (p_nl / p_total) * 100.0 if p_total > 0 else 0.0
    ok = pct <= (FACTOR_NO_LINEAL_ALERTA * 100.0)

    return {
        "pct_no_lineal": round(pct, 3),
        "ok": ok,
        "factor_cresta_requerido": float(factor_cresta_requerido),
        "observacion": "OK" if ok else "ALERTAR",
    }


def calcular_sts(
    nombre: str,
    modelo_sts: str,
    P_modulo_kVA: float,
    n_modulos: int,
    t_transferencia_ms: float,
    V_nominal: float,
    P_carga_kVA: float,
    cos_phi_carga: float,
    tipo_carga: str,
    topologia: str,
    n_sts: int = 1,
    P_no_lineal_kVA: float = 0.0,
    t_sobrecarga_seg: float = 0.0
) -> dict:
    top = str(topologia or "simple").strip().lower()
    capacidad = verificar_capacidad_sts(P_carga_kVA, P_modulo_kVA, n_modulos=n_modulos)
    transferencia = verificar_transferencia(t_transferencia_ms, tipo_carga)
    overload = verificar_overload(
        P_carga_kVA=P_carga_kVA,
        P_sts_total_kVA=capacidad["P_sts_total_kVA"],
        t_sobrecarga_seg=t_sobrecarga_seg,
    )

    redundancia = None
    if top == "2n":
        redundancia = verificar_redundancia_2N(
            P_carga_total_kVA=P_carga_kVA,
            P_modulo_kVA=P_modulo_kVA,
            n_modulos=n_modulos,
            n_sts=n_sts,
        )

    no_lineal = None
    if float(P_no_lineal_kVA) > 0:
        no_lineal = verificar_carga_no_lineal(
            P_total_kVA=P_carga_kVA,
            P_no_lineal_kVA=P_no_lineal_kVA,
            factor_cresta_requerido=FACTOR_CRESTA_IT,
        )

    return {
        "nombre": str(nombre),
        "modelo_sts": str(modelo_sts),
        "P_modulo_kVA": float(P_modulo_kVA),
        "n_modulos": int(n_modulos),
        "P_sts_total_kVA": round(float(P_modulo_kVA) * int(n_modulos), 3),
        "t_transferencia_ms": float(t_transferencia_ms),
        "V_nominal": float(V_nominal),
        "P_carga_kVA": float(P_carga_kVA),
        "P_carga_kW": round(float(P_carga_kVA) * float(cos_phi_carga), 3),
        "cos_phi_carga": float(cos_phi_carga),
        "tipo_carga": str(tipo_carga).lower(),
        "topologia": top,
        "n_sts": int(n_sts),
        "P_no_lineal_kVA": float(P_no_lineal_kVA),
        "t_sobrecarga_seg": float(t_sobrecarga_seg),
        "capacidad": capacidad,
        "transferencia": transferencia,
        "overload": overload,
        "redundancia_2N": redundancia,
        "carga_no_lineal": no_lineal,
    }
