"""
Tests P0.2 — Aporte de motores al cortocircuito.

Verifica:
- Tabla X''d subtransitoria por kW (DATA-2, IEC 60909-4:2021)
- calcular_aporte_icc_motor(): corriente subtransitoria por motor
- calcular_icc_con_aporte_motores(): Icc total red + motores
- Reglas físicas: aporte positivo, Icc con motores > sin motores
"""
import math

import pytest

from motores import calcular_aporte_icc_motor, get_xd_subtransitorio
from icc_punto import calcular_icc_con_aporte_motores, calcular_icc_punto


# ---------------------------------------------------------------------------
# DATA-2: tabla de reactancia subtransitoria
# ---------------------------------------------------------------------------

class TestXdSubtransitorio:
    def test_motor_pequeno_xd_mayor(self):
        # Motor pequeño tiene X''d mayor que motor grande (IEC 60909-4 Tabla 1)
        xd_pequeno = get_xd_subtransitorio(5.0)
        xd_grande = get_xd_subtransitorio(200.0)
        assert xd_pequeno > xd_grande

    def test_rango_fisico_valido(self):
        for p in [2.2, 7.5, 15, 37, 90, 132, 315, 500]:
            xd = get_xd_subtransitorio(float(p))
            assert 0.10 <= xd <= 0.30, f"X''d={xd} fuera de rango físico para {p} kW"

    def test_retorna_float(self):
        assert isinstance(get_xd_subtransitorio(30.0), float)

    def test_valor_tipico_motor_mediano(self):
        # IEC 60909-4 Tabla 1: 11-90 kW → X''d ≈ 0.18
        xd = get_xd_subtransitorio(37.0)
        assert 0.16 <= xd <= 0.20


# ---------------------------------------------------------------------------
# calcular_aporte_icc_motor
# ---------------------------------------------------------------------------

class TestAporteIccMotor:
    def test_aporte_positivo(self):
        aporte = calcular_aporte_icc_motor(
            P_kW=37, Vn_V=380, cos_phi=0.85, rendimiento=0.93
        )
        assert aporte["I_aporte_A"] > 0

    def test_aporte_aprox_factor_de_In(self):
        """I''_motor ≈ In / X''d — para 37 kW ≈ 5-6x In."""
        aporte = calcular_aporte_icc_motor(
            P_kW=37, Vn_V=380, cos_phi=0.85, rendimiento=0.93
        )
        In = aporte["I_nominal_A"]
        xd = aporte["Xd_subtransitorio"]
        expected = In / xd
        assert aporte["I_aporte_A"] == pytest.approx(expected, rel=1e-4)

    def test_aporte_mayor_que_In(self):
        """La corriente de aporte es siempre mayor que la nominal."""
        aporte = calcular_aporte_icc_motor(
            P_kW=37, Vn_V=380, cos_phi=0.85, rendimiento=0.93
        )
        assert aporte["I_aporte_A"] > aporte["I_nominal_A"]

    def test_motor_mas_grande_mas_aporte(self):
        """Motor más potente aporta más corriente."""
        aporte_10 = calcular_aporte_icc_motor(10, 380)
        aporte_75 = calcular_aporte_icc_motor(75, 380)
        assert aporte_75["I_aporte_A"] > aporte_10["I_aporte_A"]

    def test_dict_completo(self):
        r = calcular_aporte_icc_motor(37, 380)
        for clave in ["I_nominal_A", "I_aporte_A", "Xd_subtransitorio", "P_kW", "Vn_V"]:
            assert clave in r

    def test_motor_1F(self):
        aporte = calcular_aporte_icc_motor(2.2, 220, sistema="1F")
        assert aporte["I_aporte_A"] > 0

    def test_aporte_kA(self):
        r = calcular_aporte_icc_motor(37, 380)
        assert r["I_aporte_kA"] == pytest.approx(r["I_aporte_A"] / 1000, abs=1e-6)


# ---------------------------------------------------------------------------
# calcular_icc_con_aporte_motores
# ---------------------------------------------------------------------------

class TestIccConAporteMotores:
    def test_icc_con_motores_mayor_que_sin_motores(self):
        Zt_trafo = 0.007220
        icc_red, _, _ = calcular_icc_punto(Zt_trafo, 20, 10.0, 1, "3F")
        icc_total, _ = calcular_icc_con_aporte_motores(
            Icc_red_kA=icc_red,
            aportes_motores_A=[200.0, 150.0],
        )
        assert icc_total > icc_red

    def test_sin_motores_igual_a_red(self):
        icc_red = 15.5
        icc_total, desglose = calcular_icc_con_aporte_motores(
            Icc_red_kA=icc_red,
            aportes_motores_A=[],
        )
        assert icc_total == pytest.approx(icc_red, abs=1e-6)

    def test_aporte_escalar_suma_correcta(self):
        """Icc_total = Icc_red + sum(aportes) / 1000."""
        icc_red = 10.0  # kA
        aportes = [300.0, 400.0]  # A
        icc_total, desglose = calcular_icc_con_aporte_motores(icc_red, aportes)
        expected = icc_red + sum(aportes) / 1000.0
        assert icc_total == pytest.approx(expected, abs=1e-6)

    def test_desglose_contiene_campos(self):
        _, desglose = calcular_icc_con_aporte_motores(10.0, [200.0])
        assert "Icc_red_kA" in desglose
        assert "Icc_motores_kA" in desglose
        assert "Icc_total_kA" in desglose
        assert "n_motores" in desglose

    def test_desglose_n_motores(self):
        _, desglose = calcular_icc_con_aporte_motores(10.0, [200.0, 300.0, 400.0])
        assert desglose["n_motores"] == 3

    def test_aporte_negativo_ignorado(self):
        """Aportes negativos se filtran (no pueden reducir Icc)."""
        icc_total, _ = calcular_icc_con_aporte_motores(10.0, [-100.0])
        assert icc_total == pytest.approx(10.0, abs=1e-6)

    def test_icc_total_positiva(self):
        icc_total, _ = calcular_icc_con_aporte_motores(10.0, [500.0, 300.0])
        assert icc_total > 0


# ---------------------------------------------------------------------------
# Integración: escenario realista
# ---------------------------------------------------------------------------

class TestIntegracionMotoresIcc:
    def test_escenario_cuadro_con_2_motores(self):
        """Tablero con 2 motores BT: Icc resultante debe ser mayor que Icc red."""
        from motores import calcular_aporte_icc_motor
        Zt_trafo = 0.007220  # 1000 kVA, 380V, Ucc=5%

        # Red
        icc_red, _, _ = calcular_icc_punto(Zt_trafo, 30, 25.0, 1, "3F")

        # Dos motores: 30 kW y 11 kW
        m1 = calcular_aporte_icc_motor(30, 380)
        m2 = calcular_aporte_icc_motor(11, 380)

        icc_total, desglose = calcular_icc_con_aporte_motores(
            Icc_red_kA=icc_red,
            aportes_motores_A=[m1["I_aporte_A"], m2["I_aporte_A"]],
        )

        assert icc_total > icc_red
        assert desglose["n_motores"] == 2
        assert desglose["Icc_total_kA"] == pytest.approx(icc_total, abs=1e-6)
