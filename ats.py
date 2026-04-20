import math


MODOS_TRANSFERENCIA = {
    "open": "Open Transition - interrupcion breve (100-500ms)",
    "closed": "Closed Transition - suave, requiere sincronizacion",
    "sts": "Static Transfer - < 4ms (ver modulo STS)",
    "soft": "Soft Load - via UPS/variador, transparente",
}

SYNC_DV_MAX_PCT = 5.0
SYNC_DF_MAX_HZ = 0.2
SYNC_DFASE_MAX_DEG = 5.0
T_PARALELO_MAX_MS = 200.0

T_DETECCION_DEFAULT_MS = 3000.0
T_ARRANQUE_GE_DEFAULT_MS = 10000.0
T_ESTABILIZACION_DEFAULT_MS = 5000.0
T_CIERRE_CONTACTOR_MS = 200.0

STAMFORD_HCI544D_W14 = {
    380: {"Xd_pp": 0.12, "Xd_p": 0.17, "Xd": 3.51, "X2": 0.23, "X0": 0.11, "Rs_ohm": 0.0041, "Sn_base_kVA": 625},
    400: {"Xd_pp": 0.11, "Xd_p": 0.15, "Xd": 3.17, "X2": 0.20, "X0": 0.10, "Rs_ohm": 0.0041, "Sn_base_kVA": 625},
    416: {"Xd_pp": 0.10, "Xd_p": 0.14, "Xd": 2.93, "X2": 0.19, "X0": 0.09, "Rs_ohm": 0.0041, "Sn_base_kVA": 625},
}


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
    Sn_kVA: float
) -> dict:
    mod = str(modelo or "custom").strip().upper()
    if mod != "HCI544D_W14":
        return None

    vn = float(Vn_V)
    sn = max(float(Sn_kVA), 1e-9)
    voltajes = sorted(STAMFORD_HCI544D_W14.keys())

    if vn <= voltajes[0]:
        base = STAMFORD_HCI544D_W14[voltajes[0]].copy()
    elif vn >= voltajes[-1]:
        base = STAMFORD_HCI544D_W14[voltajes[-1]].copy()
    else:
        v0, v1 = voltajes[0], voltajes[-1]
        for i in range(len(voltajes) - 1):
            if voltajes[i] <= vn <= voltajes[i + 1]:
                v0, v1 = voltajes[i], voltajes[i + 1]
                break
        d0 = STAMFORD_HCI544D_W14[v0]
        d1 = STAMFORD_HCI544D_W14[v1]
        frac = (vn - v0) / (v1 - v0)
        base = {
            "Xd_pp": d0["Xd_pp"] + (d1["Xd_pp"] - d0["Xd_pp"]) * frac,
            "Xd_p": d0["Xd_p"] + (d1["Xd_p"] - d0["Xd_p"]) * frac,
            "Xd": d0["Xd"] + (d1["Xd"] - d0["Xd"]) * frac,
            "X2": d0["X2"] + (d1["X2"] - d0["X2"]) * frac,
            "X0": d0["X0"] + (d1["X0"] - d0["X0"]) * frac,
            "Rs_ohm": d0["Rs_ohm"] + (d1["Rs_ohm"] - d0["Rs_ohm"]) * frac,
            "Sn_base_kVA": d0["Sn_base_kVA"],
        }

    sn_base = float(base.get("Sn_base_kVA", sn))
    escala = sn_base / sn
    return {
        "Xd_pp": round(base["Xd_pp"], 6),
        "Xd_p": round(base["Xd_p"], 6),
        "Xd": round(base["Xd"], 6),
        "X2": round(base["X2"], 6),
        "X0": round(base["X0"], 6),
        "Rs_ohm": round(base["Rs_ohm"], 6),
        "Sn_base_kVA": sn_base,
        "factor_escala": round(escala, 6),
        "modelo": "HCI544D_W14",
    }


