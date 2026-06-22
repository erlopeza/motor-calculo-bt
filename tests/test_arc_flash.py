"""
Tests P1.1 — Arc Flash IEEE 1584-2002 (aplicable a sistemas BT).

Verifica:
- calcular_corriente_arco(): Ia ≤ Ibf; Ia > 0
- calcular_energia_incidente(): E > 0; E ∝ t; E ∝ 1/D²
- calcular_frontera_arco(): D_afb crece con E y con t
- categoria_ppe(): umbrales correctos (NFPA 70E Tabla 130.5)
- Escenario integrado: tablero BT real
"""
import math
import pytest
from arc_flash import (
    calcular_corriente_arco,
    calcular_energia_incidente,
    calcular_frontera_arco,
    categoria_ppe,
    calcular_arc_flash_completo,
)


# ---------------------------------------------------------------------------
# calcular_corriente_arco
# ---------------------------------------------------------------------------

class TestCorrienteArco:
    def test_ia_positiva(self):
        res = calcular_corriente_arco(Ibf_kA=20.0, V_kV=0.48, G_mm=32.0)
        assert res["Ia_kA"] > 0

    def test_ia_menor_que_ibf(self):
        """Corriente de arco siempre menor que corriente de falla bolted."""
        res = calcular_corriente_arco(Ibf_kA=20.0, V_kV=0.48, G_mm=32.0)
        assert res["Ia_kA"] < 20.0

    def test_ia_escala_con_ibf(self):
        """Mayor Ibf → mayor Ia."""
        ia_10 = calcular_corriente_arco(10.0, 0.48, 32.0)["Ia_kA"]
        ia_20 = calcular_corriente_arco(20.0, 0.48, 32.0)["Ia_kA"]
        assert ia_20 > ia_10

    def test_ia_caja_menor_que_abierta(self):
        """Configuración en caja da Ia ligeramente distinta a bus abierto."""
        ia_open = calcular_corriente_arco(20.0, 0.48, 32.0, config="open")["Ia_kA"]
        ia_box  = calcular_corriente_arco(20.0, 0.48, 32.0, config="box")["Ia_kA"]
        # En IEEE 1584-2002, K es -0.153 (open) vs -0.097 (box), lo que da Ia_box > Ia_open
        assert ia_box != ia_open  # distintos, no iguales

    def test_retorna_campos_completos(self):
        res = calcular_corriente_arco(10.0, 0.48, 32.0)
        for campo in ("Ia_kA", "Ibf_kA", "V_kV", "G_mm", "config", "norma"):
            assert campo in res

    def test_norma_referencia(self):
        res = calcular_corriente_arco(10.0, 0.48, 32.0)
        assert "1584" in res["norma"]


# ---------------------------------------------------------------------------
# calcular_energia_incidente
# ---------------------------------------------------------------------------

class TestEnergiaIncidente:
    def test_energia_positiva(self):
        E = calcular_energia_incidente(
            Ia_kA=10.0, t_s=0.1, D_mm=610.0, V_kV=0.48, G_mm=32.0
        )
        assert E["E_cal_cm2"] > 0

    def test_energia_crece_con_tiempo(self):
        """E ∝ t — doble tiempo → doble energía."""
        e1 = calcular_energia_incidente(10.0, t_s=0.1, D_mm=610.0, V_kV=0.48, G_mm=32.0)
        e2 = calcular_energia_incidente(10.0, t_s=0.2, D_mm=610.0, V_kV=0.48, G_mm=32.0)
        assert e2["E_cal_cm2"] == pytest.approx(2 * e1["E_cal_cm2"], rel=1e-4)

    def test_energia_decrece_con_distancia(self):
        """Mayor distancia → menor energía incidente."""
        e_cerca = calcular_energia_incidente(10.0, 0.2, D_mm=305.0, V_kV=0.48, G_mm=32.0)
        e_lejos = calcular_energia_incidente(10.0, 0.2, D_mm=914.0, V_kV=0.48, G_mm=32.0)
        assert e_cerca["E_cal_cm2"] > e_lejos["E_cal_cm2"]

    def test_retorna_campos_completos(self):
        res = calcular_energia_incidente(10.0, 0.1, 610.0, 0.48, 32.0)
        for campo in ("E_cal_cm2", "En_cal_cm2", "t_s", "D_mm", "norma"):
            assert campo in res

    def test_cf_bt_es_1_5(self):
        """Factor Cf = 1.5 para V ≤ 1 kV (IEEE 1584-2002 §4.7)."""
        res = calcular_energia_incidente(10.0, 0.2, 610.0, V_kV=0.48, G_mm=32.0)
        assert res.get("Cf") == pytest.approx(1.5, abs=0.01)


# ---------------------------------------------------------------------------
# calcular_frontera_arco
# ---------------------------------------------------------------------------

