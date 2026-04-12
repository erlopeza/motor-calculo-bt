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
# ============================================================
# TESTS DE COORDINACIÓN TCC — MÓDULO 7
# ============================================================
from coordinacion import (
    calcular_tiempo_disparo, verificar_selectividad_par,
    verificar_iec60364, verificar_cadena
)

# --- Tiempos de disparo ---

def test_disparo_curva_c_instantaneo():
    """Curva C 32A — Icc=1000A > Ii_max(10×In=320A) → instantáneo"""
    r = calcular_tiempo_disparo(1000, 32, "C", Ii_xIn=10)
    assert r["dispara"] == True
    assert r["t_s"] == 0.02
    assert r["region"] == "instantaneo"

def test_disparo_curva_c_termico():
    """Curva C 32A — Icc=100A en región térmica"""
    r = calcular_tiempo_disparo(100, 32, "C", Ir_xIn=1.0)
    assert r["dispara"] == True
    assert r["region"] == "termico"
    assert r["t_s"] > 0

def test_disparo_etu_tiempo_corto():
    """ETU600 1600A — Icc=5000A > Isd=2.5×In=4000A → tsd=0.30s"""
    r = calcular_tiempo_disparo(
        5000, 1600, "ETU600",
        Ir_xIn=1.0, Isd_xIr=2.5, tsd_s=0.30, Ii_xIn=10
    )
    assert r["dispara"] == True
    assert r["t_s"] == 0.30
    assert r["region"] == "tiempo_corto"

def test_disparo_etu_instantaneo():
    """ETU600 1600A — Icc=20000A > Ii=10×In=16000A → instantáneo"""
    r = calcular_tiempo_disparo(
        20000, 1600, "ETU600",
        Ir_xIn=1.0, Isd_xIr=2.5, tsd_s=0.30, Ii_xIn=10
    )
    assert r["t_s"] == 0.02
    assert r["region"] == "instantaneo"

def test_disparo_etu_region_termica_no_modelada():
    """ETU — Icc en región térmica → verificar_simaris"""
    r = calcular_tiempo_disparo(
        2000, 1600, "ETU600",
        Ir_xIn=1.0, Isd_xIr=2.5, tsd_s=0.30, Ii_xIn=10
    )
    assert r["region"] == "verificar_simaris"
    assert r["t_s"] is None

def test_disparo_no_dispara():
    """Curva C — Icc < Ir → no dispara"""
    r = calcular_tiempo_disparo(10, 32, "C", Ir_xIn=1.0)
    assert r["dispara"] == False
    assert r["region"] == "no_dispara"

# --- Selectividad entre pares ---

def test_selectividad_total():
    """Inferior dispara en 0.02s, superior en 0.30s → TOTAL"""
    inf = {"t_s": 0.02, "region": "instantaneo", "dispara": True, "nota": ""}
    sup = {"t_s": 0.30, "region": "tiempo_corto", "dispara": True, "nota": ""}
    r = verificar_selectividad_par(inf, sup)
    assert r["selectividad"] == "TOTAL"

def test_selectividad_ninguna():
    """Inferior dispara en 0.30s, superior en 0.02s → NINGUNA"""
    inf = {"t_s": 0.30, "region": "tiempo_corto", "dispara": True, "nota": ""}
    sup = {"t_s": 0.02, "region": "instantaneo",  "dispara": True, "nota": ""}
    r = verificar_selectividad_par(inf, sup)
    assert r["selectividad"] == "NINGUNA"

def test_selectividad_indeterminada():
    """Región no modelada → INDETERMINADA"""
    inf = {"t_s": None, "region": "verificar_simaris", "dispara": None, "nota": ""}
    sup = {"t_s": 0.30, "region": "tiempo_corto",      "dispara": True, "nota": ""}
    r = verificar_selectividad_par(inf, sup)
    assert r["selectividad"] == "INDETERMINADA"

