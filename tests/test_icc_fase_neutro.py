import math

import pytest

from icc_punto import calcular_icc_fase_neutro, verificar_disparo_proteccion


def test_icc_fn_calculo_basico():
    r = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=6)
    assert r["Icc_fn_A"] > 0
    assert r["Icc_fn_kA"] == round(r["Icc_fn_A"] / 1000, 6)


def test_icc_fn_u0_es_fase_neutro():
    r = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=6)
    assert r["U0_V"] == round(380 / math.sqrt(3), 3)


def test_icc_fn_zs_incluye_fase_y_neutro():
    r = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=6)
    assert r["Z_cable_fase_ohm"] == r["Z_cable_neutro_ohm"]
    assert r["Zs_total_ohm"] == pytest.approx(
        r["Zt_fuente_ohm"] + 2 * r["Z_cable_fase_ohm"],
        abs=2e-6,
    )


def test_icc_fn_circuito_largo_reduce_icc():
    corto = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=6)
    largo = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=200, S_mm2=6)
    assert largo["Icc_fn_A"] < corto["Icc_fn_A"]


def test_icc_fn_seccion_mayor_aumenta_icc():
    s6 = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=6)
    s16 = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=16)
    assert s16["Icc_fn_A"] > s6["Icc_fn_A"]


def test_verificar_disparo_cumple():
    r = verificar_disparo_proteccion(
        Icc_fn_A=500,
        Ia_A=200,
        U0_V=220,
        Zs_total_ohm=1.0,
    )
    assert r["dispara"] is True
    assert r["cumple_iec"] is True


def test_verificar_disparo_no_cumple():
    r = verificar_disparo_proteccion(
        Icc_fn_A=100,
        Ia_A=200,
        U0_V=220,
        Zs_total_ohm=2.0,
    )
    assert r["dispara"] is False
    assert r["cumple_iec"] is False


def test_verificar_disparo_margen_positivo():
    r = verificar_disparo_proteccion(500, 200, 220, 1.0)
    assert r["margen_A"] > 0


def test_verificar_disparo_margen_negativo():
    r = verificar_disparo_proteccion(100, 200, 220, 2.0)
    assert r["margen_A"] < 0


def test_icc_fn_retorna_norma_correcta():
    r = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=6)
    assert "IEC 60364-4-41" in r["norma_calculo"]


def test_verificar_disparo_retorna_norma():
    r = verificar_disparo_proteccion(500, 200, 220, 1.0)
    assert "IEC 60364-4-41 §411.4.4" == r["norma"]


def test_icc_fn_c_min_afecta_resultado():
    conservador = calcular_icc_fase_neutro(
        Vn_V=380,
        Zt_fuente_ohm=0.01,
        L_m=50,
        S_mm2=6,
        c_min=0.95,
    )
    nominal = calcular_icc_fase_neutro(
        Vn_V=380,
        Zt_fuente_ohm=0.01,
        L_m=50,
        S_mm2=6,
        c_min=1.0,
    )
    assert conservador["Icc_fn_A"] != nominal["Icc_fn_A"]
    assert conservador["Icc_fn_A"] < nominal["Icc_fn_A"]
