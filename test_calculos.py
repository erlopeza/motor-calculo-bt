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
    # ============================================================
# TESTS DE PROTECCIONES — MÓDULO 3
# ============================================================
from protecciones import (
    calcular_umbral_magnetico,
    verificar_disparo,
    verificar_poder_de_corte,
    verificar_circuito_completo,
    clasificar_margen_disparo,
)

@pytest.mark.parametrize("In_A, curva, Im_min_esp, Im_max_esp", [
    (63,  "C",  315.0,  630.0),   # Antena Panel — curva C
    (16,  "C",   80.0,  160.0),   # Iluminacion HUB — curva C
    (200, "TM", 1200.0, 2000.0),  # CRAC — curva TM
    (25,  "C",  125.0,  250.0),   # Tomacorriente — curva C
    (16,  "C",   80.0,  160.0),   # Mini Split — curva C
])
def test_umbral_magnetico(In_A, curva, Im_min_esp, Im_max_esp):
    """Verifica umbrales de disparo por curva."""
    Im_min, Im_max = calcular_umbral_magnetico(In_A, curva)
    assert Im_min == Im_min_esp
    assert Im_max == Im_max_esp

def test_disparo_crac_tm():
    """
    CRAC Unit 1-A — TM200 / Icc=10.77kA
    Im_min = 200 × 6 = 1200A
    Icc_punto = 10770A → 10770 > 1200 → dispara con margen amplio
    """
    puede, margen, Im_min = verificar_disparo(10770, 200, "TM")
    assert puede == True
    assert Im_min == 1200.0
    assert margen > 50   # margen amplio

def test_disparo_iluminacion_critico():
    """
    Iluminacion HUB — C16 / Icc=0.26kA = 260A
    Im_min = 16 × 5 = 80A
    260A > 80A → dispara, pero margen bajo
    """
    puede, margen, Im_min = verificar_disparo(260, 16, "C")
    assert puede == True
    assert Im_min == 80.0
    assert margen > 0

def test_poder_de_corte_suficiente():
    """CRAC: Icu=36kA ≥ Icc=10.77kA → suficiente"""
    ok, margen = verificar_poder_de_corte(10.77, 36)
    assert ok == True
    assert margen > 0

def test_poder_de_corte_insuficiente():
    """Caso hipotético: Icu=6kA < Icc=10kA → insuficiente"""
    ok, margen = verificar_poder_de_corte(10.0, 6.0)
    assert ok == False
    assert margen < 0

@pytest.mark.parametrize("margen, clasif_esperada", [
    (-5.0,  "NO DISPARA"),
    ( 5.0,  "MARGEN CRÍTICO"),
    (30.0,  "MARGEN ACEPTABLE"),
    (100.0, "MARGEN AMPLIO"),
])
def test_clasificacion_margen(margen, clasif_esperada):
    resultado = clasificar_margen_disparo(margen)
    assert clasif_esperada in resultado

def test_verificacion_completa_ok():
    """CRAC 1-A — todo debe estar OK."""
    r = verificar_circuito_completo("CRAC Unit 1-A", 200, "TM", 36, 10.77, 380)
    assert r["estado"] == "OK"
    assert r["puede_disparar"] == True
    assert r["poder_ok"] == True

def test_verificacion_completa_falla_disparo():
    """Caso extremo: Icc muy baja — no puede disparar."""
    r = verificar_circuito_completo("Prueba", 200, "TM", 36, 0.05, 380)
    assert "FALLA DISPARO" in r["estado"]
    # ============================================================
# TESTS DE BALANCE — MÓDULO 4
# ============================================================
from balance import obtener_fs, calcular_balance_tableros, FACTORES_SIMULTANEIDAD

def test_fs_critica():
    assert obtener_fs("critica") == 1.0

def test_fs_hvac():
    """HVAC tratado igual que critica según decisión del proyecto."""
    assert obtener_fs("hvac") == 1.0

def test_fs_tomacorriente():
    assert obtener_fs("tomacorriente") == 0.5

def test_fs_motor():
    assert obtener_fs("motor") == 0.75

def test_fs_desconocido():
    """Tipo desconocido usa fs=1.0 como fallback conservador."""
    assert obtener_fs("desconocido") == 1.0

def test_balance_mcp():
    """
    Balance básico — MDP con 2 circuitos simples.
    Verifica que la suma y el porcentaje son correctos.
    """
    circuitos = [
        {"nombre": "C1", "sistema": "3F", "I_diseno": 63,
         "cos_phi": 0.85, "S_mm2": 13.3, "paralelos": 1,
         "L_m": 10, "temp_amb": 30, "I_max": 65, "conductor": "6AWG"},
        {"nombre": "C2", "sistema": "1F", "I_diseno": 16,
         "cos_phi": 1.0, "S_mm2": 3.31, "paralelos": 1,
         "L_m": 80, "temp_amb": 35, "I_max": 25, "conductor": "12AWG"},
    ]
    balance_datos = {
        "C1": {"tablero": "MDP", "fase": "L1", "tipo_carga": "critica"},
        "C2": {"tablero": "MDP", "fase": "L3", "tipo_carga": "iluminacion"},
    }
    tableros_datos = {"MDP": 1000}

    r = calcular_balance_tableros(circuitos, balance_datos, tableros_datos, 1000)

    assert "MDP" in r["tableros"]
    assert r["tableros"]["MDP"]["S_total_kva"] > 0
    assert r["tableros"]["MDP"]["uso_pct"] < 100
    assert r["tableros"]["MDP"]["estado"] == "OK"
    assert r["uso_trafo_pct"] > 0
    assert r["estado_trafo"] == "OK"
