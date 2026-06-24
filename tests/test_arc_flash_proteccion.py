"""P1.1 integración — puente arc_flash ↔ protección (t de despeje en Ia)."""
import pytest
from arc_flash import arc_flash_desde_proteccion


class TestPuenteArcFlash:
    def test_dict_completo(self):
        r = arc_flash_desde_proteccion(Ibf_kA=20.0, V_kV=0.4, In_A=250, curva="C")
        for k in ("Ia_kA", "t_despeje_s", "region_despeje", "E_cal_cm2",
                  "D_afb_mm", "categoria_ppe", "despeje_incierto", "verificar_simaris"):
            assert k in r

    def test_ia_menor_que_ibf(self):
        r = arc_flash_desde_proteccion(20.0, 0.4, 250, "C")
        assert 0 < r["Ia_kA"] < 20.0

    def test_falla_alta_dispara_instantaneo(self):
        # Ia muy por encima del umbral magnético C (10×In) → instantáneo 0.02 s
        r = arc_flash_desde_proteccion(Ibf_kA=25.0, V_kV=0.4, In_A=100, curva="C")
        assert r["region_despeje"] == "instantaneo"
        assert r["t_despeje_s"] == pytest.approx(0.02, abs=1e-6)

    def test_proteccion_no_despeja_aplica_techo_y_bandera(self):
        # In enorme respecto a Ia → no dispara → techo 2 s + bandera
        r = arc_flash_desde_proteccion(Ibf_kA=2.0, V_kV=0.4, In_A=4000, curva="C")
        assert r["despeje_incierto"] is True
        assert r["t_despeje_s"] == pytest.approx(2.0, abs=1e-6)

    def test_energia_positiva(self):
        r = arc_flash_desde_proteccion(20.0, 0.4, 250, "C")
        assert r["E_cal_cm2"] > 0

    def test_techo_parametrizable(self):
        r = arc_flash_desde_proteccion(2.0, 0.4, 4000, "C", t_techo_s=1.0)
        assert r["t_despeje_s"] == pytest.approx(1.0, abs=1e-6)

    def test_verificar_simaris_aplica_techo_y_bandera(self):
        # ETU en región térmica propietaria → verificar_simaris + techo
        r = arc_flash_desde_proteccion(Ibf_kA=5.0, V_kV=0.4, In_A=100, curva="ETU600")
        assert r["verificar_simaris"] is True
        assert r["despeje_incierto"] is False
        assert r["t_despeje_s"] == pytest.approx(2.0, abs=1e-6)
