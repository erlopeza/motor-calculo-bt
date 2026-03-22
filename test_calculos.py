# ============================================================
# test_calculos.py
# Responsabilidad: verificar que los cálculos son correctos
# Cómo ejecutar: pytest test_calculos.py -v
# ============================================================

import pytest

from calculos import (
    calcular_caida_tension,
    calcular_potencia,
    clasificar_caida,
    capacidad_corregida,
    sugerir_conductor,
)
from transformador import (
    calcular_icc_transformador,
    icc_desde_tabla,
    clasificar_icc,
)
from icc_punto import (
    calcular_zt_cable,
    calcular_icc_punto,
    reduccion_icc,
)

# ============================================================
# TESTS DE CAÍDA DE TENSIÓN
# ============================================================

def test_caida_trifasico_basico():
    dV_V, dV_pct = calcular_caida_tension(10, 13.3, 63, 1, "3F")
    assert dV_V   == 1.436
    assert dV_pct == 0.378

def test_caida_trifasico_largo():
    dV_V, dV_pct = calcular_caida_tension(80, 33.6, 63, 1, "3F")
    assert dV_V   == 4.546
    assert dV_pct == 1.196

def test_caida_trifasico_paralelos():
    dV_V, dV_pct = calcular_caida_tension(15, 203.0, 500, 4, "3F")
    assert dV_V   == 0.28
    assert dV_pct == 0.074

def test_caida_monofasico():
    dV_V, dV_pct = calcular_caida_tension(80, 3.31, 16, 1, "1F")
    assert dV_V   == 13.535
    assert dV_pct == 6.152

def test_caida_bifasico():
    dV_V, dV_pct = calcular_caida_tension(15, 5.26, 25, 1, "2F")
    assert dV_V   == 2.495
    assert dV_pct == 1.134

# ============================================================
# TESTS DE POTENCIA
# ============================================================

def test_potencia_trifasico():
    assert calcular_potencia(63, 0.85, "3F") == 35244

def test_potencia_monofasico():
    assert calcular_potencia(16, 1.0, "1F") == 3520

def test_potencia_bifasico():
    assert calcular_potencia(25, 0.90, "2F") == 4950

# ============================================================
# TESTS DE CLASIFICACIÓN NORMATIVA
# ============================================================

def test_clasificacion_optimo():
    assert clasificar_caida(0.378) == "ÓPTIMO"
    assert clasificar_caida(1.5)   == "ÓPTIMO"

def test_clasificacion_aceptable():
    assert clasificar_caida(1.512) == "ACEPTABLE"
    assert clasificar_caida(3.0)   == "ACEPTABLE"

def test_clasificacion_precaucion():
    assert clasificar_caida(3.1)   == "PRECAUCIÓN"
    assert clasificar_caida(5.0)   == "PRECAUCIÓN"

def test_clasificacion_falla():
    assert clasificar_caida(5.1)   == "FALLA"
    assert clasificar_caida(6.152) == "FALLA"

# ============================================================
# TESTS DE CAPACIDAD CORREGIDA POR TEMPERATURA
# ============================================================

def test_capacidad_temperatura_referencia():
    assert capacidad_corregida(65, 1, 30) == 65.0

def test_capacidad_temperatura_alta():
    assert capacidad_corregida(115, 1, 35) == 110.4

def test_capacidad_paralelos():
    assert capacidad_corregida(335, 4, 30) == 1340.0

# ============================================================
# TESTS DE SUGERENCIA DE CONDUCTOR
# ============================================================

def test_sugerencia_conductor_falla():
    cond, mm2, dv = sugerir_conductor(80, 16, 1, "1F", 35)
    assert cond == "8AWG"
    assert mm2  == 8.37
    assert dv   == 2.433

def test_sugerencia_conductor_ok():
    cond, mm2, dv = sugerir_conductor(10, 63, 1, "3F", 30)
    assert cond is not None
    assert dv <= 3.0

