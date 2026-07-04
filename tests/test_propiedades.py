"""Pruebas basadas en propiedades (hypothesis) sobre el motor de cálculo.

Verifican invariantes físicos que deben cumplirse para TODA entrada válida,
no solo casos puntuales — cazan aristas numéricas no anticipadas.
"""
import math

import pytest
from hypothesis import given, settings, strategies as st

import calculos
import icc_punto
import arc_flash
import tcc_curvas
import red_desde_cadena
from flujo_nodal import calcular_flujo_nodal

# Estrategias acotadas al dominio físico válido (sin NaN/inf).
f = lambda lo, hi: st.floats(min_value=lo, max_value=hi, allow_nan=False, allow_infinity=False)
SISTEMAS = st.sampled_from(["1F", "2F", "3F"])
SECCIONES = st.sampled_from([1.5, 2.5, 4.0, 6.0, 10.0, 25.0, 50.0, 95.0, 150.0, 240.0])
PARALELOS = st.integers(min_value=1, max_value=4)

SETT = settings(max_examples=150, deadline=None)


# ---------------------------------------------------------------------------
# Caída de tensión
# ---------------------------------------------------------------------------

class TestCaidaTension:
    @SETT
    @given(L=f(1, 500), S=SECCIONES, I=f(1, 800), n=PARALELOS, sis=SISTEMAS)
    def test_dv_no_negativa(self, L, S, I, n, sis):
        dv_v, dv_pct = calculos.calcular_caida_tension(L, S, I, n, sis)
        assert dv_v >= 0 and dv_pct >= 0

    @SETT
    @given(L=f(1, 200), S=SECCIONES, I=f(1, 500), n=PARALELOS, sis=SISTEMAS)
    def test_dv_crece_con_longitud(self, L, S, I, n, sis):
        # doble longitud → no menos caída (separación clara evita ruido de redondeo)
        dv1 = calculos.calcular_caida_tension(L, S, I, n, sis)[0]
        dv2 = calculos.calcular_caida_tension(2 * L, S, I, n, sis)[0]
        assert dv2 >= dv1

    @SETT
    @given(L=f(1, 200), S=SECCIONES, I=f(1, 500), n=PARALELOS, sis=SISTEMAS)
    def test_dv_decrece_con_seccion(self, L, S, I, n, sis):
        # más paralelos = más sección efectiva → no más caída
        dv1 = calculos.calcular_caida_tension(L, S, I, n, sis)[0]
        dv2 = calculos.calcular_caida_tension(L, S, I, n + 1, sis)[0]
        assert dv2 <= dv1 + 1e-9


# ---------------------------------------------------------------------------
# Icc en punto
# ---------------------------------------------------------------------------

class TestIccPunto:
    @SETT
    @given(Zt=f(0.001, 0.05), L=f(1, 400), S=SECCIONES, n=PARALELOS, sis=SISTEMAS)
    def test_icc_positiva_y_finita(self, Zt, L, S, n, sis):
        Icc, Zt_total, Zt_cable = icc_punto.calcular_icc_punto(Zt, L, S, n, sis)
        assert Icc > 0 and math.isfinite(Icc)
        assert Zt_total >= Zt_cable - 1e-9  # el total incluye el cable

    @SETT
    @given(Zt=f(0.001, 0.05), L=f(1, 200), S=SECCIONES, n=PARALELOS, sis=SISTEMAS)
    def test_icc_decrece_con_longitud(self, Zt, L, S, n, sis):
        # más longitud → más impedancia → no más Icc
        icc1 = icc_punto.calcular_icc_punto(Zt, L, S, n, sis)[0]
        icc2 = icc_punto.calcular_icc_punto(Zt, 2 * L, S, n, sis)[0]
        assert icc2 <= icc1 + 1e-9


# ---------------------------------------------------------------------------
# Arc Flash
# ---------------------------------------------------------------------------

