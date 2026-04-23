from __future__ import annotations

import math
import uuid
from pathlib import Path

from commissioning.p1_continuidad import protocolo_continuidad
from commissioning.p2_motores import protocolo_motores
from commissioning.p3_transferencia import protocolo_sts, protocolo_transferencia
from commissioning.p4_icc import protocolo_icc
from commissioning.reporte import generar_protocolo_completo


def _tmp_dir() -> Path:
    base = Path(__file__).resolve().parent / ".tmp_commissioning"
    base.mkdir(parents=True, exist_ok=True)
    d = base / uuid.uuid4().hex
    d.mkdir(parents=True, exist_ok=True)
    return d


def _circuitos():
    return [
        {"nombre": "ALIMENTADOR-01", "conductor": "3x240mm2CU", "L_m": 25, "S_mm2": 240, "icc_ka": 27.469},
        {"nombre": "CIRCUITO-01", "conductor": "3x95mm2CU", "L_m": 5, "S_mm2": 95, "icc_ka": 19.333},
    ]


def _motores():
    return [
        {
            "nombre": "BOMBA-01",
            "I_n": 29.14,
            "arranque": {"I_arranque": 174.84},
            "dv_arranque": {"dv_pct": 8.2},
            "proteccion": {"t_arranque_max_s": 8.0},
        }
    ]


def _ats_open():
    return {
        "nombre": "ATS01",
        "modo_transferencia": "open",
        "V_nominal_V": 400.0,
        "t_deteccion_ms": 3000.0,
        "t_arranque_ge_ms": 10000.0,
        "tiempos": {"t_total_ms": 18200.0},
    }


def _ats_closed():
    r = _ats_open()
    r["modo_transferencia"] = "closed"
    return r


def _ats_sts():
    return {
        "nombre": "STS01",
        "modo_transferencia": "sts",
        "V_nominal_V": 400.0,
        "tiempos": {"t_total_ms": 4.0},
    }


def _icc_ref():
    return {"Vn_V": 400, "trafo_sec_kA": 32.736, "bus_principal_kA": 27.469}


def test_p1_retorna_dict_con_mediciones():
    p1 = protocolo_continuidad(_circuitos())
    assert isinstance(p1, dict)
    assert len(p1["mediciones"]) == 2


def test_p1_R_max_calculada_correctamente():
    p1 = protocolo_continuidad([{"nombre": "C1", "L_m": 25, "S_mm2": 240}])
    r = p1["mediciones"][0]["R_max_ohm"]
    esperado = 0.01724 * 25 / 240
    assert abs(r - esperado) < 1e-6


def test_p1_cada_medicion_tiene_campos_obligatorios():
    p1 = protocolo_continuidad(_circuitos())
    m = p1["mediciones"][0]
    req = {"circuito", "conductor", "longitud_m", "R_max_ohm", "R_tierra_max_ohm", "criterio", "resultado"}
    assert req.issubset(set(m.keys()))


def test_p2_retorna_dict_con_pruebas():
    p2 = protocolo_motores(_motores())
    assert isinstance(p2, dict)
    assert len(p2["pruebas"]) == 1


def test_p2_rango_I_arranque_es_10pct():
    p2 = protocolo_motores(_motores())
    pr = p2["pruebas"][0]
    i = pr["I_arranque_esperada_A"]
    assert pr["I_arranque_min_A"] == round(i * 0.9, 3)
    assert pr["I_arranque_max_A"] == round(i * 1.1, 3)


def test_p2_dv_limite_es_15pct_NCh():
    p2 = protocolo_motores(_motores())
    assert p2["pruebas"][0]["dV_arranque_max_pct"] == 15.0


def test_p2_campos_obligatorios():
    p2 = protocolo_motores(_motores())
    pr = p2["pruebas"][0]
    req = {"motor", "I_nominal_A", "I_arranque_esperada_A", "I_arranque_min_A", "I_arranque_max_A"}
    assert req.issubset(set(pr.keys()))


def test_p3_modo_open_tiene_6_pasos():
    p3 = protocolo_transferencia(_ats_open())
    assert p3["modo"] == "open"
    assert p3["total_pasos"] == 6