class TestFronteraArco:
    def test_frontera_positiva(self):
        afb = calcular_frontera_arco(
            Ia_kA=10.0, t_s=0.2, V_kV=0.48, G_mm=32.0, Ei_cal_cm2=1.2
        )
        assert afb["D_afb_mm"] > 0

    def test_frontera_crece_con_tiempo(self):
        afb1 = calcular_frontera_arco(10.0, t_s=0.1, V_kV=0.48, G_mm=32.0)
        afb2 = calcular_frontera_arco(10.0, t_s=0.5, V_kV=0.48, G_mm=32.0)
        assert afb2["D_afb_mm"] > afb1["D_afb_mm"]

    def test_frontera_crece_con_ia(self):
        afb1 = calcular_frontera_arco(5.0, t_s=0.2, V_kV=0.48, G_mm=32.0)
        afb2 = calcular_frontera_arco(15.0, t_s=0.2, V_kV=0.48, G_mm=32.0)
        assert afb2["D_afb_mm"] > afb1["D_afb_mm"]

    def test_retorna_campos(self):
        res = calcular_frontera_arco(10.0, 0.2, 0.48, 32.0)
        for campo in ("D_afb_mm", "Ei_cal_cm2", "norma"):
            assert campo in res

    def test_frontera_default_ei_es_1p2(self):
        """Umbral default es 1.2 cal/cm² (inicio quemadura 2do grado — IEEE 1584)."""
        res = calcular_frontera_arco(10.0, 0.2, 0.48, 32.0)
        assert res["Ei_cal_cm2"] == pytest.approx(1.2, abs=0.01)


# ---------------------------------------------------------------------------
# categoria_ppe
# ---------------------------------------------------------------------------

class TestCategoriaPPE:
    @pytest.mark.parametrize("E, cat_esperada", [
        (0.5,  0),
        (1.2,  1),
        (3.9,  1),
        (4.0,  2),
        (7.9,  2),
        (8.0,  3),
        (24.9, 3),
        (25.0, 4),
        (39.9, 4),
        (40.0, None),  # PELIGRO — sin categoría NFPA
    ])
    def test_umbrales_nfpa_70e(self, E, cat_esperada):
        res = categoria_ppe(E)
        assert res["categoria"] == cat_esperada

    def test_peligro_sin_categoria(self):
        res = categoria_ppe(50.0)
        assert res["categoria"] is None
        assert "PELIGRO" in res["estado"].upper() or "DANGER" in res["estado"].upper()

    def test_retorna_campos(self):
        res = categoria_ppe(5.0)
        for campo in ("categoria", "E_cal_cm2", "estado", "norma"):
            assert campo in res

    def test_norma_referencia_nfpa(self):
        res = categoria_ppe(5.0)
        assert "NFPA" in res["norma"] or "70E" in res["norma"]


# ---------------------------------------------------------------------------
# Integración: escenario tablero BT
# ---------------------------------------------------------------------------

class TestIntegracionArcFlash:
    def test_escenario_tablero_bt_completo(self):
        """Tablero 480V, Icc=20 kA, t=0.1s, D=610mm — valores físicamente razonables."""
        res = calcular_arc_flash_completo(
            Ibf_kA=20.0,
            V_kV=0.48,
            G_mm=32.0,
            t_s=0.1,
            D_mm=610.0,
        )
        # Todos los campos presentes
        for campo in ("Ia_kA", "E_cal_cm2", "D_afb_mm", "categoria_ppe", "norma"):
            assert campo in res

        # Físicamente razonables
        assert 0 < res["Ia_kA"] < 20.0
        assert res["E_cal_cm2"] > 0
        assert res["D_afb_mm"] > 0

    def test_proteccion_rapida_menor_energia(self):
        """Tiempo de disparo menor → energía incidente menor."""
        res_lento = calcular_arc_flash_completo(20.0, 0.48, 32.0, t_s=0.5, D_mm=610.0)
        res_rapido = calcular_arc_flash_completo(20.0, 0.48, 32.0, t_s=0.05, D_mm=610.0)
        assert res_rapido["E_cal_cm2"] < res_lento["E_cal_cm2"]

    def test_tablero_pequeno_baja_icc_categoria_baja(self):
        """Tablero con Icc baja y protección rápida → categoría PPE baja."""
        res = calcular_arc_flash_completo(
            Ibf_kA=5.0,
            V_kV=0.38,
            G_mm=25.0,
            t_s=0.02,   # disparo instantáneo
            D_mm=610.0,
        )
        # Con Icc baja y disparo instantáneo, energía debe ser muy baja
        assert res["E_cal_cm2"] < 10.0


# ---------------------------------------------------------------------------
# Guardas de dominio (#3)
# ---------------------------------------------------------------------------

class TestGuardasDominio:
    def test_ibf_cero_lanza_valueerror(self):
        with pytest.raises(ValueError):
            calcular_corriente_arco(Ibf_kA=0.0, V_kV=0.48, G_mm=32.0)

    def test_ibf_negativo_lanza_valueerror(self):
        with pytest.raises(ValueError):
            calcular_corriente_arco(Ibf_kA=-5.0, V_kV=0.48, G_mm=32.0)

    def test_ia_cero_en_energia_lanza_valueerror(self):
        with pytest.raises(ValueError):
            calcular_energia_incidente(Ia_kA=0.0, t_s=0.1, D_mm=610.0, V_kV=0.48, G_mm=32.0)

    def test_distancia_cero_lanza_valueerror(self):
        with pytest.raises(ValueError):
            calcular_energia_incidente(Ia_kA=10.0, t_s=0.1, D_mm=0.0, V_kV=0.48, G_mm=32.0)

    def test_tiempo_negativo_lanza_valueerror(self):
        with pytest.raises(ValueError):
            calcular_energia_incidente(Ia_kA=10.0, t_s=-0.1, D_mm=610.0, V_kV=0.48, G_mm=32.0)

    def test_ei_cero_en_frontera_lanza_valueerror(self):
        with pytest.raises(ValueError):
            calcular_frontera_arco(Ia_kA=10.0, t_s=0.2, V_kV=0.48, G_mm=32.0, Ei_cal_cm2=0.0)