class TestArcFlash:
    @SETT
    @given(Ibf=f(1, 65), V=f(0.2, 1.0), G=f(10, 50))
    def test_ia_positiva_y_finita(self, Ibf, V, G):
        # Invariante robusto del modelo IEEE 1584-2002: Ia > 0 y finita.
        # (Ia < Ibf se cumple dentro del rango validado del modelo — cubierto
        #  con valores realistas en test_arc_flash.py; la fórmula empírica puede
        #  dar Ia >= Ibf a corrientes bajas + V alta, fuera de su rango de ajuste.)
        r = arc_flash.calcular_corriente_arco(Ibf, V, G)
        assert r["Ia_kA"] > 0 and math.isfinite(r["Ia_kA"])

    @SETT
    @given(Ibf=f(2, 40), V=f(0.2, 1.0), G=f(10, 50))
    def test_ia_crece_con_ibf(self, Ibf, V, G):
        # más corriente de falla franca → más corriente de arco (monótona)
        ia1 = arc_flash.calcular_corriente_arco(Ibf, V, G)["Ia_kA"]
        ia2 = arc_flash.calcular_corriente_arco(1.5 * Ibf, V, G)["Ia_kA"]
        assert ia2 >= ia1

    @SETT
    @given(Ia=f(0.5, 40), t=f(0.02, 2.0), D=f(300, 1000), V=f(0.2, 1.0), G=f(10, 50))
    def test_energia_positiva_y_proporcional_al_tiempo(self, Ia, t, D, V, G):
        e1 = arc_flash.calcular_energia_incidente(Ia, t, D, V, G)["E_cal_cm2"]
        e2 = arc_flash.calcular_energia_incidente(Ia, 2 * t, D, V, G)["E_cal_cm2"]
        assert e1 > 0
        # tolerancia abs cubre el ruido de redondeo a 4 decimales en energías diminutas
        assert e2 == pytest.approx(2 * e1, rel=1e-3, abs=1e-3)

    @SETT
    @given(Ia=f(0.5, 40), t=f(0.02, 2.0), V=f(0.2, 1.0), G=f(10, 50))
    def test_frontera_decrece_con_distancia_de_trabajo(self, Ia, t, V, G):
        # a mayor distancia de trabajo, la energía en ese punto es menor
        e_cerca = arc_flash.calcular_energia_incidente(Ia, t, 300.0, V, G)["E_cal_cm2"]
        e_lejos = arc_flash.calcular_energia_incidente(Ia, t, 900.0, V, G)["E_cal_cm2"]
        assert e_lejos <= e_cerca + 1e-9

    @SETT
    @given(Ibf=f(1, 65), V=f(0.2, 1.0), G=f(10, 50), t=f(0.02, 2.0), D=f(300, 1000))
    def test_completo_coherente(self, Ibf, V, G, t, D):
        r = arc_flash.calcular_arc_flash_completo(Ibf, V, G, t_s=t, D_mm=D)
        assert r["E_cal_cm2"] > 0 and math.isfinite(r["E_cal_cm2"])
        assert r["D_afb_mm"] > 0


# ---------------------------------------------------------------------------
# TCC (región térmica IEC 60898)
# ---------------------------------------------------------------------------

class TestTCC:
    @SETT
    @given(In=f(10, 400), mult=f(1.05, 4.0), modelo=st.sampled_from(["B", "C", "D"]))
    def test_tiempo_termico_positivo(self, In, mult, modelo):
        r = tcc_curvas.calcular_tiempo_tcc(mult * In, In, "IEC60898", modelo)
        if r["dispara"] and r["region"] == "termico":
            assert r["t_s"] > 0 and math.isfinite(r["t_s"])

    @SETT
    @given(In=f(10, 400), modelo=st.sampled_from(["B", "C", "D"]))
    def test_tiempo_decrece_con_corriente(self, In, modelo):
        # dentro de la región térmica, más corriente → menos tiempo
        r1 = tcc_curvas.calcular_tiempo_tcc(1.5 * In, In, "IEC60898", modelo)
        r2 = tcc_curvas.calcular_tiempo_tcc(2.5 * In, In, "IEC60898", modelo)
        if (r1["region"] == "termico" and r2["region"] == "termico"):
            assert r2["t_s"] <= r1["t_s"]


# ---------------------------------------------------------------------------
# red_desde_cadena — conservación de carga sobre cadenas radiales aleatorias
# ---------------------------------------------------------------------------

def _cadena_radial(iccs):
    """Cadena lineal G0→G1→…: cada nodo cuelga del anterior, Icc decreciente."""
    cadena = []
    prev = ""
    for i, icc in enumerate(iccs):
        nombre = f"N{i}"
        cadena.append({"nombre": nombre, "upstream": prev, "nivel": i,
                       "In_A": 100, "curva": "C", "Icc_kA": icc})
        prev = nombre
    return cadena


class TestRedDesdeCadena:
    @SETT
    @given(
        iccs=st.lists(f(1.0, 40.0), min_size=1, max_size=6),
        p_total=f(10, 500),
    )
    def test_carga_total_conservada(self, iccs, p_total):
        # Icc estrictamente decreciente aguas abajo (físico)
        iccs = sorted(set(round(x, 3) for x in iccs), reverse=True)
        if len(iccs) < 1:
            return
        cadena = _cadena_radial(iccs)
        circuitos = [{"nombre": "L", "sistema": "3F", "I_diseno": p_total, "cos_phi": 0.9}]
        red = red_desde_cadena.construir_red(cadena, trafo_z_ohm=0.005, circuitos=circuitos)
        p_asignada = -sum(b.P_kW for b in red.buses if b.tipo == "PQ")
        p_esperada = math.sqrt(3) * 380.0 * p_total * 0.9 / 1000.0
        assert p_asignada == pytest.approx(p_esperada, rel=1e-6)

    @SETT
    @given(iccs=st.lists(f(1.0, 40.0), min_size=1, max_size=6))
    def test_ramas_impedancia_no_negativa(self, iccs):
        iccs = sorted(set(round(x, 3) for x in iccs), reverse=True)
        cadena = _cadena_radial(iccs)
        circuitos = [{"nombre": "L", "sistema": "3F", "I_diseno": 100, "cos_phi": 0.9}]
        red = red_desde_cadena.construir_red(cadena, trafo_z_ohm=0.005, circuitos=circuitos)
        for r in red.ramas:
            assert r.R_ohm > 0 and r.X_ohm >= 0
