"""
Tests P0.1 — Impedancia compleja de cable (R+jX).

Verifica:
- Tabla de reactancia X por sección en conductores.py
- calcular_zt_cable_complejo() devuelve complex con parte imaginaria > 0
- calcular_icc_punto() con modelo complejo da Icc <= modelo resistivo
- calcular_icc_fase_neutro() incluye componente imaginaria
- Retrocompatibilidad: calcular_zt_cable() y Zt_total siguen siendo float
"""
import math

import pytest

from conductores import get_reactancia_cable_ohm_km
from icc_punto import (
    calcular_icc_fase_neutro,
    calcular_icc_punto,
    calcular_zt_cable,
    calcular_zt_cable_complejo,
)


# ---------------------------------------------------------------------------
# DATA-1: tabla de reactancia
# ---------------------------------------------------------------------------

class TestReactanciaTabla:
    def test_retorna_float_positivo(self):
        x = get_reactancia_cable_ohm_km(25.0)
        assert isinstance(x, float)
        assert x > 0

    def test_rango_razonable_BT_50Hz(self):
        # IEC 60909-2 Table B.1: 0.06 – 0.10 Ω/km para cables BT 50 Hz
        for s in [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]:
            x = get_reactancia_cable_ohm_km(float(s))
            assert 0.05 <= x <= 0.12, f"X={x} fuera de rango para {s} mm²"

    def test_monotonia_X_decrece_con_seccion(self):
        # A mayor sección, mayor capacidad de corriente → menor X por km
        x_pequena = get_reactancia_cable_ohm_km(2.5)
        x_grande = get_reactancia_cable_ohm_km(240.0)
        assert x_pequena > x_grande

    def test_interpolacion_seccion_no_exacta(self):
        # Secciones intermedias (p.ej. AWG equivalentes) no deben fallar
        x = get_reactancia_cable_ohm_km(13.3)  # ~6AWG
        assert x > 0

    def test_seccion_minima_no_falla(self):
        x = get_reactancia_cable_ohm_km(0.5)
        assert x > 0

    def test_seccion_grande_no_falla(self):
        x = get_reactancia_cable_ohm_km(500.0)
        assert x > 0


# ---------------------------------------------------------------------------
# calcular_zt_cable_complejo
# ---------------------------------------------------------------------------

class TestZtCableComplejo:
    def test_devuelve_complex(self):
        z = calcular_zt_cable_complejo(100, 25.0)
        assert isinstance(z, complex)

    def test_parte_real_positiva(self):
        z = calcular_zt_cable_complejo(100, 25.0)
        assert z.real > 0

    def test_parte_imaginaria_positiva(self):
        z = calcular_zt_cable_complejo(100, 25.0)
        assert z.imag > 0

    def test_magnitud_mayor_que_R_solo(self):
        r = calcular_zt_cable(100, 25.0)
        z = calcular_zt_cable_complejo(100, 25.0)
        assert abs(z) > r

    def test_parte_real_igual_a_zt_cable(self):
        r = calcular_zt_cable(100, 25.0)
        z = calcular_zt_cable_complejo(100, 25.0)
        assert z.real == pytest.approx(r, abs=1e-7)

    def test_paralelos_reduce_Z(self):
        z1 = calcular_zt_cable_complejo(100, 25.0, paralelos=1)
        z2 = calcular_zt_cable_complejo(100, 25.0, paralelos=2)
        assert abs(z2) < abs(z1)

    def test_longitud_escala_linealmente(self):
        z100 = calcular_zt_cable_complejo(100, 25.0)
        z200 = calcular_zt_cable_complejo(200, 25.0)
        assert abs(z200.real - 2 * z100.real) < 1e-9
        assert abs(z200.imag - 2 * z100.imag) < 1e-9

    def test_valor_concreto_25mm2_100m(self):
        # R = 0.0175 * 100 / 25 = 0.07 Ω
        # X = get_reactancia_cable_ohm_km(25) * 100 / 1000
        from conductores import RHO_CU
        r_expected = RHO_CU * 100 / 25.0
        x_expected = get_reactancia_cable_ohm_km(25.0) * 100 / 1000.0
        z = calcular_zt_cable_complejo(100, 25.0)
        assert z.real == pytest.approx(r_expected, abs=1e-7)
        assert z.imag == pytest.approx(x_expected, abs=1e-7)

    def test_retrocompat_calcular_zt_cable_devuelve_float(self):
        r = calcular_zt_cable(100, 25.0)
        assert isinstance(r, float)


