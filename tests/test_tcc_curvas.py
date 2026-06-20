"""
Tests P1.2 — Librería de curvas TCC (DATA-3).

Verifica:
- Catálogo JSON carga sin error
- IEC 60898 curvas B/C/D — fórmula t = k/(I/In)^2
- IEC 60255 IDMT: NI / VI / EI / LTI — fórmula t = TMS × β/((I/Is)^α − 1)
- Lookup por tipo, modelo y fabricante
- Propiedades físicas: t > 0, monotonía (mayor corriente → menor tiempo)
"""
import math
import pytest
from tcc_curvas import (
    buscar_curva,
    calcular_tiempo_tcc,
    cargar_catalogo,
    listar_disponibles,
)


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------

class TestCatalogoCarga:
    def test_catalogo_carga_sin_error(self):
        cat = cargar_catalogo()
        assert isinstance(cat, list)
        assert len(cat) >= 7  # B, C, D, NI, VI, EI, LTI

    def test_catalogo_tiene_version(self):
        from tcc_curvas import CATALOGO_VERSION
        assert isinstance(CATALOGO_VERSION, str)
        assert len(CATALOGO_VERSION) > 0

    def test_cada_entrada_tiene_campos_obligatorios(self):
        for entrada in cargar_catalogo():
            for campo in ("id", "tipo", "modelo", "formula", "parametros"):
                assert campo in entrada, f"Falta campo '{campo}' en {entrada.get('id', '?')}"

    def test_listar_disponibles_incluye_iec60898(self):
        disp = listar_disponibles()
        assert "IEC60898" in disp

    def test_listar_disponibles_incluye_iec60255(self):
        disp = listar_disponibles()
        assert "IEC60255" in disp

    def test_listar_disponibles_modelos_B_C_D(self):
        disp = listar_disponibles()
        modelos_bt = {m for m in disp.get("IEC60898", [])}
        assert {"B", "C", "D"}.issubset(modelos_bt)

    def test_listar_disponibles_idmt_NI_VI_EI(self):
        disp = listar_disponibles()
        modelos_idmt = {m for m in disp.get("IEC60255", [])}
        assert {"NI", "VI", "EI"}.issubset(modelos_idmt)


# ---------------------------------------------------------------------------
# Lookup: buscar_curva
# ---------------------------------------------------------------------------

class TestBuscarCurva:
    def test_busca_curva_B(self):
        c = buscar_curva(tipo="IEC60898", modelo="B")
        assert c is not None
        assert c["modelo"] == "B"

    def test_busca_curva_NI(self):
        c = buscar_curva(tipo="IEC60255", modelo="NI")
        assert c is not None
        assert c["modelo"] == "NI"

    def test_busca_curva_no_existe_retorna_none(self):
        c = buscar_curva(tipo="FICTICIO", modelo="X")
        assert c is None

    def test_busca_insensible_a_mayusculas(self):
        c = buscar_curva(tipo="iec60898", modelo="c")
        assert c is not None
        assert c["modelo"] == "C"


# ---------------------------------------------------------------------------
# IEC 60898: curvas B / C / D
# ---------------------------------------------------------------------------

class TestTccIEC60898:
    @pytest.mark.parametrize("modelo,k", [("B", 45), ("C", 80), ("D", 180)])
    def test_region_termica_formula_k_cuadrado(self, modelo, k):
        """t = k / (I/In)² en región térmica."""
        In_A = 100.0
        I_A = 1.5 * In_A  # en región térmica (por encima de In, por debajo de Imag)
        resultado = calcular_tiempo_tcc(I_A, In_A, tipo="IEC60898", modelo=modelo)
        esperado = k / (I_A / In_A) ** 2
        assert resultado["t_s"] == pytest.approx(esperado, rel=1e-4)
        assert resultado["region"] == "termico"

    def test_curva_B_region_instantanea(self):
        """I ≥ 5×In → instantáneo."""
        In_A = 100.0
        resultado = calcular_tiempo_tcc(5.1 * In_A, In_A, tipo="IEC60898", modelo="B")
        assert resultado["region"] == "instantaneo"
        assert resultado["t_s"] == pytest.approx(0.02, abs=1e-6)

    def test_curva_C_region_instantanea(self):
        In_A = 63.0
        resultado = calcular_tiempo_tcc(10.1 * In_A, In_A, tipo="IEC60898", modelo="C")
        assert resultado["region"] == "instantaneo"

    def test_curva_D_region_instantanea(self):
        In_A = 40.0
        resultado = calcular_tiempo_tcc(20.1 * In_A, In_A, tipo="IEC60898", modelo="D")
        assert resultado["region"] == "instantaneo"

    def test_no_dispara_bajo_In(self):
        In_A = 63.0
        resultado = calcular_tiempo_tcc(0.9 * In_A, In_A, tipo="IEC60898", modelo="C")
        assert resultado["region"] == "no_dispara"
        assert resultado["dispara"] is False

    def test_monotonia_mayor_corriente_menor_tiempo(self):
        In_A = 100.0
        t1 = calcular_tiempo_tcc(1.5 * In_A, In_A, tipo="IEC60898", modelo="C")["t_s"]
        t2 = calcular_tiempo_tcc(3.0 * In_A, In_A, tipo="IEC60898", modelo="C")["t_s"]
        assert t1 > t2, "Mayor corriente debe producir menor tiempo de disparo"


