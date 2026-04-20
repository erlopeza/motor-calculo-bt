from ats import (
    calcular_ats,
    calcular_icc_ge_ats,
    calcular_tiempos_transferencia,
    verificar_corriente_ats,
    verificar_protecciones_modo_ge,
    verificar_sincronizacion,
)


def test_icc_ge_subtransitorio():
    r = calcular_icc_ge_ats(Sn_kVA=650, Vn_V=400, Xd_pp_pct=14.0, Xd_p_pct=20.0, Xd_pct=120.0, R1_pct=2.0, X0_pct=5.0)
    assert r["Ik3_pp_kA"] > 2.0


def test_icc_ge_transitorio():
    r = calcular_icc_ge_ats(Sn_kVA=650, Vn_V=400, Xd_pp_pct=14.0, Xd_p_pct=20.0, Xd_pct=120.0)
    assert r["Ik3_p_kA"] < r["Ik3_pp_kA"]


def test_icc_ge_permanente():
    r = calcular_icc_ge_ats(Sn_kVA=650, Vn_V=400, Xd_pp_pct=14.0, Xd_p_pct=20.0, Xd_pct=120.0)
    assert r["Ik3_kA"] < r["Ik3_p_kA"]


def test_icc_ge_monofasico():
    r = calcular_icc_ge_ats(Sn_kVA=650, Vn_V=400, Xd_pp_pct=14.0, X0_pct=5.0)
    assert r["Ik1_pp_kA"] > 0


def test_icc_ge_defaults():
    r = calcular_icc_ge_ats(Sn_kVA=500, Vn_V=400)
    assert r["usa_defaults"] is True


def test_icc_ge_parametros_reales():
    r = calcular_icc_ge_ats(
        Sn_kVA=650, Vn_V=400,
        Xd_pp_pct=14.0, Xd_p_pct=18.0, Xd_pct=90.0, R1_pct=1.2, X0_pct=3.5
    )
    assert r["usa_defaults"] is False


def test_sync_ok():
    r = verificar_sincronizacion(400, 408, 50.0, 50.1, 0, 3)
    assert r["ok"] is True


def test_sync_falla_dv():
    r = verificar_sincronizacion(400, 424, 50.0, 50.1, 0, 3)
    assert r["ok"] is False


def test_sync_falla_df():
    r = verificar_sincronizacion(400, 404, 50.0, 50.31, 0, 3)
    assert r["ok"] is False


def test_sync_falla_fase():
    r = verificar_sincronizacion(400, 404, 50.0, 50.1, 0, 7)
    assert r["ok"] is False


def test_tiempos_open():
    r = calcular_tiempos_transferencia("open")
    assert r["t_interrupcion_ms"] > 0


def test_tiempos_closed():
    r = calcular_tiempos_transferencia("closed")
    assert r["t_interrupcion_ms"] == 0
    assert r["requiere_sincronizacion"] is True


def test_tiempos_sts():
    r = calcular_tiempos_transferencia("sts")
    assert "M11" in r["observacion"]


def test_tiempos_soft():
    r = calcular_tiempos_transferencia("soft")
    assert r["t_interrupcion_ms"] == 0


def test_corriente_ats_ok():
    r = verificar_corriente_ats(I_carga_A=120, I_nominal_ats_A=250)
    assert r["ok"] is True


def test_corriente_ats_excedida():
    r = verificar_corriente_ats(I_carga_A=230, I_nominal_ats_A=250)
    assert r["ok"] is False


def test_protecciones_modo_ge_ok():
    r = verificar_protecciones_modo_ge(
        [{"nombre": "C1", "In_A": 50, "curva": "D", "Icu_kA": 36}],
        Icc_ge_subtrans_kA=3.0,
        Icc_ge_perm_kA=1.0,
    )
    assert r[0]["observacion"] in ("OK", "ALERTA_PERM", "VERIFICAR_DISPARO")


def test_protecciones_modo_ge_falla_pdc():
    r = verificar_protecciones_modo_ge(
        [{"nombre": "C1", "In_A": 50, "curva": "D", "Icu_kA": 2.0}],
        Icc_ge_subtrans_kA=3.0,
        Icc_ge_perm_kA=1.0,
    )
    assert r[0]["observacion"] == "FALLA_PDC"


def test_protecciones_modo_ge_alerta_perm():
    r = verificar_protecciones_modo_ge(
        [{"nombre": "C1", "In_A": 160, "curva": "D", "Icu_kA": 36}],
        Icc_ge_subtrans_kA=6.0,
        Icc_ge_perm_kA=2.0,
    )
    assert r[0]["observacion"] in ("ALERTA_PERM", "VERIFICAR_DISPARO")


def test_calcular_ats_open_completo():
    r = calcular_ats(
        nombre="ATS-01",
        modelo_ats="SOCOMEC",
        I_nominal_A=250,
        V_nominal_V=400,
        modo_transferencia="open",
        I_carga_A=120,
        Sn_ge_kVA=650,
        circuitos=[{"nombre": "C1", "In_A": 40, "curva": "D", "Icu_kA": 25}],
    )
    assert r["modo_transferencia"] == "open"
    assert r["corriente"]["ok"] is True


def test_calcular_ats_closed_completo():
    r = calcular_ats(
        nombre="ATS-02",
        modelo_ats="SOCOMEC",
        I_nominal_A=250,
        V_nominal_V=400,
        modo_transferencia="closed",
        I_carga_A=120,
        Sn_ge_kVA=650,
        V_red_V=400,
        V_ge_V=404,
        f_red_Hz=50.0,
        f_ge_Hz=50.1,
        fase_red_deg=0.0,
        fase_ge_deg=3.0,
        circuitos=[{"nombre": "C1", "In_A": 40, "curva": "D", "Icu_kA": 25}],
    )
    assert r["modo_transferencia"] == "closed"
    assert r["sincronizacion"] is not None
