"""P1.1 memoria — enriquecer circuitos y sección Arc Flash en la memoria SEC."""
from pathlib import Path
import uuid
from reporteria_sec import enriquecer_circuitos_con_proteccion


def test_enriquecer_agrega_in_y_curva():
    circuitos = [{"nombre": "C-01", "sistema": "3F", "icc_ka": 10.0}]
    protecciones = {"C-01": {"In_A": 250, "curva": "C", "poder_corte_kA": 25}}
    out = enriquecer_circuitos_con_proteccion(circuitos, protecciones)
    assert out[0]["In_A"] == 250
    assert out[0]["curva"] == "C"

def test_enriquecer_sin_proteccion_no_rompe():
    circuitos = [{"nombre": "C-99", "sistema": "3F", "icc_ka": 5.0}]
    out = enriquecer_circuitos_con_proteccion(circuitos, {})
    assert "In_A" not in out[0] or out[0].get("In_A") in (None, 0)

def test_enriquecer_no_muta_original():
    circuitos = [{"nombre": "C-01", "sistema": "3F", "icc_ka": 10.0}]
    enriquecer_circuitos_con_proteccion(circuitos, {"C-01": {"In_A": 100, "curva": "B"}})
    assert "In_A" not in circuitos[0]
