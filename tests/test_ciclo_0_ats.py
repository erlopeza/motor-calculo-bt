from pathlib import Path

import ats
import generador
from ats import calcular_ats


def _ats_base(**overrides):
    datos = {
        "nombre": "ATS-X",
        "modelo_ats": "GENERICO",
        "I_nominal_A": 400,
        "V_nominal_V": 400,
        "modo_transferencia": "open",
        "I_carga_A": 160,
        "Sn_ge_kVA": 650,
        "Xd_pp_pct": 14.0,
        "Xd_p_pct": 18.0,
        "Xd_pct": 90.0,
        "R1_pct": 1.2,
        "Rs_ohm": 0.003,
        "X0_pct": 3.5,
        "t_deteccion_ms": 2500.0,
        "t_arranque_ge_ms": 9000.0,
        "t_estabilizacion_ge_ms": 4500.0,
    }
    datos.update(overrides)
    return datos


def test_ats_no_contiene_string_stamford():
    texto = Path(ats.__file__).read_text(encoding="utf-8")
    assert "stamford" not in texto.lower()
    assert "calcular_icc_ge_ats" not in texto


def test_ats_reutiliza_calcular_icc_ge_de_generador():
    assert ats.calcular_icc_ge is generador.calcular_icc_ge


def test_ats_resultado_icc_igual_a_generador_directo():
    params = _ats_base()
    directo = generador.calcular_icc_ge(
        P_kVA=params["Sn_ge_kVA"],
        V_nominal=params["V_nominal_V"],
        Xd_pp_pct=params["Xd_pp_pct"],
        Xd_p_pct=params["Xd_p_pct"],
        Xd_pct=params["Xd_pct"],
        R1_pct=params["R1_pct"],
        Rs_ohm=params["Rs_ohm"],
        X0_pct=params["X0_pct"],
    )
    via_ats = calcular_ats(**params)
    assert abs(via_ats["icc_ge"]["Ik3_pp_kA"] - directo["Ik3_pp_kA"]) < 0.001
    assert abs(via_ats["icc_ge"]["Ik3_kA"] - directo["Ik3_kA"]) < 0.001


def test_ats_usa_defaults_true_si_tiempos_no_especificados():
    params = _ats_base()
    params.pop("t_deteccion_ms")
    params.pop("t_arranque_ge_ms")
    params.pop("t_estabilizacion_ge_ms")
    r = calcular_ats(**params)
    assert r["usa_defaults"] is True
    assert "t_deteccion_ms" in r["defaults_aplicados"]
    assert "t_arranque_ge_ms" in r["defaults_aplicados"]
    assert "t_estabilizacion_ge_ms" in r["defaults_aplicados"]


def test_ats_sin_defaults_si_tiempos_provistos():
    r = calcular_ats(**_ats_base())
    assert r["usa_defaults"] is False
    assert r["defaults_aplicados"] == []


def test_ats_no_duplica_norm_to_pu():
    assert not hasattr(ats, "_norm_to_pu")
    assert not hasattr(ats, "_norm_r_to_pu")