# --- IEC 60364-4-41 ---

def test_iec60364_cumple():
    assert verificar_iec60364(0.02, "3F_380")["cumple"] == True

def test_iec60364_falla():
    """ta-cur=10.622s > t_max=5s → FALLA (caso real BTDP 4.1)"""
    r = verificar_iec60364(10.622, "3F_380")
    assert r["cumple"] == False
    assert r["estado"] == "FALLA"

def test_iec60364_monofasico():
    """t_max = 0.4s para 1F_220"""
    assert verificar_iec60364(0.3, "1F_220")["cumple"] == True
    assert verificar_iec60364(0.5, "1F_220")["cumple"] == False

# --- Cadena completa — caso LEO ARICA Cadena A ---

def test_cadena_leo_arica_modo_red():
    """
    Cadena A Modo Red LEO ARICA:
        G0A: ETU600 1600A  Isd=2.5×In=4000A  tsd=0.30s  Ii=10×In=16000A
        G1A: ETU320  630A  Ii=9×In=5670A
        C2A: Curva C  32A  Ii=10×In=320A

    Icc en punto final = 4490A (circuito antena — dato real M2)

    Con Icc=4490A:
        G0A: Icc(4490) > Isd(4000) → tiempo_corto t=0.30s
        G1A: Icc(4490) < Ii(5670)  → región térmica ETU → verificar_simaris
        C2A: Icc(4490) >> Ii(320)  → instantáneo t=0.02s
    """
    dispositivos = [
        {
            "nombre": "G0A_3WA1600", "nivel": 0,
            "In_A": 1600, "curva": "ETU600",
            "Ir_xIn": 1.0, "Isd_xIr": 2.5, "tsd_s": 0.30, "Ii_xIn": 10
        },
        {
            "nombre": "G1A_3VA630", "nivel": 1,
            "In_A": 630, "curva": "ETU320",
            "Ir_xIn": 0.8, "Isd_xIr": None, "tsd_s": None, "Ii_xIn": 9
        },
        {
            "nombre": "C2A_5SY32", "nivel": 2,
            "In_A": 32, "curva": "C",
            "Ir_xIn": 1.0, "Ii_xIn": 10
        },
    ]

    r = verificar_cadena(dispositivos, Icc_A=4490, sistema="3F_380")

    # C2A (Curva C 32A): Icc=4490 >> Ii_max=320A → instantáneo
    final = r["resultados_disparo"][-1]
    assert final["t_s"] == 0.02
    assert final["region"] == "instantaneo"

    # G0A (ETU600 1600A): Icc=4490 > Isd=4000A → tiempo_corto t=0.30s
    cabecera = r["resultados_disparo"][0]
    assert cabecera["region"] == "tiempo_corto"
    assert cabecera["t_s"] == 0.30

    # G1A (ETU320 630A): Icc=4490 < Ii=5670A, sin Isd → verificar_simaris
    nivel1 = r["resultados_disparo"][1]
    assert nivel1["region"] == "verificar_simaris"

    # Selectividad global: hay región no modelada → INDETERMINADA
    assert r["selectividad_global"] == "INDETERMINADA"

    # IEC 60364-4-41: t_final=0.02s < 5s → OK
    assert r["iec60364_final"]["cumple"] == True
# ============================================================
# TESTS TRANSFORMADOR — IEC 60909 c_max/c_min + tolerancia %Z
# ============================================================
from transformador import reporte_transformador

def test_icc_max_mayor_que_nominal():
    """Icc_max (c=1.1 · %Z mín) > Icc_nominal"""
    _, _, d = calcular_icc_transformador(1000, 380, 5.0)
    assert d["Icc_max_kA"] > d["Icc_kA"]

def test_icc_min_menor_que_nominal():
    """Icc_min (c=0.95 · %Z máx) < Icc_nominal"""
    _, _, d = calcular_icc_transformador(1000, 380, 5.0)
    assert d["Icc_min_kA"] < d["Icc_kA"]

