# test_conductores.py — versión corregida
import pytest
from conductores import get_tabla_conductores, LIMITE_DV

def test_tabla_awg_carga():
    t = get_tabla_conductores("AWG")
    assert "14AWG" in t
    assert t["6AWG"]["mm2"] == 13.3

def test_tabla_mm2_carga():
    t = get_tabla_conductores("MM2")
    assert "2.5mm2" in t
    assert t["2.5mm2"]["I_max"] == 21

def test_orden_ascendente_mm2():
    t = get_tabla_conductores("MM2")
    secciones = [v["mm2"] for v in t.values()]
    assert secciones == sorted(secciones)

def test_norma_invalida():
    with pytest.raises(ValueError):
        get_tabla_conductores("IEC")

def test_limite_dv():
    assert LIMITE_DV == 3.0