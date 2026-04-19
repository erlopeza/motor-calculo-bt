from trafo_iso import (
    calcular_corriente_nominal,
    calcular_dv_trafo,
    calcular_icc_secundario,
    calcular_trafo_iso,
    verificar_capacidad_trafo,
)


def test_capacidad_trafo_ok():
    r = verificar_capacidad_trafo(P_carga_kVA=150, P_trafo_kVA=250)
    assert r["ok"] is True
    assert r["uso_pct"] == 60.0


def test_capacidad_trafo_excedida():
    r = verificar_capacidad_trafo(P_carga_kVA=230, P_trafo_kVA=250)
    assert r["ok"] is False
    assert r["uso_pct"] > 80.0


def test_corriente_nominal_3F():
    i = calcular_corriente_nominal(P_kVA=250, V_nominal=380, sistema="3F")
    assert 379.0 <= i <= 380.5


def test_icc_secundario_nominal():
    r = calcular_icc_secundario(P_kVA=250, V_nominal=380, Ucc_pct=5.0)
    assert 7.5 <= r["Icc_nominal_kA"] <= 7.7


def test_icc_con_tolerancia():
    r = calcular_icc_secundario(P_kVA=250, V_nominal=380, Ucc_pct=5.0)
    assert r["Icc_max_kA"] > r["Icc_nominal_kA"]
    assert r["Icc_min_kA"] < r["Icc_nominal_kA"]


def test_dv_trafo_ok():
    r = calcular_dv_trafo(P_carga_kVA=100, P_trafo_kVA=250, Ucc_pct=5.0, cos_phi=0.9)
    assert r["ok"] is True
    assert r["dv_pct"] <= 3.0


def test_calcular_trafo_iso_completo():
    r = calcular_trafo_iso(
        nombre="TISO-01",
        P_trafo_kVA=250,
        V_primario=380,
        V_secundario=220,
        conexion="Dyn5",
        P_carga_kVA=150,
        cos_phi=0.9,
        Ucc_pct=5.0,
        n_trafos=1,
        modo="servicio",
    )
    for k in ["capacidad", "I_nominal_sec_A", "icc_secundario", "dv_trafo"]:
        assert k in r


def test_trafo_dyn5():
    r = calcular_trafo_iso(
        nombre="TISO-02",
        P_trafo_kVA=250,
        V_primario=380,
        V_secundario=220,
        conexion="Dyn5",
        P_carga_kVA=120,
    )
    assert r["conexion"] == "Dyn5"


def test_n_trafos_redundancia():
    r = calcular_trafo_iso(
        nombre="TISO-RED",
        P_trafo_kVA=250,
        V_primario=380,
        V_secundario=220,
        conexion="Dyn5",
        P_carga_kVA=200,
        n_trafos=2,
    )
    assert r["n_trafos"] == 2
    assert "multiple" in r["observacion_configuracion"].lower()


def test_trafo_modo_bypass():
    r = calcular_trafo_iso(
        nombre="TISO-BYP",
        P_trafo_kVA=250,
        V_primario=380,
        V_secundario=220,
        conexion="Dyn5",
        P_carga_kVA=120,
        modo="bypass",
    )
    assert r["modo"] == "bypass"
