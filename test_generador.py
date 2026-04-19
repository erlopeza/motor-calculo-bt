import pytest

from generador import (
    COS_PHI_GE_DEFAULT,
    calcular_autonomia,
    calcular_derrateo_altitud,
    calcular_dv_arranque_ge,
    calcular_generador,
    calcular_icc_ge,
    calcular_potencia_minima_ge,
    verificar_ge_seleccionado,
    verificar_protecciones_modo_ge,
)


def test_derrateo_sin_altitud():
    assert calcular_derrateo_altitud(0) == 1.0


def test_derrateo_3000_msnm():
    assert calcular_derrateo_altitud(3000) == 0.8


def test_derrateo_sobre_4000():
    with pytest.raises(ValueError):
        calcular_derrateo_altitud(4500)


def test_potencia_minima_ge():
    r = calcular_potencia_minima_ge(
        P_demanda_kW=200.0,
        P_motor_max_kW=50.0,
        factor_arranque_motor=6.0,
        altitud_msnm=0.0,
        margen=1.25,
    )
    assert r["P_minimo_kW"] == 562.5
    assert r["P_minimo_kVA"] == 703.125
    assert r["P_estandar_kVA"] == 750


def test_potencia_minima_con_derrateo():
    r = calcular_potencia_minima_ge(
        P_demanda_kW=200.0,
        P_motor_max_kW=50.0,
        factor_arranque_motor=6.0,
        altitud_msnm=3000.0,
        margen=1.25,
    )
    assert r["factor_derrateo"] == 0.8
    assert r["P_estandar_kVA"] >= 900


def test_verificar_ge_suficiente():
    r = verificar_ge_seleccionado(
        modelo_ge="RCS500B-C",
        P_ge_kVA_prime=1000,
        P_ge_kVA_emergencia=1100,
        cos_phi_ge=0.8,
        P_demanda_kW=300,
        P_motor_max_kW=30,
        factor_arranque_motor=6.0,
        altitud_msnm=0,
        regimen_uso="prime",
    )
    assert r["ok"] is True
    assert r["margen_kVA"] > 0


def test_verificar_ge_insuficiente():
    r = verificar_ge_seleccionado(
        modelo_ge="RCS500B-C",
        P_ge_kVA_prime=200,
        P_ge_kVA_emergencia=220,
        cos_phi_ge=0.8,
        P_demanda_kW=250,
        P_motor_max_kW=40,
        factor_arranque_motor=6.0,
        altitud_msnm=0,
        regimen_uso="prime",
    )
    assert r["ok"] is False
    assert r["margen_kVA"] < 0


def test_icc_ge_nominal():
    r = calcular_icc_ge(P_kVA=500.0, V_nominal=380.0, Xd_pct=25.0)
    assert r["Icc_nominal_kA"] > 0
    assert r["Icc_max_kA"] > r["Icc_nominal_kA"]
    assert r["Icc_min_kA"] < r["Icc_nominal_kA"]


def test_dv_arranque_ge_ok():
    r = calcular_dv_arranque_ge(
        P_motor_kW=15.0,
        factor_arranque=2.0,
        P_ge_kVA=500.0,
        V_nominal=380.0,
    )
    assert r["dv_pct"] < 15.0
    assert r["estado"] in ("OK_CRITICO", "OK")


def test_dv_arranque_ge_critico():
    r = calcular_dv_arranque_ge(
        P_motor_kW=110.0,
        factor_arranque=6.0,
        P_ge_kVA=150.0,
        V_nominal=380.0,
    )
    assert r["dv_pct"] > 15.0
    assert r["estado"] == "CRITICO"


def test_autonomia_uso_alto():
    r = calcular_autonomia(
        P_demanda_kW=300.0,
        P_ge_prime_kW=400.0,
        consumo_100_galhr=26.41,
        consumo_75_galhr=20.20,
        capacidad_tanque_gal=160.0,
        consumo_50_galhr=14.91,
    )
    assert r["uso_pct"] == 75.0
    assert 20.0 <= r["consumo_estimado_galhr"] <= 20.3


def test_autonomia_ok():
    r = calcular_autonomia(
        P_demanda_kW=100.0,
        P_ge_prime_kW=400.0,
        consumo_100_galhr=26.41,
        consumo_75_galhr=20.20,
        capacidad_tanque_gal=300.0,
        consumo_50_galhr=14.91,
    )
    assert r["autonomia_hr"] >= 6.0
    assert r["autonomia_ok"] is True


def test_protecciones_modo_ge_ok():
    r = verificar_protecciones_modo_ge(
        [{"nombre": "C1", "proteccion_A": 40, "curva": "MA"}],
        Icc_ge_kA=0.3,
    )
    assert len(r) == 1
    assert r[0]["ok"] is True


def test_protecciones_modo_ge_falla():
    r = verificar_protecciones_modo_ge(
        [{"nombre": "C1", "proteccion_A": 10, "curva": "MA"}],
        Icc_ge_kA=0.2,
    )
    assert len(r) == 1
    assert r[0]["ok"] is False
    assert r[0]["observacion"] == "VERIFICAR"


def test_calcular_generador_completo():
    r = calcular_generador(
        nombre="GE-01",
        modelo_ge="RCS500B-C",
        P_ge_kVA_prime=404,
        P_ge_kVA_emergencia=445,
        cos_phi_ge=COS_PHI_GE_DEFAULT,
        V_nominal=380.0,
        regimen_uso="prime",
        P_demanda_kW=250.0,
        P_motor_max_kW=40.0,
        factor_arranque_motor=6.0,
        altitud_msnm=30.0,
        consumo_100_galhr=26.41,
        consumo_75_galhr=20.20,
        capacidad_tanque_gal=160.0,
        circuitos=[{"nombre": "C1", "proteccion_A": 25, "curva": "D"}],
    )
    for key in [
        "potencia_requerida",
        "verificacion_ge",
        "icc_ge",
        "dv_arranque_ge",
        "autonomia",
        "protecciones_modo_ge",
    ]:
        assert key in r
    assert isinstance(r["protecciones_modo_ge"], list)
