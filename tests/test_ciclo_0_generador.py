from pathlib import Path

import generador
from generador import calcular_generador, calcular_icc_ge, get_parametros_alternador
from presets.alternadores.stamford_hci544d import get_parametros as get_hci544d


def _generador_base(**overrides):
    datos = {
        "nombre": "GE-X",
        "modelo_ge": "MAQUINA_PARAMETRICA",
        "P_ge_kVA_prime": 650,
        "P_ge_kVA_emergencia": 715,
        "cos_phi_ge": 0.8,
        "V_nominal": 400,
        "regimen_uso": "prime",
        "P_demanda_kW": 220,
        "P_motor_max_kW": 30,
        "factor_arranque_motor": 4.0,
        "altitud_msnm": 0,
        "Xd_pp_pct": 14.0,
        "Xd_p_pct": 18.0,
        "Xd_pct": 90.0,
        "R1_pct": 1.2,
        "Rs_ohm": 0.003,
        "X0_pct": 3.5,
    }
    datos.update(overrides)
    return datos


def test_generador_acepta_cualquier_maquina_via_parametros():
    r = calcular_generador(**_generador_base(P_ge_kVA_prime=900, V_nominal=480))
    assert r["icc_ge"]["Ik3_pp_kA"] > r["icc_ge"]["Ik3_p_kA"] > r["icc_ge"]["Ik3_kA"]
    assert r["usa_defaults"] is False
    assert r["defaults_aplicados"] == []


def test_stamford_como_preset_reproduce_resultado_actual():
    p = get_parametros_alternador("stamford_hci544d", Vn_V=400)
    assert p["Xd_pp_pct"] == 0.11
    assert p["Xd_p_pct"] == 0.15
    assert p["Xd_pct"] == 3.17
    assert p["X0_pct"] == 0.10
    assert p["Rs_ohm"] == 0.0041
    assert p["Sn_base_kVA"] == 625.0
    p_380 = get_hci544d(Vn_V=380, Sn_kVA=404)
    r = calcular_icc_ge(
        P_kVA=404,
        V_nominal=380,
        Xd_pp_pct=p_380["Xd_pp_pct"],
        Xd_p_pct=p_380["Xd_p_pct"],
        Xd_pct=p_380["Xd_pct"],
        Rs_ohm=p_380["Rs_ohm"],
        X0_pct=p_380["X0_pct"],
    )
    assert 5.2 <= r["Ik3_pp_kA"] <= 5.5


def test_generador_modelo_inexistente_usa_defaults():
    p = get_parametros_alternador("modelo_que_no_existe", Vn_V=400)
    assert p["usa_defaults"] is True
    assert p["modelo_no_encontrado"] == "modelo_que_no_existe"
    assert p["Xd_pp_pct"] == generador.XD_PP_DEFAULT


def test_generador_usa_defaults_true_si_falta_xd_pp():
    datos = _generador_base(Xd_pp_pct=generador.XD_PP_DEFAULT)
    r = calcular_generador(**datos)
    assert r["usa_defaults"] is True
    assert "Xd_pp_pct" in r["defaults_aplicados"]
    assert r["icc_ge"]["usa_defaults"] is True


def test_calcular_generador_sin_defaults_declara_lista_vacia():
    r = calcular_generador(**_generador_base())
    assert r["usa_defaults"] is False
    assert r["defaults_aplicados"] == []


def test_generador_no_contiene_marca_comercial_en_runtime():
    texto = Path(generador.__file__).read_text(encoding="utf-8")
    assert "stamford" not in texto.lower()
    assert "STAMFORD_HCI544D_W14" not in texto