# ============================================================
# TESTS DE DEMANDA — MÓDULO 6
# ============================================================
from demanda import (
    obtener_fd, calcular_corriente_alimentador,
    seleccionar_transformador, dimensionar_acometida_sec,
    calcular_demanda, FACTORES_DEMANDA
)

# --- Factor de demanda ---

def test_fd_datacenter_critica():
    assert obtener_fd("datacenter", "critica") == 1.0

def test_fd_datacenter_tomacorriente():
    assert obtener_fd("datacenter", "tomacorriente") == 0.50

def test_fd_comercial_hvac():
    assert obtener_fd("comercial", "hvac") == 0.85

def test_fd_industrial_motor():
    assert obtener_fd("industrial", "motor") == 0.75

def test_fd_residencial_alumbrado():
    assert obtener_fd("residencial", "alumbrado") == 0.66

def test_fd_desconocido_fallback():
    """Tipo desconocido retorna 1.0 — criterio conservador."""
    assert obtener_fd("industrial", "inexistente") == 1.0

def test_fd_insensible_mayusculas():
    assert obtener_fd("DATACENTER", "CRITICA") == 1.0

# --- Corriente alimentador ---

def test_corriente_3F_1000kva():
    """1000 kVA / 380V trifásico → 1519.3 A"""
    I = calcular_corriente_alimentador(1000, 380, "3F")
    assert abs(I - 1519.3) < 1.0

def test_corriente_1F_10kva():
    """10 kVA / 220V monofásico → 45.5 A"""
    I = calcular_corriente_alimentador(10, 220, "1F")
    assert abs(I - 45.5) < 1.0

def test_corriente_cero():
    assert calcular_corriente_alimentador(0, 380, "3F") == 0.0

# --- Selección transformador ---

def test_trafo_876kva_selecciona_1250():
    """876.7 kVA / 0.80 = 1095.9 → próximo IEC = 1250 kVA"""
    r = seleccionar_transformador(876.7)
    assert r["kVA_seleccionado"] == 1250

def test_trafo_uso_dentro_80():
    """500 kVA selecciona 630 → uso = 79.4% → OK"""
    r = seleccionar_transformador(500)
    assert r["kVA_seleccionado"] == 630
    assert r["estado"] == "OK"

def test_trafo_kva_minimo_correcto():
    """kVA_minimo = S / 0.80"""
    r = seleccionar_transformador(800)
    assert abs(r["kVA_minimo"] - 1000.0) < 0.1

# --- Acometida SEC ---

def test_sec_urbana_icc():
    r = dimensionar_acometida_sec(100, 220, "1F", "urbana")
    assert r["Icc_kA"] == 6.0

def test_sec_rural_icc():
    r = dimensionar_acometida_sec(100, 220, "1F", "rural")
    assert r["Icc_kA"] == 2.0

def test_sec_proteccion_125pct():
    """Protección mínima = I_alim × 1.25"""
    r = dimensionar_acometida_sec(100, 220, "1F", "urbana")
    I = calcular_corriente_alimentador(100, 220, "1F")
    assert abs(r["I_prot_min_A"] - round(I * 1.25, 1)) < 0.1

# --- Integración calcular_demanda ---

def test_demanda_integracion_basica():
    """
    Proyecto básico: 2 circuitos datacenter.
    CRAC 3F 63A → critica Fd=1.0
    Tomacorriente 1F 20A → tomacorriente Fd=0.5
    """
    circuitos = [
        {"nombre": "CRAC-1", "sistema": "3F", "I_diseno": 63,
         "cos_phi": 0.85, "S_mm2": 13.3, "paralelos": 1,
         "L_m": 10, "temp_amb": 30, "I_max": 65,
         "conductor": "6AWG"},
        {"nombre": "TOM-1", "sistema": "1F", "I_diseno": 20,
         "cos_phi": 1.0, "S_mm2": 5.26, "paralelos": 1,
         "L_m": 25, "temp_amb": 30, "I_max": 35,
         "conductor": "10AWG"},
    ]
    balance_datos = {
        "CRAC-1": {"tablero": "MDP", "fase": "L1", "tipo_carga": "critica"},
        "TOM-1":  {"tablero": "MDP", "fase": "L2", "tipo_carga": "tomacorriente"},
    }
    params = {
        "tipo_instalacion":   "datacenter",
        "cos_phi_global":     0.85,
        "factor_crecimiento": 1.0,
        "tension_alim":       380,
        "sistema_alim":       "3F",
    }

    r = calcular_demanda(circuitos, balance_datos, params)

    assert r["S_total_kva"] > 0
    assert r["I_alim_A"] > 0
    # CRAC Fd=1.0, TOM Fd=0.5 → demanda TOM = mitad
    tom = next(d for d in r["detalle"] if d["nombre"] == "TOM-1")
    assert tom["Fd"] == 0.5
    assert tom["P_dem_kw"] == round(tom["P_inst_kw"] * 0.5, 3)