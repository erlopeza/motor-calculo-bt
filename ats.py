import math

from generador import calcular_icc_ge, get_parametros_alternador

# ============================================================
# CONSTANTES - clasificacion por origen
# TIPO A: parametro de proyecto - DEBE ser ingresado por usuario
# TIPO B: constante normada - no modificar sin cambiar norma
# TIPO C: criterio de diseno - cambiar solo con justificacion
# ============================================================

MODOS_TRANSFERENCIA = {
    "open": "Open Transition - interrupcion breve (100-500ms)",
    "closed": "Closed Transition - suave, requiere sincronizacion",
    "sts": "Static Transfer - < 4ms (ver modulo STS)",
    "soft": "Soft Load - via UPS/variador, transparente",
}

SYNC_DV_MAX_PCT = 5.0  # TIPO B - IEC 60947-6-1 8.3 sincronismo de tension
SYNC_DF_MAX_HZ = 0.2  # TIPO B - IEC 60947-6-1 8.3 sincronismo de frecuencia
SYNC_DFASE_MAX_DEG = 5.0  # TIPO B - IEC 60947-6-1 8.3 sincronismo de fase
T_PARALELO_MAX_MS = 200.0  # TIPO B - IEC 60947-6-1 closed transition

T_DETECCION_DEFAULT_MS = 3000.0  # TIPO A - DEFAULT: configurable por logica AMF
T_ARRANQUE_GE_DEFAULT_MS = 10000.0  # TIPO A - DEFAULT: verificar con ficha GE
T_ESTABILIZACION_DEFAULT_MS = 5000.0  # TIPO A - DEFAULT: verificar con regulador AVR
T_CIERRE_CONTACTOR_MS = 200.0  # TIPO C - tiempo tipico de maniobra


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


def _defaults_tiempos_aplicados(
    t_deteccion_ms: float,
    t_arranque_ge_ms: float,
    t_estabilizacion_ge_ms: float
) -> list:
    defaults = []
    if float(t_deteccion_ms) == T_DETECCION_DEFAULT_MS:
        defaults.append("t_deteccion_ms")
    if float(t_arranque_ge_ms) == T_ARRANQUE_GE_DEFAULT_MS:
        defaults.append("t_arranque_ge_ms")
    if float(t_estabilizacion_ge_ms) == T_ESTABILIZACION_DEFAULT_MS:
        defaults.append("t_estabilizacion_ge_ms")
    return defaults


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
    icc = calcular_icc_ge(
        P_kVA=Sn_ge_kVA,
        V_nominal=V_nominal_V,
        Xd_pp_pct=Xd_pp_pct,
        Xd_p_pct=Xd_p_pct,
        Xd_pct=Xd_pct,
        R1_pct=R1_pct,
        Rs_ohm=Rs_ohm,
        X0_pct=X0_pct,
    )
    defaults_aplicados = _defaults_tiempos_aplicados(
        t_deteccion_ms=t_deteccion_ms,
        t_arranque_ge_ms=t_arranque_ge_ms,
        t_estabilizacion_ge_ms=t_estabilizacion_ge_ms,
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
        "usa_defaults": bool(defaults_aplicados),
        "defaults_aplicados": defaults_aplicados,
    }