def calcular_icc_ge_ats(
    Sn_kVA: float,
    Vn_V: float,
    Xd_pp_pct: float = 20.0,
    Xd_p_pct: float = 28.0,
    Xd_pct: float = 120.0,
    R1_pct: float = 2.0,
    Rs_ohm: float = None,
    X0_pct: float = 5.0,
    c_max: float = 1.05,
    c_min: float = 0.95
) -> dict:
    sn = max(float(Sn_kVA), 1e-9)
    vn = max(float(Vn_V), 1e-9)
    zbase = (vn ** 2) / (sn * 1000.0)

    xd_pp = _norm_to_pu(Xd_pp_pct)
    xd_p = _norm_to_pu(Xd_p_pct)
    xd = _norm_to_pu(Xd_pct)
    x0 = _norm_to_pu(X0_pct)
    if Rs_ohm is not None:
        r_ohm = max(float(Rs_ohm), 0.0)
        r_pu = r_ohm / max(zbase, 1e-12)
    else:
        r_pu = _norm_r_to_pu(R1_pct)
    z1_pp = complex(r_pu, xd_pp) * zbase
    z1_p = complex(r_pu, xd_p) * zbase
    z1 = complex(r_pu, xd) * zbase
    z0 = complex(0.0, x0) * zbase

    z1pp_abs = abs(z1_pp)
    z1p_abs = abs(z1_p)
    z1_abs = abs(z1)
    z0_abs = abs(z0)

    ik3_pp = c_max * vn / (math.sqrt(3.0) * max(z1pp_abs, 1e-12))
    ik3_p = c_max * vn / (math.sqrt(3.0) * max(z1p_abs, 1e-12))
    ik3 = c_max * vn / (math.sqrt(3.0) * max(z1_abs, 1e-12))
    ik1_pp = c_max * math.sqrt(3.0) * vn / max((2.0 * z1pp_abs + z0_abs), 1e-12)
    ik3_min = c_min * vn / (math.sqrt(3.0) * max(z1pp_abs, 1e-12))

    usa_defaults = (
        abs(xd_pp - _norm_to_pu(20.0)) < 1e-9
        or abs(xd_p - _norm_to_pu(28.0)) < 1e-9
        or abs(xd - _norm_to_pu(120.0)) < 1e-9
        or (Rs_ohm is None and abs(r_pu - _norm_r_to_pu(2.0)) < 1e-9)
        or abs(x0 - _norm_to_pu(5.0)) < 1e-9
    )

    return {
        "Ik3_pp_kA": round(ik3_pp / 1000.0, 3),
        "Ik3_p_kA": round(ik3_p / 1000.0, 3),
        "Ik3_kA": round(ik3 / 1000.0, 3),
        "Ik1_pp_kA": round(ik1_pp / 1000.0, 3),
        "Ik3_min_kA": round(ik3_min / 1000.0, 3),
        "usa_defaults": usa_defaults,
    }


def verificar_sincronizacion(
    V_fuente1_V: float,
    V_fuente2_V: float,
    f_fuente1_Hz: float,
    f_fuente2_Hz: float,
    fase_fuente1_deg: float = 0.0,
    fase_fuente2_deg: float = 0.0
) -> dict:
    v1 = float(V_fuente1_V)
    v2 = float(V_fuente2_V)
    f1 = float(f_fuente1_Hz)
    f2 = float(f_fuente2_Hz)
    p1 = float(fase_fuente1_deg)
    p2 = float(fase_fuente2_deg)

    v_nom = max((abs(v1) + abs(v2)) / 2.0, 1e-9)
    delta_v = abs(v1 - v2) / v_nom * 100.0
    delta_f = abs(f1 - f2)
    delta_fase = abs(p1 - p2)

    ok = (
        delta_v <= SYNC_DV_MAX_PCT
        and delta_f <= SYNC_DF_MAX_HZ
        and delta_fase <= SYNC_DFASE_MAX_DEG
    )

    return {
        "ok": ok,
        "delta_V_pct": round(delta_v, 3),
        "delta_f_Hz": round(delta_f, 3),
        "delta_fase_deg": round(delta_fase, 3),
        "limite_dV": SYNC_DV_MAX_PCT,
        "limite_df": SYNC_DF_MAX_HZ,
        "limite_fase": SYNC_DFASE_MAX_DEG,
        "observacion": "Sincronizacion OK" if ok else "No cumple sincronizacion IEC 60947-6-1",
    }


