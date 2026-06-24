"""Mapeo cadena de coordinación → Red (flujo_nodal)."""
import math
import pytest
from red_desde_cadena import construir_red


def _cadena_min():
    return [
        {"nombre": "G0", "upstream": "", "nivel": 0, "In_A": 1600, "curva": "ETU600", "Icc_kA": 30.0},
        {"nombre": "G1", "upstream": "G0", "nivel": 1, "In_A": 630, "curva": "ETU320", "Icc_kA": 10.0},
        {"nombre": "C2", "upstream": "G1", "nivel": 2, "In_A": 160, "curva": "C", "Icc_kA": 5.0},
    ]


def _circuitos_min():
    return [
        {"nombre": "L1", "sistema": "3F", "I_diseno": 100.0, "cos_phi": 0.9},
        {"nombre": "L2", "sistema": "3F", "I_diseno": 80.0, "cos_phi": 0.9},
    ]


def _rama(red, frm, to):
    return next(r for r in red.ramas if r.from_bus == frm and r.to_bus == to)


def _carga_total_circuitos(circuitos):
    tot = 0.0
    for c in circuitos:
        v = 380.0 if c["sistema"] == "3F" else 220.0
        f = math.sqrt(3) if c["sistema"] == "3F" else 1.0
        tot += f * v * float(c["I_diseno"]) * float(c["cos_phi"]) / 1000.0
    return tot


# --- topología ---
def test_construye_red_con_slack_trafo():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    slacks = [b for b in red.buses if b.tipo == "slack"]
    assert len(slacks) == 1 and slacks[0].id == "TRAFO"

def test_un_bus_por_dispositivo():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    ids = {b.id for b in red.buses}
    assert {"G0", "G1", "C2"}.issubset(ids)

def test_ramas_siguen_upstream():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    pares = {(r.from_bus, r.to_bus) for r in red.ramas}
    assert ("TRAFO", "G0") in pares
    assert ("G0", "G1") in pares
    assert ("G1", "C2") in pares

# --- impedancia desde Icc ---
def test_z_rama_positiva_y_creciente_en_profundidad():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    z_g1 = _rama(red, "G0", "G1")
    z_c2 = _rama(red, "G1", "C2")
    assert z_g1.R_ohm > 0 and z_c2.R_ohm > 0
    assert abs(complex(z_c2.R_ohm, z_c2.X_ohm)) > abs(complex(z_g1.R_ohm, z_g1.X_ohm))

def test_z_rama_coincide_con_escalera_icc():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min(), xr=0.1, vn_v=380.0)
    z_g1_acum = 1.05 * 380.0 / (math.sqrt(3) * 10000.0)
    z_g0_acum = 1.05 * 380.0 / (math.sqrt(3) * 30000.0)
    z_rama_esperada = z_g1_acum - z_g0_acum
    r = _rama(red, "G0", "G1")
    assert abs(complex(r.R_ohm, r.X_ohm)) == pytest.approx(z_rama_esperada, rel=1e-3)

def test_nodo_sin_icc_se_excluye():
    cadena = _cadena_min() + [
        {"nombre": "X9", "upstream": "C2", "nivel": 3, "In_A": 32, "curva": "C", "Icc_kA": None},
    ]
    red = construir_red(cadena, trafo_z_ohm=0.005, circuitos=_circuitos_min())
    ids = {b.id for b in red.buses}
    assert "X9" not in ids

# --- cargas en hojas ---
def test_carga_solo_en_hojas():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    g0 = next(b for b in red.buses if b.id == "G0")
    c2 = next(b for b in red.buses if b.id == "C2")
    assert g0.P_kW == 0.0
    assert c2.P_kW < 0.0

def test_carga_total_conservada():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    p_cargas = -sum(b.P_kW for b in red.buses if b.tipo == "PQ")
    esperado = _carga_total_circuitos(_circuitos_min())
    assert p_cargas == pytest.approx(esperado, rel=1e-6)

def test_reparto_por_peso_de_In():
    cadena = [
        {"nombre": "G0", "upstream": "", "nivel": 0, "In_A": 1000, "curva": "TM", "Icc_kA": 20.0},
        {"nombre": "HojaA", "upstream": "G0", "nivel": 1, "In_A": 200, "curva": "C", "Icc_kA": 8.0},
        {"nombre": "HojaB", "upstream": "G0", "nivel": 1, "In_A": 100, "curva": "C", "Icc_kA": 8.0},
    ]
    red = construir_red(cadena, trafo_z_ohm=0.005, circuitos=_circuitos_min())
    a = next(b for b in red.buses if b.id == "HojaA")
    b = next(b for b in red.buses if b.id == "HojaB")
    assert abs(a.P_kW) == pytest.approx(2 * abs(b.P_kW), rel=1e-6)
