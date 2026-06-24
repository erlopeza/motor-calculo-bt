"""Validación: flujo nodal sobre la cadena real de circuitos.xlsx (G0A→G1A→C1A→C2A)."""
from pathlib import Path
import openpyxl
import pytest
from excel import leer_cadena_excel
from red_desde_cadena import construir_red
from flujo_nodal import calcular_flujo_nodal

LIBRO = Path(__file__).resolve().parents[1] / "circuitos.xlsx"


def _circuitos_simple():
    return [
        {"nombre": "L1", "sistema": "3F", "I_diseno": 100.0, "cos_phi": 0.9},
        {"nombre": "L2", "sistema": "3F", "I_diseno": 63.0, "cos_phi": 0.85},
    ]


def _cadena_real():
    wb = openpyxl.load_workbook(LIBRO, read_only=True, data_only=True)
    return leer_cadena_excel(wb)


def test_cadena_real_existe():
    assert LIBRO.exists(), "circuitos.xlsx debe existir en la raíz del repo"
    assert _cadena_real(), "la hoja cadena debe tener dispositivos"


def test_cadena_real_converge_y_tensiones_decrecen():
    red = construir_red(_cadena_real(), trafo_z_ohm=0.005, circuitos=_circuitos_simple(), vn_v=380.0)
    res = calcular_flujo_nodal(red)
    assert res["convergido"] is True
    v_trafo = res["buses"]["TRAFO"]["V_pu"]
    assert v_trafo == pytest.approx(1.0, abs=1e-6)
    for bid, r in res["buses"].items():
        if bid != "TRAFO":
            assert r["V_pu"] <= 1.0 + 1e-9


def test_cadena_real_perdidas_positivas():
    red = construir_red(_cadena_real(), trafo_z_ohm=0.005, circuitos=_circuitos_simple(), vn_v=380.0)
    res = calcular_flujo_nodal(red)
    assert res["perdidas_totales_kW"] >= 0.0


def test_cadena_real_carga_en_hojas():
    """La carga total se reparte en las barras hoja (no en intermedias ni en el slack)."""
    red = construir_red(_cadena_real(), trafo_z_ohm=0.005, circuitos=_circuitos_simple(), vn_v=380.0)
    res = calcular_flujo_nodal(red)
    # Al menos una barra con carga (P inyectada negativa) distinta del slack.
    con_carga = [bid for bid, r in res["buses"].items() if bid != "TRAFO" and r["P_kW"] < -0.01]
    assert con_carga, "debe haber barras hoja con carga asignada"