def calcular_tiempos_transferencia(
    modo: str,
    t_deteccion_ms: float = T_DETECCION_DEFAULT_MS,
    t_arranque_ge_ms: float = T_ARRANQUE_GE_DEFAULT_MS,
    t_estabilizacion_ge_ms: float = T_ESTABILIZACION_DEFAULT_MS,
    t_paralelo_ms: float = 150.0
) -> dict:
    m = str(modo or "open").strip().lower()
    t_det = float(t_deteccion_ms)
    t_arr = float(t_arranque_ge_ms)
    t_est = float(t_estabilizacion_ge_ms)
    t_par = float(t_paralelo_ms)

    if m == "open":
        t_total = t_det + t_arr + t_est + T_CIERRE_CONTACTOR_MS
        return {
            "modo": "open",
            "t_total_ms": round(t_total, 3),
            "t_interrupcion_ms": float(T_CIERRE_CONTACTOR_MS),
            "secuencia": ["detectar_falla", "arrancar_ge", "estabilizar_ge", "cerrar_contactor"],
            "requiere_sincronizacion": False,
            "observacion": "Open transition con interrupcion breve",
        }
    if m == "closed":
        t_total = t_det + t_arr + t_est + t_par + T_CIERRE_CONTACTOR_MS
        return {
            "modo": "closed",
            "t_total_ms": round(t_total, 3),
            "t_interrupcion_ms": 0.0,
            "secuencia": ["detectar_falla", "arrancar_ge", "estabilizar_ge", "sincronizar", "paralelo_controlado", "transferir"],
            "requiere_sincronizacion": True,
            "observacion": "Closed transition requiere sincronizacion",
        }
    if m == "sts":
        return {
            "modo": "sts",
            "t_total_ms": 4.0,
            "t_interrupcion_ms": 0.0,
            "secuencia": ["transferencia_estatica"],
            "requiere_sincronizacion": False,
            "observacion": "Derivar a modulo M11 STS",
        }
    return {
        "modo": "soft",
        "t_total_ms": round(t_det + t_arr + t_est, 3),
        "t_interrupcion_ms": 0.0,
        "secuencia": ["detectar_falla", "arrancar_ge", "soportar_con_ups", "transferir_suave"],
        "requiere_sincronizacion": False,
        "observacion": "Soft load via UPS/variador",
    }


def verificar_corriente_ats(
    I_carga_A: float,
    I_nominal_ats_A: float,
    factor_uso_max: float = 0.85
) -> dict:
    i_carga = float(I_carga_A)
    i_nom = max(float(I_nominal_ats_A), 1e-9)
    uso = (i_carga / i_nom) * 100.0
    limite = float(factor_uso_max) * 100.0
    ok = uso <= limite
    margen = (i_nom * float(factor_uso_max)) - i_carga
    return {
        "ok": ok,
        "uso_pct": round(uso, 3),
        "margen_A": round(margen, 3),
        "observacion": "OK" if ok else "Corriente ATS excedida sobre limite operativo",
    }


def verificar_protecciones_modo_ge(
    circuitos: list,
    Icc_ge_subtrans_kA: float,
    Icc_ge_perm_kA: float
) -> list:
    out = []
    ikpp_a = float(Icc_ge_subtrans_kA) * 1000.0
    ikperm_a = float(Icc_ge_perm_kA) * 1000.0
    for c in (circuitos or []):
        nombre = c.get("nombre", "SIN_NOMBRE")
        curva = str(c.get("curva", "C")).upper()
        in_a = float(c.get("In_A", c.get("proteccion_A", 0.0)) or 0.0)
        icu = float(c.get("Icu_kA", c.get("poder_corte_kA", 0.0)) or 0.0)
        im = _curve_multiplier(curva) * in_a

        pdc_ok = icu >= float(Icc_ge_subtrans_kA)
        disparo_subtrans_ok = im < ikpp_a
        alerta_perm = im > ikperm_a
        ok = pdc_ok and disparo_subtrans_ok and not alerta_perm
        if not pdc_ok:
            obs = "FALLA_PDC"
        elif alerta_perm:
            obs = "ALERTA_PERM"
        elif not disparo_subtrans_ok:
            obs = "VERIFICAR_DISPARO"
        else:
            obs = "OK"

        out.append({
            "nombre": nombre,
            "Icu_kA": round(icu, 3),
            "Im_A": round(im, 3),
            "Ikpp_A": round(ikpp_a, 3),
            "Ikperm_A": round(ikperm_a, 3),
            "ok": ok,
            "observacion": obs,
        })
    return out


