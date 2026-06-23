"""Regresión: K_CURVA B/C/D deriva del catálogo tcc (fuente única) sin cambiar números."""
from coordinacion import K_CURVA, calcular_tiempo_disparo


def test_kcurva_bcd_valores_esperados():
    # Valores concretos (IEC 60898 / catálogo DATA-3): no cambian al unificar.
    assert K_CURVA["B"] == 45
    assert K_CURVA["C"] == 80
    assert K_CURVA["D"] == 180


def test_kcurva_conserva_TM():
    assert K_CURVA["TM"] == 100

def test_tiempo_termico_identico_tras_unificar():
    # Curva C, In=100, I=150 (región térmica) → t = 80/(1.5²) = 35.556 s
    r = calcular_tiempo_disparo(150.0, 100.0, "C")
    assert r["region"] == "termico"
    assert round(r["t_s"], 3) == 35.556