def test_icc_max_leo_arica():
    """LEO ARICA: Icc_max ≈ 36.14 kA con c=1.1 y tol=7.5%"""
    _, _, d = calcular_icc_transformador(1000, 380, 5.0)
    assert 35.0 < d["Icc_max_kA"] < 38.0

def test_icc_min_leo_arica():
    """LEO ARICA: Icc_min ≈ 26.85 kA con c=0.95 y tol=7.5%"""
    _, _, d = calcular_icc_transformador(1000, 380, 5.0)
    assert 25.0 < d["Icc_min_kA"] < 29.0

def test_tolerancia_cero_sin_efecto_en_zt():
    """Sin tolerancia: Zt_min = Zt_max = Zt_nominal"""
    _, _, d = calcular_icc_transformador(1000, 380, 5.0, tolerancia_ucc_pct=0)
    assert d["Zt_min_ohm"] == d["Zt_ohm"]
    assert d["Zt_max_ohm"] == d["Zt_ohm"]

def test_compatibilidad_hacia_atras():
    """Retorno (Icc_kA, Zt_ohm) compatible con código existente"""
    Icc_kA, Zt_ohm, _ = calcular_icc_transformador(1000, 380, 5.0)
    assert isinstance(Icc_kA, float)
    assert isinstance(Zt_ohm, float)
    assert 30.0 <= Icc_kA <= 31.0

def test_reporte_incluye_icc_max_min():
    """El reporte muestra Icc máxima y mínima"""
    _, _, d = calcular_icc_transformador(1000, 380, 5.0)
    lineas = reporte_transformador(d, "A", d["Icc_kA"])
    texto = "\n".join(lineas)
    assert "máxima" in texto
    assert "mínima" in texto
    assert "IEC 60909" in texto

# ============================================================
# TESTS A-3/A-4 — NORMA POR PERFIL
# ============================================================
from perfiles import obtener_perfil

def test_perfil_industrial_norma_awg():
    assert obtener_perfil("industrial")["norma"] == "AWG"

def test_perfil_comercial_norma_mm2():
    assert obtener_perfil("comercial")["norma"] == "MM2"

def test_perfil_domestico_norma_mm2():
    assert obtener_perfil("domestico")["norma"] == "MM2"

def test_sugerir_conductor_norma_awg_explicito():
    cond, mm2, dv = sugerir_conductor(10, 30, 1, "3F", 30, norma="AWG")
    assert cond is not None
    assert "AWG" in cond or "MCM" in cond

def test_sugerir_conductor_norma_mm2():
    cond, mm2, dv = sugerir_conductor(10, 30, 1, "3F", 30, norma="MM2")
    assert cond is not None
    assert "MM2" in cond

def test_sugerir_conductor_mm2_tramo_largo():
    cond, mm2, dv = sugerir_conductor(200, 50, 1, "3F", 30, norma="MM2")
    assert cond is not None
    assert dv <= 3.0

# ============================================================
# TESTS A-8 — INTEGRACIÓN EXCEL + MM2
# ============================================================
import os
from excel import leer_circuitos_excel, enriquecer_circuitos

def test_leer_circuitos_excel_conductor_mm2():
    ruta = os.path.join(os.path.dirname(__file__),
                        "tests", "circuitos_test_mm2.xlsx")
    circuitos = leer_circuitos_excel(ruta)
    assert len(circuitos) == 1
    assert circuitos[0]["conductor"] == "10MM2"

def test_enriquecer_circuitos_mm2():
    ruta = os.path.join(os.path.dirname(__file__),
                        "tests", "circuitos_test_mm2.xlsx")
    circuitos = leer_circuitos_excel(ruta)
    circuitos = enriquecer_circuitos(circuitos, norma="MM2")
    assert circuitos[0]["S_mm2"] == 10.0
    assert circuitos[0]["I_max"] == 50
