from gui_core.sesion import SesionProyecto
from gui_core.presentadores import presentar_reporte


def test_presentar_reporte_sin_calculos_indica_gate():
    s = SesionProyecto()
    r = presentar_reporte(s)
    assert "apto_emision" in r
    assert isinstance(r["alertas"], list)


def test_presentar_reporte_con_datos_minimos(tmp_path):
    s = SesionProyecto()
    s.cargar({
        "proyecto": "T", "perfil": "industrial",
        "circuitos": [{"nombre": "C-01", "conductor": "6AWG", "S_mm2": 13.3,
                       "I_diseno": 40.0, "I_max": 65.0, "cos_phi": 0.9, "L_m": 15.0,
                       "paralelos": 1, "sistema": "3F", "dv_pct": 0.3, "icc_ka": 10.0,
                       "estado": "OK", "norma": "MM2"}],
    })
    r = presentar_reporte(s, carpeta_salida=str(tmp_path))
    assert r["ruta_docx"].endswith(".docx")
