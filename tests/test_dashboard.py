from streamlit.testing.v1 import AppTest


def _app() -> AppTest:
    return AppTest.from_file("dashboard.py", default_timeout=10)


def test_detalle_muestra_las_4_rutas_de_reporte():
    at = _app()
    at.run()
    ti = at.sidebar.text_input[0]
    ti.set_value("motor_bt.db").run()
    assert not at.exception
    textos = " ".join(t.value for t in at.text)
    assert "ruta_reporte_txt" in textos
    assert "ruta_reporte_xlsx" in textos
    assert "ruta_reporte_docx" in textos
    assert "ruta_reporte_pdf" in textos
