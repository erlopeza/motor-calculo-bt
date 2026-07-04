"""Robustez de módulos de cálculo ante entradas degeneradas (aristas de crash)."""
import pytest

import protecciones as P
import icc_punto as I


# ---------------------------------------------------------------------------
# protecciones — In inválido no debe dividir por cero
# ---------------------------------------------------------------------------

class TestProteccionesRobustez:
    def test_verificar_disparo_In_cero_no_crashea(self):
        # In=0 (hoja de protecciones con In en blanco) → indeterminable, no crash
        r = P.verificar_disparo(5000, 0, "C")
        assert r == (None, None, None)

    def test_verificar_disparo_In_negativo_no_crashea(self):
        assert P.verificar_disparo(5000, -10, "C") == (None, None, None)

    def test_verificar_disparo_valido_sigue_ok(self):
        puede, margen, im = P.verificar_disparo(5000, 100, "C")
        assert puede is True and im is not None


# ---------------------------------------------------------------------------
# icc_punto — geometría inválida (S=0, paralelos=0) da error claro, no ZeroDivision
# ---------------------------------------------------------------------------

class TestIccGeometriaRobustez:
    def test_zt_complejo_S_cero_error_claro(self):
        with pytest.raises(ValueError):
            I.calcular_zt_cable_complejo(20, 0, 1)

    def test_zt_complejo_paralelos_cero_error_claro(self):
        with pytest.raises(ValueError):
            I.calcular_zt_cable_complejo(20, 10.0, 0)

    def test_icc_punto_paralelos_cero_error_claro(self):
        with pytest.raises(ValueError):
            I.calcular_icc_punto(0.007, 20, 10.0, 0, "3F")

    def test_zt_complejo_valido_sigue_ok(self):
        z = I.calcular_zt_cable_complejo(20, 10.0, 1)
        assert z.real > 0
