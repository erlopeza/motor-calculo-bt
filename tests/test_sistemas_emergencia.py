import pytest

from src.sistemas_emergencia import (
    autonomia_requerida,
    calcular_emergencia_completo,
    clasificar_grupo,
    potencia_generador,
)


def test_clasificar_iluminacion_evacuacion():
    assert clasificar_grupo("iluminacion_evacuacion")["grupo"] == 0


def test_clasificar_ups_servidores():
    assert clasificar_grupo("ups_servidores")["grupo"] == 2


def test_clasificar_bomba_incendio():
    assert clasificar_grupo("bomba_incendio")["grupo"] == 1


def test_clasificar_tipo_invalido():
    with pytest.raises(ValueError):
        clasificar_grupo("carga_no_normada")


def test_autonomia_grupo0_edificio_bajo():
    resultado = autonomia_requerida(0, num_pisos=5, tipo_recinto="general")
    assert resultado["autonomia_min"] == 60
    assert resultado["fuente_recomendada"] == "baterias"


def test_autonomia_grupo0_edificio_alto():
    assert autonomia_requerida(0, num_pisos=6)["autonomia_min"] == 120


def test_autonomia_grupo0_asistencial():
    assert autonomia_requerida(0, num_pisos=2, tipo_recinto="asistencial")["autonomia_min"] == 120


def test_autonomia_grupo1_generador():
    resultado = autonomia_requerida(1)
    assert resultado["autonomia_min"] == 120
    assert resultado["fuente_recomendada"] == "generador"


def test_autonomia_grupo2_ups():
    resultado = autonomia_requerida(2)
    assert resultado["autonomia_min"] == -1
    assert resultado["fuente_recomendada"] == "ups"


def test_autonomia_grupo_invalido():
    with pytest.raises(ValueError):
        autonomia_requerida(9)


def test_potencia_generador_basico():
    resultado = potencia_generador([10, 20, 5], fp=0.8, margen_pct=25)
    assert resultado["p_total_kw"] == 35.0
    assert resultado["p_con_margen_kw"] == 43.75
    assert resultado["s_requerido_kva"] == 54.69


def test_potencia_generador_margen_cero():
    resultado = potencia_generador([10, 20], fp=0.8, margen_pct=0)
    assert resultado["p_con_margen_kw"] == 30.0
    assert resultado["s_requerido_kva"] == 37.5


def test_potencia_generador_lista_vacia():
    with pytest.raises(ValueError):
        potencia_generador([])


def test_potencia_generador_fp_invalido():
    with pytest.raises(ValueError):
        potencia_generador([10], fp=0)


def test_emergencia_completo_sala_cirugia():
    resultado = calcular_emergencia_completo("sala_cirugia", 6, [12, 8], tipo_recinto="asistencial")
    assert set(resultado.keys()) == {"grupo", "autonomia", "generador"}
    assert resultado["grupo"]["grupo"] == 2
    assert resultado["autonomia"]["fuente_recomendada"] == "ups"
    assert resultado["generador"]["p_total_kw"] == 20.0


def test_emergencia_completo_iluminacion():
    resultado = calcular_emergencia_completo("iluminacion_evacuacion", 3, [2.5, 1.5])
    assert resultado["grupo"]["grupo"] == 0
    assert resultado["autonomia"]["autonomia_min"] == 60