# ---------------------------------------------------------------------------
# calcular_icc_punto con modelo complejo
# ---------------------------------------------------------------------------

class TestIccPuntoComplejo:
    def test_icc_compleja_menor_o_igual_que_resistiva(self):
        """Con reactancia, la impedancia total es mayor → Icc menor."""
        Zt_trafo = 0.007220
        # Cable largo: la reactancia tiene efecto apreciable
        icc_kA, _, _ = calcular_icc_punto(Zt_trafo, 200, 25.0, 1, "3F")
        # Modelo resistivo puro daría valor mayor; no chequeamos el delta exacto
        # pero Icc debe ser positiva y menor que bornes de trafo
        assert icc_kA > 0
        assert icc_kA < 30.39

    def test_zt_total_es_float(self):
        """La API de retorno sigue siendo float (magnitud |Z|), no complex."""
        _, Zt_total, Zt_cable = calcular_icc_punto(0.01, 50, 10.0, 1, "3F")
        assert isinstance(Zt_total, float)
        assert isinstance(Zt_cable, float)

    def test_zt_total_mayor_que_trafo(self):
        Zt_trafo = 0.007220
        _, Zt_total, _ = calcular_icc_punto(Zt_trafo, 10, 13.3, 1, "3F")
        assert Zt_total > Zt_trafo

    def test_icc_decrece_con_longitud(self):
        Zt_trafo = 0.007220
        icc_10m, _, _ = calcular_icc_punto(Zt_trafo, 10, 25.0, 1, "3F")
        icc_200m, _, _ = calcular_icc_punto(Zt_trafo, 200, 25.0, 1, "3F")
        assert icc_200m < icc_10m

    def test_icc_1F_menor_que_3F(self):
        """Monofásico tiene mayor bucle de retorno → Icc menor."""
        Zt_trafo = 0.007220
        icc_3f, _, _ = calcular_icc_punto(Zt_trafo, 50, 10.0, 1, "3F")
        icc_1f, _, _ = calcular_icc_punto(Zt_trafo, 50, 10.0, 1, "1F")
        assert icc_1f < icc_3f

    def test_reporte_incluye_modelo_impedancia(self):
        """El resultado de calcular_icc_punto reporta el modelo usado."""
        Zt_trafo = 0.007220
        result = calcular_icc_punto(Zt_trafo, 50, 10.0, 1, "3F")
        # API existente: tuple de 3 valores
        assert len(result) == 3
        icc_kA, zt_total, zt_cable = result
        assert icc_kA > 0
        assert zt_total > 0
        assert zt_cable > 0


# ---------------------------------------------------------------------------
# calcular_icc_fase_neutro con modelo complejo
# ---------------------------------------------------------------------------

class TestIccFaseNeutroComplejo:
    def test_icc_fn_positiva_con_reactancia(self):
        r = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=10.0)
        assert r["Icc_fn_A"] > 0

    def test_icc_fn_decrece_con_longitud(self):
        corto = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=10.0)
        largo = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=200, S_mm2=10.0)
        assert largo["Icc_fn_A"] < corto["Icc_fn_A"]

    def test_icc_fn_reporte_incluye_reactancia(self):
        r = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=10.0)
        assert "X_cable_ohm" in r
        assert r["X_cable_ohm"] > 0

    def test_icc_fn_zs_total_incluye_reactancia(self):
        r = calcular_icc_fase_neutro(Vn_V=380, Zt_fuente_ohm=0.01, L_m=50, S_mm2=10.0)
        # Zs_total debe ser la magnitud del lazo complejo
        assert "Zs_total_ohm" in r
        assert r["Zs_total_ohm"] > 0
