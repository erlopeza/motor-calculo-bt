"""Robustez del ensamblado de reporte en main.py.

main.py ahora es importable (bloque interactivo bajo `if __name__ == '__main__'`).
Las funciones generar_seccion_* y generar_reporte_txt deben producir texto sin
crashear ante secciones ausentes (None) o datos mínimos.
"""
import main


def _circuito():
    return {
        "nombre": "C-01", "sistema": "3F", "conductor": "6AWG", "S_mm2": 13.3,
        "I_max": 65.0, "paralelos": 1, "I_diseno": 40.0, "cos_phi": 0.9,
        "L_m": 15.0, "temp_amb": 30,
    }


# ---------------------------------------------------------------------------
# main.py importable sin disparar la shell interactiva
# ---------------------------------------------------------------------------

def test_main_importable_sin_efectos():
    # Si el import disparara input(), la suite entera colgaría.
    assert callable(main.generar_reporte_txt)
    assert callable(main.generar_seccion_transformador)


# ---------------------------------------------------------------------------
# Secciones con entradas ausentes / degeneradas
# ---------------------------------------------------------------------------

class TestSeccionesDegeneradas:
    def test_transformador_none(self):
        lineas, res = main.generar_seccion_transformador(None)
        assert isinstance(lineas, list) and res == {}

    def test_transformador_dict_vacio_no_crashea(self):
        lineas, res = main.generar_seccion_transformador({})
        assert isinstance(lineas, list) and res == {}

    def test_motores_vacio(self):
        assert main.generar_seccion_motores([]) == []

    def test_generador_sin_datos(self):
        assert main.generar_seccion_generador([], None) == []

    def test_sts_none_y_vacio(self):
        assert main.generar_seccion_sts(None) == []
        assert main.generar_seccion_sts({}) == []

    def test_trafo_iso_none(self):
        assert main.generar_seccion_trafo_iso(None) == []

    def test_ups_none(self):
        assert main.generar_seccion_ups(None) == []

    def test_ats_none(self):
        assert main.generar_seccion_ats(None) == []


# ---------------------------------------------------------------------------
# Reporte completo
# ---------------------------------------------------------------------------

class TestReporteTxt:
    def test_reporte_minimo_sin_secciones(self):
        lineas, ok, falla = main.generar_reporte_txt("PROY", [], "01/01/2026")
        assert isinstance(lineas, list) and lineas
        assert ok == 0 and falla == 0

    def test_reporte_un_circuito(self):
        lineas, ok, falla = main.generar_reporte_txt("PROY", [_circuito()], "01/01/2026")
        texto = "\n".join(lineas)
        assert "C-01" in texto
        assert ok + falla == 1

    def test_reporte_con_trafo_valido(self):
        trafo = {"nombre": "T1", "modo": "A", "kVA": 1000.0, "Vn_BT": 380.0,
                 "Ucc_pct": 5.0, "conexion": "Dyn11"}
        lineas, ok, falla = main.generar_reporte_txt(
            "PROY", [_circuito()], "01/01/2026", datos_trafo=trafo)
        assert isinstance(lineas, list) and lineas
