# ============================================================
# test_calculos.py
# Responsabilidad: verificar que los cálculos son correctos
# Cómo ejecutar: pytest test_calculos.py -v
# ============================================================

# Importa las funciones que vamos a verificar
from calculos import (
    calcular_caida_tension,
    calcular_potencia,
    clasificar_caida,
    capacidad_corregida,
    sugerir_conductor,
)

# ============================================================
# TESTS DE CAÍDA DE TENSIÓN
# Valores verificados manualmente contra el reporte real
# ============================================================

def test_caida_trifasico_basico():
    """CRAC Unit 1-A — 3F / 6AWG / 63A / 10m / 30°C"""
    # Estos valores los conocemos del reporte LEO-ARICA
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
    # Con 4 paralelos la sección equivalente es 4 × 203 = 812mm²
    dV_V, dV_pct = calcular_caida_tension(15, 203.0, 500, 4, "3F")
    assert dV_V   == 0.28
    assert dV_pct == 0.074

def test_caida_monofasico():
    """Iluminacion HUB — 1F / 12AWG / 16A / 80m"""
    # Factor 2.0 para monofásico — caída mayor que trifásico
    dV_V, dV_pct = calcular_caida_tension(80, 3.31, 16, 1, "1F")
    assert dV_V   == 13.535
    assert dV_pct == 6.152

def test_caida_bifasico():
    """Mini Split 1-A — 2F / 10AWG / 25A / 15m"""
    # Factor 2.0 igual que monofásico
    dV_V, dV_pct = calcular_caida_tension(15, 5.26, 25, 1, "2F")
    assert dV_V   == 2.495
    assert dV_pct == 1.134

# ============================================================
# TESTS DE POTENCIA
# ============================================================

def test_potencia_trifasico():
    """CRAC Unit 1-A — 3F / 63A / cosφ=0.85"""
    P = calcular_potencia(63, 0.85, "3F")
    assert P == 35244

def test_potencia_monofasico():
    """Iluminacion HUB — 1F / 16A / cosφ=1.0"""
    P = calcular_potencia(16, 1.0, "1F")
    assert P == 3520

def test_potencia_bifasico():
    """Mini Split 1-A — 2F / 25A / cosφ=0.90"""
    P = calcular_potencia(25, 0.90, "2F")
    assert P == 4950

# ============================================================
# TESTS DE CLASIFICACIÓN NORMATIVA
# ============================================================

def test_clasificacion_optimo():
    """Caída ≤ 1.5% debe clasificar como ÓPTIMO"""
    assert clasificar_caida(0.378) == "ÓPTIMO"
    assert clasificar_caida(1.5)   == "ÓPTIMO"

def test_clasificacion_aceptable():
    """Caída entre 1.5% y 3.0% debe clasificar como ACEPTABLE"""
    assert clasificar_caida(1.512) == "ACEPTABLE"
    assert clasificar_caida(3.0)   == "ACEPTABLE"

def test_clasificacion_precaucion():
    """Caída entre 3.0% y 5.0% debe clasificar como PRECAUCIÓN"""
    assert clasificar_caida(3.1)   == "PRECAUCIÓN"
    assert clasificar_caida(5.0)   == "PRECAUCIÓN"

def test_clasificacion_falla():
    """Caída > 5.0% debe clasificar como FALLA"""
    assert clasificar_caida(5.1)   == "FALLA"
    assert clasificar_caida(6.152) == "FALLA"

# ============================================================
# TESTS DE CAPACIDAD CORREGIDA POR TEMPERATURA
# ============================================================

def test_capacidad_temperatura_referencia():
    """A 30°C factor = 1.00 — capacidad sin cambio"""
    # 6AWG = 65A × 1 conductor × factor 1.00
    assert capacidad_corregida(65, 1, 30) == 65.0

def test_capacidad_temperatura_alta():
    """A 35°C factor = 0.96 — capacidad reducida"""
    # 2AWG = 115A × 1 × 0.96 = 110.4A
    assert capacidad_corregida(115, 1, 35) == 110.4

def test_capacidad_paralelos():
    """4x400MCM a 30°C — capacidad total"""
    # 400MCM = 335A × 4 paralelos × 1.00 = 1340A
    assert capacidad_corregida(335, 4, 30) == 1340.0

# ============================================================
# TESTS DE SUGERENCIA DE CONDUCTOR
# ============================================================

def test_sugerencia_conductor_falla():
    """Iluminacion HUB falla con 12AWG — debe sugerir 8AWG"""
    # 1F / 16A / 80m / 35°C — el 12AWG da 6.152% FALLA
    cond, mm2, dv = sugerir_conductor(80, 16, 1, "1F", 35)
    assert cond == "8AWG"
    assert mm2  == 8.37
    assert dv   == 2.433

def test_sugerencia_conductor_ok():
    """Circuito que ya cumple — sugerencia debe ser el conductor mínimo"""
    # 3F / 63A / 10m / 30°C — cualquier conductor desde 6AWG cumple
    cond, mm2, dv = sugerir_conductor(10, 63, 1, "3F", 30)
    assert cond is not None   # debe encontrar algo
    assert dv <= 3.0          # debe estar dentro del límite