# ============================================================
# TESTS DEL TRANSFORMADOR — PARAMETRIZADOS
# ============================================================

@pytest.mark.parametrize("kVA, Vn, Ucc, Icc_min, Icc_max, In_esperado", [
    (1000, 380, 5.0, 30.0, 31.0, 1519.8),
    (400,  380, 4.0, 15.0, 16.0,  607.9),
    (630,  380, 4.0, 23.0, 25.0,  957.3),
    (250,  380, 4.0,  9.0, 10.0,  379.9),
    (160,  380, 4.0,  6.0,  7.0,  243.1),
])
def test_icc_transformador(kVA, Vn, Ucc, Icc_min, Icc_max, In_esperado):
    Icc_kA, Zt_ohm, datos = calcular_icc_transformador(kVA, Vn, Ucc)
    assert Icc_min <= Icc_kA <= Icc_max
    assert Zt_ohm > 0
    assert datos["Ucc_pct"] == Ucc
    assert datos["kVA"] == kVA

# ============================================================
# TESTS MODO B — tabla típica IEC 60076
# ============================================================

@pytest.mark.parametrize("kVA_entrada, kVA_ref_esperado, Ucc_esperado", [
    (950,  1000, 5.0),
    (1050, 1000, 5.0),
    (300,   250, 4.0),
    (500,   400, 4.0),
    (100,   100, 4.0),
])
def test_icc_desde_tabla(kVA_entrada, kVA_ref_esperado, Ucc_esperado):
    Icc_kA, Ucc_pct, kVA_ref = icc_desde_tabla(kVA_entrada)
    assert kVA_ref == kVA_ref_esperado
    assert Ucc_pct == Ucc_esperado
    assert Icc_kA  > 0

# ============================================================
# TESTS DE CLASIFICACIÓN DE Icc
# ============================================================

@pytest.mark.parametrize("Icc_kA, texto_esperado", [
    (5.0,  "BAJO"),
    (8.0,  "MEDIO"),
    (20.0, "ALTO"),
    (35.0, "MUY ALTO"),
    (55.0, "EXTREMO"),
])
def test_clasificacion_icc(Icc_kA, texto_esperado):
    assert texto_esperado in clasificar_icc(Icc_kA)

# ============================================================
# TESTS DE Icc EN PUNTO — MÓDULO 2
# ============================================================

@pytest.mark.parametrize("L, S, par, Zt_esperado", [
    (10,  13.3,  1, 0.013158),
    (80,  33.6,  1, 0.041667),
    (15, 203.0,  4, 0.000323),
    (20,  53.5,  1, 0.006542),
])
def test_zt_cable(L, S, par, Zt_esperado):
    """Verifica impedancia resistiva del cable."""
    Zt = calcular_zt_cable(L, S, par)
    assert abs(Zt - Zt_esperado) < 0.0001

def test_icc_punto_crac():
    """CRAC 1-A — Icc en punto debe ser menor que en bornes."""
    Zt_trafo = 0.007220
    Icc_kA, Zt_total, Zt_cable = calcular_icc_punto(
        Zt_trafo, 10, 13.3, 1, "3F"
    )
    assert Icc_kA < 30.39
    assert Icc_kA > 0
    assert Zt_total > Zt_trafo

def test_icc_punto_antenna_largo():
    """Antenna Panel 80m — reducción importante, Icc positiva."""
    Zt_trafo = 0.007220
    Icc_kA, _, _ = calcular_icc_punto(
        Zt_trafo, 80, 33.6, 1, "3F"
    )
    assert Icc_kA < 30.39   # menor que en bornes
    assert Icc_kA > 3.0     # positiva y significativa

def test_reduccion_icc():
    """Reducción positiva, menor al 100%, dentro de rango."""
    reduccion = reduccion_icc(30.39, 15.0)
    assert 0 < reduccion < 100
    assert 50.0 <= reduccion <= 51.0   # rango — tolerancia redondeo