def test_p3_modo_closed_tiene_paso_sincronizacion():
    p3 = protocolo_transferencia(_ats_closed())
    criterios = " ".join(x["criterio"] for x in p3["pasos"])
    assert "DeltaV<=5%" in criterios


def test_p3_modo_sts_tiene_medicion_4ms():
    p3 = protocolo_transferencia(_ats_sts())
    assert p3["modo"] == "sts"
    assert any("<= 4 ms" in x["criterio"] for x in p3["pasos"])


def test_p3_valores_esperados_desde_resultado_ats():
    p3 = protocolo_transferencia(_ats_open())
    vals = p3["valores_esperados"]
    assert vals["t_total_ms_esperado"] == 18200.0
    assert vals["V_GE_esperado_V"] == 400.0


def test_p4_Z_lazo_calculada_correctamente():
    p4 = protocolo_icc(_circuitos(), _icc_ref())
    p = next(x for x in p4["puntos"] if x["punto"] == "Bornes trafo sec")
    esperado = 400 / (math.sqrt(3) * 32.736 * 1000)
    assert abs(p["Z_lazo_esperado_ohm"] - esperado) < 1e-6


def test_p4_rango_aceptacion_es_10pct():
    p4 = protocolo_icc(_circuitos(), _icc_ref())
    p = next(x for x in p4["puntos"] if x["punto"] == "Bus principal SWG")
    assert p["Icc_min_aceptable_kA"] == round(p["Icc_calculado_kA"] * 0.9, 3)
    assert p["Icc_max_aceptable_kA"] == round(p["Icc_calculado_kA"] * 1.1, 3)


def test_p4_punto_mas_alejado_incluido():
    p4 = protocolo_icc(_circuitos(), _icc_ref())
    assert any("Punto mas alejado" in x["punto"] for x in p4["puntos"])


def test_reporte_genera_string_no_vacio():
    txt = generar_protocolo_completo(
        protocolo_continuidad(_circuitos()),
        protocolo_motores(_motores()),
        protocolo_transferencia(_ats_open()),
        protocolo_icc(_circuitos(), _icc_ref()),
        nombre_proyecto="LEO-ARICA",
        ejecutante="Equipo Pruebas",
    )
    assert isinstance(txt, str)
    assert len(txt.strip()) > 0


def test_reporte_contiene_P1_P2_P3_P4():
    txt = generar_protocolo_completo(
        protocolo_continuidad(_circuitos()),
        protocolo_motores(_motores()),
        protocolo_transferencia(_ats_open()),
        protocolo_icc(_circuitos(), _icc_ref()),
        nombre_proyecto="LEO-ARICA",
        ejecutante="Equipo Pruebas",
    )
    assert "P1 - CONTINUIDAD" in txt
    assert "P2 - PRUEBA DE MOTORES" in txt
    assert "P3 - PRUEBA DE TRANSFERENCIA" in txt
    assert "P4 - VERIFICACION Icc" in txt


def test_reporte_contiene_firma():
    txt = generar_protocolo_completo(
        protocolo_continuidad(_circuitos()),
        protocolo_motores(_motores()),
        protocolo_transferencia(_ats_open()),
        protocolo_icc(_circuitos(), _icc_ref()),
        nombre_proyecto="LEO-ARICA",
        ejecutante="Equipo Pruebas",
    )
    assert "FIRMA TECNICO" in txt
    assert "FIRMA INGENIERO" in txt


def test_reporte_escribe_archivo_si_ruta():
    ruta = _tmp_dir() / "protocolo.txt"
    out = generar_protocolo_completo(
        protocolo_continuidad(_circuitos()),
        protocolo_motores(_motores()),
        protocolo_transferencia(_ats_open()),
        protocolo_icc(_circuitos(), _icc_ref()),
        nombre_proyecto="LEO-ARICA",
        ejecutante="Equipo Pruebas",
        ruta_salida=str(ruta),
    )
    assert out == str(ruta)
    assert ruta.exists()

