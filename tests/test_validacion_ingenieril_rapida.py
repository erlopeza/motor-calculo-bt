import math

import pytest

from calculos import (
    calcular_caida_tension,
    capacidad_corregida,
    sugerir_conductor,
)
from conductores import get_tabla_conductores
from demanda import obtener_fd
from transformador import calcular_icc_transformador


def test_caida_tension_trifasica_contra_formula_manual():
    """
    Caso patron:
    3F, 380 V, cobre, 10 m, 63 A, 13.3 mm2, 1 paralelo.
    """
    L_m = 10
    S_mm2 = 13.3
    I = 63
    paralelos = 1
    sistema = "3F"

    dV_V, dV_pct = calcular_caida_tension(L_m, S_mm2, I, paralelos, sistema)

    esperado_v = (math.sqrt(3) * 0.0175 * L_m * I) / (S_mm2 * paralelos)
    esperado_pct = esperado_v / 380 * 100

    assert dV_V == pytest.approx(round(esperado_v, 3), abs=0.001)
    assert dV_pct == pytest.approx(round(esperado_pct, 3), abs=0.001)


def test_icc_transformador_respeta_cmax_cmin_y_tolerancia():
    """
    Verifica consistencia IEC 60909 / IEC 60076:
    Icc_max > Icc_nominal > Icc_min.
    """
    icc_nom, zt_ohm, datos = calcular_icc_transformador(1000, 380, 6.0)

    assert datos["c_max"] == 1.10
    assert datos["c_min"] == 0.95
    assert datos["tolerancia_pct"] == 7.5
    assert datos["Zt_min_ohm"] < round(zt_ohm, 6)
    assert datos["Zt_max_ohm"] > round(zt_ohm, 6)
    assert datos["Icc_max_kA"] > icc_nom > datos["Icc_min_kA"]


def test_demanda_factores_tabla_vigente():
    """
    Prueba rapida de la tabla de factores de demanda vigente del proyecto.
    """
    assert obtener_fd("comercial", "alumbrado") == 0.75
    assert obtener_fd("comercial", "tomacorriente") == 0.60
    assert obtener_fd("industrial", "motor") == 0.75
    assert obtener_fd("datacenter", "ups") == 1.00
    assert obtener_fd("desconocido", "alumbrado") == 1.00


def test_tablas_awg_mm2_y_sugerencia_son_consistentes():
    """
    Verifica disponibilidad de ambas normas y sugerencias compatibles.
    """
    tabla_awg = get_tabla_conductores("AWG")
    tabla_mm2 = get_tabla_conductores("MM2")

    assert "6AWG" in tabla_awg
    assert tabla_awg["6AWG"]["mm2"] == 13.3
    assert "10MM2" in tabla_mm2
    assert tabla_mm2["10MM2"]["I_max"] == 50

    nombre_awg, _, dv_awg = sugerir_conductor(
        L_m=20, I_diseno=30, paralelos=1, sistema="3F", temp_amb=30, norma="AWG"
    )
    nombre_mm2, _, dv_mm2 = sugerir_conductor(
        L_m=20, I_diseno=30, paralelos=1, sistema="3F", temp_amb=30, norma="MM2"
    )

    assert nombre_awg is not None
    assert nombre_mm2 is not None
    assert dv_awg <= 3.0
    assert dv_mm2 <= 3.0


def test_regresion_fisica_simple_monotonia():
    """
    Reglas fisicas basicas:
    mayor seccion baja caida, mas longitud sube caida,
    mas paralelos mejora capacidad y caida equivalente.
    """
    dV_seccion_chica, _ = calcular_caida_tension(30, 13.3, 63, 1, "3F")
    dV_seccion_grande, _ = calcular_caida_tension(30, 33.6, 63, 1, "3F")
    assert dV_seccion_grande < dV_seccion_chica

    dV_corto, _ = calcular_caida_tension(10, 13.3, 63, 1, "3F")
    dV_largo, _ = calcular_caida_tension(30, 13.3, 63, 1, "3F")
    assert dV_largo > dV_corto

    dV_un_paralelo, _ = calcular_caida_tension(30, 13.3, 63, 1, "3F")
    dV_dos_paralelos, _ = calcular_caida_tension(30, 13.3, 63, 2, "3F")
    assert dV_dos_paralelos < dV_un_paralelo

    assert capacidad_corregida(65, 2, 30) > capacidad_corregida(65, 1, 30)
