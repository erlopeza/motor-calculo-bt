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

# ============================================================
# TESTS DE CAÍDA DE TENSIÓN
# Valores verificados manualmente contra el reporte real
# ============================================================

def test_caida_trifasico_basico():
    """CRAC Unit 1-A — 3F / 6AWG / 63A / 10m"""
    dV_V, dV_pct = calcular_caida_tension(10, 13.3, 63, 1, "3F")
    assert dV_V   == 1.436
    assert dV_pct == 0.378

def test_caida_trifasico_largo():
    """Antenna Panel campo — 3F / 2AWG / 63A / 80m"""
    dV_V, dV_pct = calcular_caida_tension(80, 33.6, 63, 1, "3F")
    assert dV_V   == 4.546
    assert dV_pct == 1.196

def test_caida_trifasico_paralelos():
    """Alimentacion UPS 1 — 3F / 4x400MCM / 500A / 15m"""
    dV_V, dV_pct = calcular_caida_tension(15, 203.0, 500, 4, "3F")
    assert dV_V   == 0.28
    assert dV_pct == 0.074

def test_caida_monofasico():
    """Iluminacion HUB — 1F / 12AWG / 16A / 80m"""
    dV_V, dV_pct = calcular_caida_tension(80, 3.31, 16, 1, "1F")
    assert dV_V   == 13.535
    assert dV_pct == 6.152

def test_caida_bifasico():
    """Mini Split 1-A — 2F / 10AWG / 25A / 15m"""
    dV_V, dV_pct = calcular_caida_tension(15, 5.26, 25, 1, "2F")
    assert dV_V   == 2.495
    assert dV_pct == 1.134

# ============================================================
# TESTS DE POTENCIA
# ============================================================

def test_potencia_trifasico():
    """CRAC Unit 1-A — 3F / 63A / cosφ=0.85"""
    assert calcular_potencia(63, 0.85, "3F") == 35244

def test_potencia_monofasico():
    """Iluminacion HUB — 1F / 16A / cosφ=1.0"""
    assert calcular_potencia(16, 1.0, "1F") == 3520

def test_potencia_bifasico():
    """Mini Split 1-A — 2F / 25A / cosφ=0.90"""
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
    """6AWG a 30°C — sin corrección"""
    assert capacidad_corregida(65, 1, 30) == 65.0

def test_capacidad_temperatura_alta():
    """2AWG a 35°C — factor 0.96"""
    assert capacidad_corregida(115, 1, 35) == 110.4

def test_capacidad_paralelos():
    """4x400MCM a 30°C"""
    assert capacidad_corregida(335, 4, 30) == 1340.0

# ============================================================
# TESTS DE SUGERENCIA DE CONDUCTOR
# ============================================================

def test_sugerencia_conductor_falla():
    """12AWG falla en 1F/80m/16A — debe sugerir 8AWG"""
    cond, mm2, dv = sugerir_conductor(80, 16, 1, "1F", 35)
    assert cond == "8AWG"
    assert mm2  == 8.37
    assert dv   == 2.433

def test_sugerencia_conductor_ok():
    """Circuito que cumple — sugerencia dentro del límite"""
    cond, mm2, dv = sugerir_conductor(10, 63, 1, "3F", 30)
    assert cond is not None
    assert dv <= 3.0

# ============================================================
# TESTS DEL TRANSFORMADOR — PARAMETRIZADOS
# Un solo test verifica múltiples transformadores
# Agregar un caso nuevo = agregar una línea a la tabla
# ============================================================

@pytest.mark.parametrize("kVA, Vn, Ucc, Icc_min, Icc_max, In_esperado", [
    (1000, 380, 5.0, 30.0, 31.0, 1519.8),   # LEO ARICA — caso real
    (400,  380, 4.0, 15.0, 16.0,  607.9),   # transformador mediano
    (630,  380, 4.0, 23.0, 25.0,  957.3),   # transformador grande
    (250,  380, 4.0,  9.0, 10.0,  379.9),   # transformador pequeño
    (160,  380, 4.0,  6.0,  7.0,  243.1),   # transformador chico
])
def test_icc_transformador(kVA, Vn, Ucc, Icc_min, Icc_max, In_esperado):
    """
    Verifica Icc en bornes BT para distintos transformadores.
    Usa rangos en lugar de valores exactos — tolerancia de redondeo.
    """
    Icc_kA, Zt_ohm, datos = calcular_icc_transformador(kVA, Vn, Ucc)
    assert Icc_min <= Icc_kA <= Icc_max   # dentro del rango esperado
    assert Zt_ohm > 0                      # impedancia positiva
    assert datos["Ucc_pct"] == Ucc        # dato de entrada correcto
    assert datos["kVA"] == kVA            # potencia correcta

# ============================================================
# TESTS MODO B — tabla típica IEC 60076
# ============================================================

@pytest.mark.parametrize("kVA_entrada, kVA_ref_esperado, Ucc_esperado", [
    (950,  1000, 5.0),   # cerca de 1000 → usa 1000
    (1050, 1000, 5.0),   # cerca de 1000 → usa 1000
    (300,   250, 4.0),   # cerca de 250 → usa 250
    (500,   400, 4.0),   # cerca de 400 → usa 400
    (100,   100, 4.0),   # exacto 100 → usa 100
])
def test_icc_desde_tabla(kVA_entrada, kVA_ref_esperado, Ucc_esperado):
    """
    Modo B — verifica que busca el kVA más cercano en la tabla.
    """
    Icc_kA, Ucc_pct, kVA_ref = icc_desde_tabla(kVA_entrada)
    assert kVA_ref  == kVA_ref_esperado
    assert Ucc_pct  == Ucc_esperado
    assert Icc_kA   > 0

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
    """Verifica clasificación por nivel de cortocircuito."""
    resultado = clasificar_icc(Icc_kA)
    assert texto_esperado in resultado