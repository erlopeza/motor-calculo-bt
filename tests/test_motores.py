from motores import (
    FACTORES_NCH_1228,
    calcular_corriente_arranque,
    calcular_corriente_motor,
    calcular_dv_arranque,
    calcular_motor,
    dimensionar_conductor_motor,
    seleccionar_guardamotor,
    verificar_proteccion_arranque,
)


def test_corriente_motor_3F():
    i = calcular_corriente_motor(15.0, 380.0, 0.85, 0.92, "3F")
    assert 29.10 <= i <= 29.20


def test_corriente_motor_1F():
    i = calcular_corriente_motor(2.2, 220.0, 0.85, 0.90, "1F")
    assert 13.0 <= i <= 13.2


def test_arranque_directo_default():
    r = calcular_corriente_arranque(29.14, "directo")
    assert r["factor_usado"] == 6.0
    assert r["en_rango_tipico"] is True


def test_arranque_factor_personalizado():
    r_ok = calcular_corriente_arranque(29.14, "directo", factor_arranque=7.5)
    r_bad = calcular_corriente_arranque(29.14, "directo", factor_arranque=9.0)
    assert r_ok["en_rango_tipico"] is True
    assert r_bad["en_rango_tipico"] is False


def test_arranque_estrella_triangulo():
    r = calcular_corriente_arranque(29.14, "estrella_triangulo")
    assert r["factor_usado"] == 2.0


def test_dv_arranque_ok():
    r = calcular_dv_arranque(40.0, 10.0, 35.0, "3F", 380.0)
    assert r["dv_pct"] < 15.0
    assert r["estado"] == "OK"


def test_dv_arranque_critico():
    r = calcular_dv_arranque(220.0, 120.0, 3.31, "1F", 220.0)
    assert r["dv_pct"] > 15.0
    assert r["estado"] == "CRITICO"


def test_conductor_permanente():
    r = dimensionar_conductor_motor(40.0, "permanente", 60, norma="AWG")
    assert r["factor_regimen"] == 1.25
    assert r["I_diseño"] == 50.0


def test_conductor_intermitente_5min():
    r = dimensionar_conductor_motor(40.0, "intermitente", 5, norma="AWG")
    assert r["factor_regimen"] == FACTORES_NCH_1228["intermitente"][5]
    assert r["I_diseño"] == 34.0


def test_guardamotor_rango_cubre_In():
    r = seleccionar_guardamotor(29.14)
    assert r["rango_min"] == 25.0
    assert r["rango_max"] == 40.0


def test_proteccion_MA_ok():
    r = verificar_proteccion_arranque(165.0, 40.0, "MA")
    assert r["ok"] is True


def test_proteccion_MA_falla():
    r = verificar_proteccion_arranque(250.0, 16.0, "MA")
    assert r["ok"] is False


def test_calcular_motor_completo():
    r = calcular_motor(
        nombre="BOMBA-01",
        P_kW=15.0,
        V_nominal=380.0,
        cos_phi=0.85,
        rendimiento=0.92,
        sistema="3F",
        tipo_arranque="directo",
        regimen="permanente",
        periodo_min=999,
        L_m=20.0,
        S_mm2_conductor=None,
        proteccion_A=40.0,
        curva="MA",
        factor_arranque=None,
        temperatura=30.0,
        Icc_punto=10000.0,
        norma="AWG",
    )
    for key in [
        "nombre", "I_n", "arranque", "conductor", "dv_nominal",
        "dv_arranque", "guardamotor", "proteccion"
    ]:
        assert key in r
    assert r["arranque"]["I_arranque"] > r["I_n"]
