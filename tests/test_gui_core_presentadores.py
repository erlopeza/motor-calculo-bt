from gui_core.sesion import SesionProyecto
from gui_core.presentadores import (
    presentar_dv, presentar_icc_trafo, presentar_icc_punto,
    presentar_arc_flash, presentar_coordinacion,
    presentar_flujo_nodal,
)


def _sesion_basica():
    s = SesionProyecto()
    s.cargar({
        "circuitos": [{
            "nombre": "C-01", "sistema": "3F", "conductor": "6AWG", "S_mm2": 13.3,
            "I_max": 65.0, "paralelos": 1, "I_diseno": 40.0, "cos_phi": 0.9,
            "L_m": 15.0, "temp_amb": 30,
        }],
        "trafo": {"modo": "A", "kVA": 1000.0, "Vn_BT": 380.0, "Ucc_pct": 5.0},
    })
    return s


def test_presentar_dv_devuelve_filas_y_estado():
    r = presentar_dv(_sesion_basica())
    assert r["filas"] and "dv_pct" in r["filas"][0]
    assert isinstance(r["alertas"], list)


def test_presentar_dv_marca_alerta_en_falla():
    s = SesionProyecto()
    s.cargar({"circuitos": [{
        "nombre": "LARGO", "sistema": "3F", "conductor": "14AWG", "S_mm2": 2.08,
        "I_max": 25.0, "paralelos": 1, "I_diseno": 24.0, "cos_phi": 0.9,
        "L_m": 300.0, "temp_amb": 30,
    }]})
    r = presentar_dv(s)
    assert r["alertas"]


def test_presentar_icc_trafo():
    r = presentar_icc_trafo(_sesion_basica())
    assert r["Icc_kA"] > 0 and r["Zt_ohm"] > 0


def test_presentar_icc_punto_por_circuito():
    r = presentar_icc_punto(_sesion_basica())
    assert r["filas"] and r["filas"][0]["Icc_kA"] > 0


def test_presentar_arc_flash_por_circuito():
    s = _sesion_basica()
    s.cargar({"protecciones": {"C-01": {"In_A": 100, "curva": "C"}}})
    r = presentar_arc_flash(s)
    assert r["filas"] and r["filas"][0]["E_cal_cm2"] > 0
    assert isinstance(r["alertas"], list)


def test_presentar_coordinacion_sin_cadena_vacio():
    r = presentar_coordinacion(SesionProyecto())
    assert r["filas"] == [] and r["alertas"] == []


def test_presentar_flujo_nodal_sin_cadena_vacio():
    r = presentar_flujo_nodal(SesionProyecto())
    assert r["buses"] == [] and r["alertas"] == []


def test_presentar_flujo_nodal_con_cadena():
    s = SesionProyecto()
    s.cargar({
        "cadena": [
            {"nombre": "G0", "upstream": "", "nivel": 0, "In_A": 1600, "curva": "C", "Icc_kA": 30.0},
            {"nombre": "C2", "upstream": "G0", "nivel": 1, "In_A": 160, "curva": "C", "Icc_kA": 6.0},
        ],
        "circuitos": [{"nombre": "L1", "sistema": "3F", "I_diseno": 100.0, "cos_phi": 0.9}],
        "trafo_z_ohm": 0.007,
    })
    r = presentar_flujo_nodal(s)
    assert any(b["id"] == "TRAFO" for b in r["buses"])
    assert r["convergido"] is True
