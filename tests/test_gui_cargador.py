from pathlib import Path

from gui.cargador import cargar_excel_a_sesion
from gui_core.sesion import SesionProyecto

LIBRO = Path(__file__).resolve().parents[1] / "circuitos.xlsx"


def test_cargar_excel_puebla_sesion():
    assert LIBRO.exists()
    s = SesionProyecto()
    resumen = cargar_excel_a_sesion(str(LIBRO), s)
    assert s.tiene_circuitos
    assert isinstance(resumen, dict) and "hojas" in resumen
    assert resumen["hojas"] >= 1


def test_cargar_excel_inexistente_no_crashea():
    s = SesionProyecto()
    resumen = cargar_excel_a_sesion("no-existe.xlsx", s)
    assert resumen["error"]
    assert not s.tiene_circuitos