def calcular_ats(
    nombre: str,
    modelo_ats: str,
    I_nominal_A: float,
    V_nominal_V: float,
    modo_transferencia: str,
    I_carga_A: float,
    Sn_ge_kVA: float,
    Xd_pp_pct: float = 20.0,
    Xd_p_pct: float = 28.0,
    Xd_pct: float = 120.0,
    R1_pct: float = 2.0,
    Rs_ohm: float = None,
    X0_pct: float = 5.0,
    t_deteccion_ms: float = T_DETECCION_DEFAULT_MS,
    t_arranque_ge_ms: float = T_ARRANQUE_GE_DEFAULT_MS,
    t_estabilizacion_ge_ms: float = T_ESTABILIZACION_DEFAULT_MS,
    t_paralelo_ms: float = 150.0,
    V_red_V: float = None,
    V_ge_V: float = None,
    f_red_Hz: float = None,
    f_ge_Hz: float = None,
    fase_red_deg: float = 0.0,
    fase_ge_deg: float = 0.0,
    circuitos: list = None
) -> dict:
    modo = str(modo_transferencia or "open").strip().lower()
    desc = MODOS_TRANSFERENCIA.get(modo, MODOS_TRANSFERENCIA["open"])

    corriente = verificar_corriente_ats(I_carga_A, I_nominal_A)
    tiempos = calcular_tiempos_transferencia(
        modo=modo,
        t_deteccion_ms=t_deteccion_ms,
        t_arranque_ge_ms=t_arranque_ge_ms,
        t_estabilizacion_ge_ms=t_estabilizacion_ge_ms,
        t_paralelo_ms=t_paralelo_ms,
    )
    icc = calcular_icc_ge_ats(
        Sn_kVA=Sn_ge_kVA,
        Vn_V=V_nominal_V,
        Xd_pp_pct=Xd_pp_pct,
        Xd_p_pct=Xd_p_pct,
        Xd_pct=Xd_pct,
        R1_pct=R1_pct,
        Rs_ohm=Rs_ohm,
        X0_pct=X0_pct,
    )

    sync = None
    sync_warning = None
    if modo == "closed":
        if None in (V_red_V, V_ge_V, f_red_Hz, f_ge_Hz):
            sync_warning = "Faltan datos V/f para validar sincronizacion closed transition"
        else:
            sync = verificar_sincronizacion(
                V_fuente1_V=V_red_V,
                V_fuente2_V=V_ge_V,
                f_fuente1_Hz=f_red_Hz,
                f_fuente2_Hz=f_ge_Hz,
                fase_fuente1_deg=fase_red_deg,
                fase_fuente2_deg=fase_ge_deg,
            )

    protecciones = verificar_protecciones_modo_ge(
        circuitos or [],
        Icc_ge_subtrans_kA=icc["Ik3_pp_kA"],
        Icc_ge_perm_kA=icc["Ik3_kA"],
    )

    return {
        "nombre": str(nombre),
        "modelo_ats": str(modelo_ats),
        "modo_transferencia": modo,
        "descripcion_modo": desc,
        "I_nominal_A": float(I_nominal_A),
        "I_carga_A": float(I_carga_A),
        "corriente": corriente,
        "tiempos": tiempos,
        "icc_ge": icc,
        "sincronizacion": sync,
        "sincronizacion_warning": sync_warning,
        "protecciones_modo_ge": protecciones,
        "deriva_sts_m11": modo == "sts",
    }
