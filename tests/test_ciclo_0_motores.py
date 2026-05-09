from src.arranque_motores import calcular_arranque_completo
from motores import (
    calcular_corriente_arranque,
    calcular_motor,
)


def _motor_base(**overrides):
    datos = {
        "nombre": "M-BOMBA-01",
        "P_kW": 11.0,
        "V_nominal": 380.0,
        "cos_phi": 0.86,
        "rendimiento": 0.93,
        "sistema": "1F",
        "tipo_arranque": "directo",
        "regimen": "permanente",
        "periodo_min": 60,
        "L_m": 25.0,
        "S_mm2_conductor": 25.0,
        "proteccion_A": 63.0,
        "curva": "D",
        "factor_arranque": 6.5,
        "temperatura": 35.0,
        "Icc_punto": 5000.0,
        "norma": "MM2",
    }
    datos.update(overrides)
    return datos


def test_motor_sin_defaults_no_marca_usa_defaults():
    r = calcular_motor(**_motor_base())
    assert r["usa_defaults"] is False
    assert r["defaults_aplicados"] == []


def test_motor_con_factor_arranque_none_marca_default():
    r = calcular_motor(**_motor_base(factor_arranque=None))
    assert r["usa_defaults"] is True
    assert "factor_arranque" in r["defaults_aplicados"]
    assert isinstance(r["factor_arranque_efectivo"], float)
    assert r["factor_arranque_efectivo"] == r["arranque"]["factor_arranque_efectivo"]


def test_motor_con_sistema_3f_default_marca():
    r = calcular_motor(**_motor_base(sistema="3F"))
    assert r["usa_defaults"] is True
    assert "sistema" in r["defaults_aplicados"]


def test_motor_con_temperatura_default_marca():
    r = calcular_motor(**_motor_base(temperatura=30.0))
    assert r["usa_defaults"] is True
    assert "temperatura" in r["defaults_aplicados"]


def test_motor_lista_defaults_siempre_es_lista():
    r = calcular_motor(**_motor_base())
    assert isinstance(r["defaults_aplicados"], list)
    assert r["defaults_aplicados"] == []


def test_fachada_arranque_motores_mantiene_api_simplificada():
    r = calcular_arranque_completo(11.0, 380.0, 0.86, 0.93)
    assert set(r.keys()) == {"in_a", "ia_arranque_a", "metodo", "guardamotor"}

    canonico = calcular_corriente_arranque(r["in_a"], "directo", factor_arranque=6.0)
    assert canonico["usa_defaults"] is False
    assert canonico["defaults_aplicados"] == []
