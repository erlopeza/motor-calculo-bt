import math

from calculos import (
    calcular_caida_acumulada,
    calcular_caida_alimentador,
    calcular_caida_tension,
)


def test_caida_acumulada_suma_correcta():
    r = calcular_caida_acumulada(2.0, 2.0)
    assert r["dv_total_pct"] == 4.0


def test_caida_acumulada_clasificacion_optimo():
    r = calcular_caida_acumulada(0.5, 0.5)
    assert r["clasificacion"] == "óptimo"
    assert r["cumple_ric"] is True


def test_caida_acumulada_clasificacion_aceptable():
    r = calcular_caida_acumulada(1.0, 1.5)
    assert r["clasificacion"] == "aceptable"
    assert r["cumple_ric"] is True


def test_caida_acumulada_clasificacion_precaucion():
    r = calcular_caida_acumulada(2.0, 2.0)
    assert r["clasificacion"] == "precaución"
    assert r["cumple_ric"] is True


def test_caida_acumulada_clasificacion_falla():
    r = calcular_caida_acumulada(3.0, 3.0)
    assert r["clasificacion"] == "falla"
    assert r["cumple_ric"] is False


def test_caida_acumulada_limite_exacto_5pct():
    r = calcular_caida_acumulada(2.0, 3.0)
    assert r["dv_total_pct"] == 5.0
    assert r["cumple_ric"] is True


def test_caida_acumulada_limite_superado():
    r = calcular_caida_acumulada(2.0, 3.01)
    assert r["dv_total_pct"] == 5.01
    assert r["cumple_ric"] is False


def test_caida_alimentador_wrapper_consistente():
    p_w = 50000.0
    v_v = 380.0
    fp = 0.9
    i_diseno = p_w / (math.sqrt(3.0) * v_v * fp)
    _, dv_pct = calcular_caida_tension(50.0, 35.0, i_diseno, 1, "3F")

    r = calcular_caida_alimentador(
        P_W=p_w,
        L_m=50.0,
        S_mm2=35.0,
        Vn_V=v_v,
        sistema="3F",
        cos_phi=fp,
    )

    assert r["dV_pct"] == dv_pct
    assert r["es_alimentador"] is True


def test_caida_acumulada_retorna_norma():
    r = calcular_caida_acumulada(1.0, 1.0)
    assert r["norma"] == "RIC N°10 / NCh Elec. 4/2003"


def test_caida_acumulada_campos_completos():
    r = calcular_caida_acumulada(1.0, 2.0)
    assert set(r.keys()) == {
        "dv_alimentador_pct",
        "dv_circuito_pct",
        "dv_total_pct",
        "clasificacion",
        "cumple_ric",
        "norma",
    }
