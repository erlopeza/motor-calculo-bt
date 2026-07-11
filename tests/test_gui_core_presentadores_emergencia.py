import json

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


def test_presentar_reporte_status_con_falla_real(tmp_path):
    s = SesionProyecto()
    s.cargar({
        "proyecto": "T", "perfil": "industrial",
        "circuitos": [{"nombre": "C-01", "conductor": "6AWG", "S_mm2": 13.3,
                       "I_diseno": 40.0, "I_max": 65.0, "cos_phi": 0.9, "L_m": 15.0,
                       "paralelos": 1, "sistema": "3F", "norma": "MM2"}],
    })
    s.registrar("dv", {"filas": [{"nombre": "C-01", "dv_v": 20, "dv_pct": 6.0,
                                  "estado": "FALLA"}]}, ["C-01"])
    r = presentar_reporte(s, carpeta_salida=str(tmp_path))
    assert r["ruta_json"].endswith(".json")
    with open(r["ruta_json"], "r", encoding="utf-8") as f:
        payload = json.load(f)
    resultados = payload["resultados"]
    assert resultados["status"] == "CON_FALLAS"
    assert resultados["n_fallas"] >= 1


def test_presentar_reporte_alerta_gate_con_ats_en_default(tmp_path):
    s = SesionProyecto()
    s.cargar({
        "proyecto": "T", "perfil": "industrial",
        "circuitos": [{"nombre": "C-01", "conductor": "6AWG", "S_mm2": 13.3,
                       "I_diseno": 40.0, "I_max": 65.0, "cos_phi": 0.9, "L_m": 15.0,
                       "paralelos": 1, "sistema": "3F", "norma": "MM2"}],
    })
    s.ats = {"t_arranque_ge_ms": 10000.0}
    r = presentar_reporte(s, carpeta_salida=str(tmp_path))
    assert r["apto_emision"] is False
    assert r["nivel"] == "INCOMPLETO"


def test_presentar_reporte_alerta_si_dv_no_calculado(tmp_path):
    s = SesionProyecto()
    s.cargar({
        "proyecto": "T", "perfil": "industrial",
        "circuitos": [{"nombre": "C-01", "conductor": "6AWG", "S_mm2": 13.3,
                       "I_diseno": 40.0, "I_max": 65.0, "cos_phi": 0.9, "L_m": 15.0,
                       "paralelos": 1, "sistema": "3F", "norma": "MM2"}],
    })
    r = presentar_reporte(s, carpeta_salida=str(tmp_path))
    assert any("ΔV" in a or "no calculado" in a for a in r["alertas"])
