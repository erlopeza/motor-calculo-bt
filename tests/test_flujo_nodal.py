"""
Tests F3-P2.1 — Flujo de carga nodal (Newton-Raphson).

Verifica:
- Modelo de datos: Bus, Rama, Red
- Y-bus: construcción y propiedades (diagonal dominante, simétrica)
- Newton-Raphson: convergencia, conservación de potencia
- Propiedades físicas: caída de tensión bajo carga, monotonía
- Pérdidas por rama: positivas, consistentes con balance de potencia
- Reporte de texto generado sin error
"""
import math
import pytest
import numpy as np

from flujo_nodal import (
    Bus,
    Rama,
    Red,
    calcular_flujo_nodal,
    calcular_perdidas_rama,
    reporte_flujo_nodal,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _red_2bus(P_carga_kW: float = 50.0, Q_carga_kVAR: float = 25.0,
              R_ohm: float = 0.05, X_ohm: float = 0.02) -> Red:
    """Red mínima: slack + 1 carga."""
    return Red(
        buses=[
            Bus(id="B0", tipo="slack", P_kW=0.0, Q_kVAR=0.0),
            Bus(id="B1", tipo="PQ", P_kW=-P_carga_kW, Q_kVAR=-Q_carga_kVAR),
        ],
        ramas=[Rama(from_bus="B0", to_bus="B1", R_ohm=R_ohm, X_ohm=X_ohm)],
        V_base_kV=0.38,
        S_base_kVA=1000.0,
    )


def _red_3bus() -> Red:
    """Red lineal: B0 (slack) → B1 → B2."""
    return Red(
        buses=[
            Bus(id="B0", tipo="slack"),
            Bus(id="B1", tipo="PQ", P_kW=-40.0, Q_kVAR=-20.0),
            Bus(id="B2", tipo="PQ", P_kW=-60.0, Q_kVAR=-30.0),
        ],
        ramas=[
            Rama(from_bus="B0", to_bus="B1", R_ohm=0.05, X_ohm=0.02),
            Rama(from_bus="B1", to_bus="B2", R_ohm=0.08, X_ohm=0.03),
        ],
        V_base_kV=0.38,
        S_base_kVA=1000.0,
    )


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------

class TestModeloDatos:
    def test_bus_defaults(self):
        b = Bus(id="B0", tipo="slack")
        assert b.V_pu == pytest.approx(1.0)
        assert b.P_kW == pytest.approx(0.0)

    def test_rama_almacena_impedancia(self):
        r = Rama(from_bus="A", to_bus="B", R_ohm=0.1, X_ohm=0.05)
        assert r.R_ohm == pytest.approx(0.1)
        assert r.X_ohm == pytest.approx(0.05)

    def test_red_indexa_buses(self):
        red = _red_2bus()
        assert red.indice_bus("B0") == 0
        assert red.indice_bus("B1") == 1

    def test_red_calcula_Z_base(self):
        red = _red_2bus()
        # Z_base = V_base_kV² / S_base_MVA = 0.38² / 1.0 = 0.1444 Ω
        assert red.Z_base_ohm == pytest.approx(0.38**2 / 1.0, rel=1e-4)

    def test_red_requiere_exactamente_un_slack(self):
        with pytest.raises((ValueError, AssertionError)):
            Red(
                buses=[
                    Bus(id="B0", tipo="PQ"),
                    Bus(id="B1", tipo="PQ"),
                ],
                ramas=[Rama("B0", "B1", 0.05, 0.02)],
            )

    def test_rama_con_bus_inexistente_lanza_valueerror(self):
        """#6: una rama que referencia un bus inexistente debe fallar claro."""
        with pytest.raises(ValueError):
            Red(
                buses=[
                    Bus(id="B0", tipo="slack"),
                    Bus(id="B1", tipo="PQ", P_kW=-10.0),
                ],
                ramas=[Rama("B0", "FANTASMA", 0.05, 0.02)],
            )

    def test_pv_no_soportado_lanza_error(self):
        """#1: PV no implementado — debe rechazarse explícitamente."""
        with pytest.raises((ValueError, NotImplementedError)):
            Red(
                buses=[
                    Bus(id="B0", tipo="slack"),
                    Bus(id="B1", tipo="PV", P_kW=20.0),
                ],
                ramas=[Rama("B0", "B1", 0.05, 0.02)],
            )


# ---------------------------------------------------------------------------
# Y-bus
# ---------------------------------------------------------------------------

class TestYbus:
    def test_ybus_simetrica(self):
        red = _red_2bus()
        Y = red.construir_ybus()
        np.testing.assert_allclose(Y, Y.T, atol=1e-12)

    def test_ybus_suma_filas_nula(self):
        """Para una red sin derivaciones a tierra: sum de cada fila ≈ 0."""
        red = _red_2bus()
        Y = red.construir_ybus()
        sumas = Y.sum(axis=1)
        np.testing.assert_allclose(np.abs(sumas), 0.0, atol=1e-10)

    def test_ybus_diagonal_dominante_en_magnitud(self):
        red = _red_2bus()
        Y = red.construir_ybus()
        for i in range(len(red.buses)):
            diag = abs(Y[i, i])
            suma_fuera = sum(abs(Y[i, j]) for j in range(len(red.buses)) if j != i)
            assert diag >= suma_fuera - 1e-12

    def test_ybus_3bus_tiene_3x3(self):
        red = _red_3bus()
        Y = red.construir_ybus()
        assert Y.shape == (3, 3)


# ---------------------------------------------------------------------------
# Newton-Raphson: convergencia
# ---------------------------------------------------------------------------

class TestConvergencia:
    def test_converge_2bus(self):
        res = calcular_flujo_nodal(_red_2bus())
        assert res["convergido"] is True

    def test_converge_3bus(self):
        res = calcular_flujo_nodal(_red_3bus())
        assert res["convergido"] is True

    def test_iteraciones_finitas(self):
        res = calcular_flujo_nodal(_red_2bus())
        assert isinstance(res["iteraciones"], int)
        assert 1 <= res["iteraciones"] <= 50

    def test_resultado_tiene_todos_los_buses(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        for bus in red.buses:
            assert bus.id in res["buses"]

    def test_bus_resultado_tiene_campos(self):
        res = calcular_flujo_nodal(_red_2bus())
        for campo in ("V_pu", "delta_deg", "V_kV", "P_kW", "Q_kVAR"):
            assert campo in res["buses"]["B1"]


# ---------------------------------------------------------------------------
# Propiedades físicas
# ---------------------------------------------------------------------------

class TestFisica:
    def test_slack_mantiene_tension(self):
        res = calcular_flujo_nodal(_red_2bus())
        assert res["buses"]["B0"]["V_pu"] == pytest.approx(1.0, abs=1e-6)

    def test_slack_angulo_cero(self):
        res = calcular_flujo_nodal(_red_2bus())
        assert res["buses"]["B0"]["delta_deg"] == pytest.approx(0.0, abs=1e-6)

    def test_carga_tiene_tension_menor_que_slack(self):
        res = calcular_flujo_nodal(_red_2bus())
        assert res["buses"]["B1"]["V_pu"] < res["buses"]["B0"]["V_pu"]

    def test_carga_mayor_mas_caida_tension(self):
        r1 = calcular_flujo_nodal(_red_2bus(P_carga_kW=50.0))
        r2 = calcular_flujo_nodal(_red_2bus(P_carga_kW=150.0))
        assert r2["buses"]["B1"]["V_pu"] < r1["buses"]["B1"]["V_pu"]

    def test_cable_mas_largo_mas_caida(self):
        r1 = calcular_flujo_nodal(_red_2bus(R_ohm=0.03, X_ohm=0.01))
        r2 = calcular_flujo_nodal(_red_2bus(R_ohm=0.15, X_ohm=0.06))
        assert r2["buses"]["B1"]["V_pu"] < r1["buses"]["B1"]["V_pu"]

    def test_tension_en_kV_consistente_con_pu(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        V_pu = res["buses"]["B1"]["V_pu"]
        V_kV = res["buses"]["B1"]["V_kV"]
        assert V_kV == pytest.approx(V_pu * red.V_base_kV, rel=1e-4)

    def test_angulo_carga_negativo_rama_inductiva(self):
        """Rama X-dominante (X >> R) con carga inductiva → ángulo negativo.

        En redes de transmisión (X >> R) el ángulo del bus de carga es
        negativo respecto al slack. En BT (R > X) puede ser positivo:
        Im(ΔV) ∝ P·X − Q·R cambia de signo según la relación X/R.
        """
        res = calcular_flujo_nodal(_red_2bus(R_ohm=0.01, X_ohm=0.15))
        assert res["buses"]["B1"]["delta_deg"] < 0.0

    def test_angulo_carga_no_nulo(self):
        """Bajo carga el ángulo del bus PQ es distinto de cero (hay flujo)."""
        res = calcular_flujo_nodal(_red_2bus())
        assert abs(res["buses"]["B1"]["delta_deg"]) > 1e-6

    def test_3bus_tension_decrece_en_cascada(self):
        """V_B2 ≤ V_B1 ≤ V_B0 en red radial con cargas en todos los buses."""
        res = calcular_flujo_nodal(_red_3bus())
        v0 = res["buses"]["B0"]["V_pu"]
        v1 = res["buses"]["B1"]["V_pu"]
        v2 = res["buses"]["B2"]["V_pu"]
        assert v0 >= v1 >= v2


# ---------------------------------------------------------------------------
# Balance de potencia
# ---------------------------------------------------------------------------

class TestBalancePotencia:
    def test_perdidas_positivas(self):
        """Las pérdidas totales deben ser positivas (red pasiva)."""
        res = calcular_flujo_nodal(_red_2bus())
        assert res["perdidas_totales_kW"] > 0

    def test_balance_P_slack_igual_carga_mas_perdidas(self):
        """P_slack ≈ P_carga + P_perdidas (conservación de energía)."""
        P_carga = 50.0
        res = calcular_flujo_nodal(_red_2bus(P_carga_kW=P_carga))
        P_slack = res["buses"]["B0"]["P_kW"]
        perdidas = res["perdidas_totales_kW"]
        # P_slack (generada) = P_carga + pérdidas
        assert P_slack == pytest.approx(P_carga + perdidas, rel=0.01)

    def test_suma_inyecciones_igual_perdidas(self):
        """Σ P_inyectada = P_perdidas (suma de inyecciones de carga negativas)."""
        res = calcular_flujo_nodal(_red_2bus(P_carga_kW=50.0))
        P_total = sum(b["P_kW"] for b in res["buses"].values())
        # P_total = P_slack - P_carga (ambas positivas aquí)
        # El balance: P_slack + P_carga_inyectada = pérdidas
        # P_carga_inyectada es negativo → P_total = pérdidas
        assert abs(P_total) == pytest.approx(res["perdidas_totales_kW"], rel=0.01)


# ---------------------------------------------------------------------------
# Pérdidas por rama
# ---------------------------------------------------------------------------

class TestPerdidasRama:
    def test_perdidas_rama_positivas(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        perdidas = calcular_perdidas_rama(red, res)
        for rama_id, p in perdidas.items():
            assert p["perdidas_kW"] >= 0

    def test_perdidas_rama_suman_totales(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        perdidas = calcular_perdidas_rama(red, res)
        suma = sum(p["perdidas_kW"] for p in perdidas.values())
        assert suma == pytest.approx(res["perdidas_totales_kW"], rel=1e-4)

    def test_perdidas_rama_tiene_campos(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        perdidas = calcular_perdidas_rama(red, res)
        for rama_id, p in perdidas.items():
            for campo in ("perdidas_kW", "I_A", "P_entrada_kW", "P_salida_kW"):
                assert campo in p, f"Falta campo '{campo}' en rama {rama_id}"

    def test_corriente_rama_positiva(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        perdidas = calcular_perdidas_rama(red, res)
        for p in perdidas.values():
            assert p["I_A"] >= 0


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

class TestReporte:
    def test_reporte_genera_texto(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        lineas = reporte_flujo_nodal(res)
        assert isinstance(lineas, list)
        assert len(lineas) > 0
        texto = "\n".join(lineas)
        assert "B0" in texto
        assert "B1" in texto

    def test_reporte_indica_convergencia(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        lineas = reporte_flujo_nodal(res)
        texto = "\n".join(lineas)
        assert "CONVERGI" in texto.upper() or "OK" in texto.upper()

    def test_reporte_incluye_perdidas(self):
        red = _red_2bus()
        res = calcular_flujo_nodal(red)
        lineas = reporte_flujo_nodal(res)
        texto = "\n".join(lineas)
        assert "pérdida" in texto.lower() or "perdida" in texto.lower()
