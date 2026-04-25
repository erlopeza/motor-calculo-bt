import pytest

from src.arranque_motores import (
    calcular_arranque_completo,
    corriente_arranque,
    corriente_nominal,
    metodo_arranque,
    seleccionar_guardamotor,
)


def test_corriente_nominal_motor_5kw_380v():
    assert corriente_nominal(5.0, 380.0, 0.85, 0.92) == pytest.approx(9.71, abs=0.01)


def test_corriente_nominal_motor_22kw():
    assert corriente_nominal(22.0, 380.0, 0.86, 0.93) == pytest.approx(41.79, abs=0.01)


def test_corriente_nominal_error_potencia_negativa():
    with pytest.raises(ValueError):
        corriente_nominal(-1.0, 380.0, 0.85, 0.92)


def test_corriente_nominal_error_fp_invalido():
    with pytest.raises(ValueError):
        corriente_nominal(5.0, 380.0, 1.1, 0.92)


def test_corriente_arranque_factor_defecto():
    assert corriente_arranque(10.0) == 60.0


def test_corriente_arranque_factor_custom():
    assert corriente_arranque(10.0, factor_ia=7.0) == 70.0


def test_corriente_arranque_error_negativo():
    with pytest.raises(ValueError):
        corriente_arranque(0.0)


def test_metodo_dol_motor_pequeno():
    resultado = metodo_arranque(5.5)
    assert resultado["metodo"] == "DOL"
    assert resultado["reduccion_corriente_pct"] == 0.0


def test_metodo_estrella_triangulo():
    resultado = metodo_arranque(15.0)
    assert resultado["metodo"] == "Estrella-Triangulo"
    assert resultado["reduccion_corriente_pct"] == 33.0


def test_metodo_variador():
    resultado = metodo_arranque(45.0)
    assert resultado["metodo"] == "Variador de frecuencia"
    assert resultado["reduccion_corriente_pct"] == 70.0


def test_metodo_limite_exacto_7_5kw():
    assert metodo_arranque(7.5)["metodo"] == "DOL"


def test_guardamotor_rango_correcto():
    resultado = seleccionar_guardamotor(8.5)
    assert resultado["rango_min"] == 6.3
    assert resultado["rango_max"] == 10.0
    assert resultado["ajuste_recomendado"] == 8.5


def test_guardamotor_error_fuera_tabla():
    with pytest.raises(ValueError):
        seleccionar_guardamotor(200.0)


def test_arranque_completo_motor_11kw():
    resultado = calcular_arranque_completo(11.0, 380.0, 0.86, 0.93)

    assert set(resultado.keys()) == {"in_a", "ia_arranque_a", "metodo", "guardamotor"}
    assert resultado["in_a"] > 0
    assert resultado["ia_arranque_a"] == round(resultado["in_a"] * 6.0, 2)
    assert resultado["metodo"]["metodo"] == "Estrella-Triangulo"
    assert resultado["guardamotor"]["rango_min"] <= resultado["in_a"] <= resultado["guardamotor"]["rango_max"]