# ---------------------------------------------------------------------------
# IEC 60255: curvas IDMT (NI / VI / EI / LTI)
# ---------------------------------------------------------------------------

class TestTccIEC60255:
    def test_NI_valor_tipico(self):
        """NI con I/Is=10, TMS=1: t = 0.14/((10)^0.02 - 1) ≈ 3.0s."""
        Is_A = 100.0
        I_A = 10 * Is_A
        res = calcular_tiempo_tcc(I_A, Is_A, tipo="IEC60255", modelo="NI", tms=1.0)
        esperado = 1.0 * 0.14 / (10**0.02 - 1)
        assert res["t_s"] == pytest.approx(esperado, rel=1e-4)
        assert res["region"] == "idmt"

    def test_VI_valor_tipico(self):
        """VI con I/Is=10, TMS=1: t = 13.5/((10)^1 - 1) = 1.5s."""
        Is_A = 100.0
        I_A = 10 * Is_A
        res = calcular_tiempo_tcc(I_A, Is_A, tipo="IEC60255", modelo="VI", tms=1.0)
        esperado = 1.0 * 13.5 / (10**1.0 - 1)
        assert res["t_s"] == pytest.approx(esperado, rel=1e-4)

    def test_EI_valor_tipico(self):
        """EI con I/Is=10, TMS=1: t = 80/((10)^2 - 1) ≈ 0.808s."""
        Is_A = 100.0
        I_A = 10 * Is_A
        res = calcular_tiempo_tcc(I_A, Is_A, tipo="IEC60255", modelo="EI", tms=1.0)
        esperado = 1.0 * 80.0 / (10**2.0 - 1)
        assert res["t_s"] == pytest.approx(esperado, rel=1e-4)

    def test_LTI_valor_tipico(self):
        """LTI con I/Is=5, TMS=1: t = 120/((5)^1 - 1) = 30s."""
        Is_A = 100.0
        I_A = 5 * Is_A
        res = calcular_tiempo_tcc(I_A, Is_A, tipo="IEC60255", modelo="LTI", tms=1.0)
        esperado = 1.0 * 120.0 / (5**1.0 - 1)
        assert res["t_s"] == pytest.approx(esperado, rel=1e-4)

    def test_tms_escala_linealmente(self):
        """TMS × 2 → t × 2."""
        Is_A = 100.0
        I_A = 5 * Is_A
        t1 = calcular_tiempo_tcc(I_A, Is_A, tipo="IEC60255", modelo="NI", tms=1.0)["t_s"]
        t2 = calcular_tiempo_tcc(I_A, Is_A, tipo="IEC60255", modelo="NI", tms=2.0)["t_s"]
        assert t2 == pytest.approx(2 * t1, rel=1e-6)

    def test_no_dispara_bajo_Is(self):
        """I ≤ Is → la curva IDMT no aplica (sin disparo)."""
        Is_A = 100.0
        res = calcular_tiempo_tcc(0.9 * Is_A, Is_A, tipo="IEC60255", modelo="NI", tms=1.0)
        assert res["dispara"] is False

    def test_idmt_monotona(self):
        Is_A = 100.0
        t1 = calcular_tiempo_tcc(2 * Is_A, Is_A, tipo="IEC60255", modelo="VI", tms=1.0)["t_s"]
        t2 = calcular_tiempo_tcc(10 * Is_A, Is_A, tipo="IEC60255", modelo="VI", tms=1.0)["t_s"]
        assert t1 > t2

    def test_tiempo_siempre_positivo(self):
        Is_A = 100.0
        for modelo in ("NI", "VI", "EI", "LTI"):
            for mult in (1.5, 5, 20):
                res = calcular_tiempo_tcc(
                    mult * Is_A, Is_A, tipo="IEC60255", modelo=modelo, tms=0.5
                )
                if res["dispara"]:
                    assert res["t_s"] > 0, f"Tiempo negativo en {modelo} mult={mult}"

    def test_retorna_dict_completo(self):
        Is_A = 100.0
        res = calcular_tiempo_tcc(5 * Is_A, Is_A, tipo="IEC60255", modelo="NI", tms=1.0)
        for campo in ("t_s", "region", "dispara", "nota"):
            assert campo in res

    def test_curva_desconocida_retorna_none_t(self):
        res = calcular_tiempo_tcc(500, 100, tipo="FICTICIO", modelo="X")
        assert res["t_s"] is None
        assert res["dispara"] is False
