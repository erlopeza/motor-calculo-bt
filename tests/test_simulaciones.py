from __future__ import annotations

import uuid
from pathlib import Path

from simulaciones.analizador import (
    analizar_todos,
    calcular_divergencia,
    calcular_resultado_motor,
)
from simulaciones.escenarios import ESCENARIOS
from simulaciones.reporte import generar_reporte_divergencias


def _tmp_dir() -> Path:
    base = Path(__file__).resolve().parent / ".tmp_simulaciones"
    base.mkdir(parents=True, exist_ok=True)
    d = base / uuid.uuid4().hex
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resultados():
    return analizar_todos(ESCENARIOS)


def test_analizar_todos_retorna_6_resultados():
    out = _resultados()
    assert len(out) == 6


def test_resultado_tiene_campos_obligatorios():
    out = _resultados()[0]
    requeridos = {
        "id",
        "descripcion",
        "resultado_motor",
        "resultado_simaris",
        "divergencia_pct",
        "categoria",
        "justificacion",
        "accion",
    }
    assert requeridos.issubset(set(out.keys()))


def test_S01_categoria_supuesto_conservador():
    out = {x["id"]: x for x in _resultados()}
    assert out["S01"]["categoria"] == "SUPUESTO_CONSERVADOR"


def test_S03_categoria_equipo_distinto():
    out = {x["id"]: x for x in _resultados()}
    assert out["S03"]["categoria"] == "EQUIPO_DISTINTO"


def test_S04_categoria_variable_ignorada():
    out = {x["id"]: x for x in _resultados()}
    assert out["S04"]["categoria"] == "VARIABLE_IGNORADA"


def test_S06_categoria_variable_ignorada():
    out = {x["id"]: x for x in _resultados()}
    assert out["S06"]["categoria"] == "VARIABLE_IGNORADA"


def test_divergencia_positiva_cuando_motor_mayor():
    d = calcular_divergencia({"x": 12}, {"x": 10}, "x")
    assert d > 0


def test_divergencia_negativa_cuando_motor_menor():
    d = calcular_divergencia({"x": 8}, {"x": 10}, "x")
    assert d < 0


def test_divergencia_cero_cuando_iguales():
    d = calcular_divergencia({"x": 10}, {"x": 10}, "x")
    assert d == 0


def test_reporte_genera_string_no_vacio():
    txt = generar_reporte_divergencias(_resultados())
    assert isinstance(txt, str)
    assert len(txt.strip()) > 0


def test_reporte_contiene_todos_los_ids():
    txt = generar_reporte_divergencias(_resultados())
    for sid in ("S01", "S02", "S03", "S04", "S05", "S06"):
        assert sid in txt


def test_reporte_contiene_resumen():
    txt = generar_reporte_divergencias(_resultados())
    assert "RESUMEN" in txt
    assert "Escenarios analizados" in txt


def test_reporte_escribe_archivo_si_ruta_definida():
    ruta = _tmp_dir() / "divergencias.txt"
    out = generar_reporte_divergencias(_resultados(), ruta_salida=str(ruta))
    assert out == str(ruta)
    assert ruta.exists()


def test_S01_motor_calcula_icc_trafo():
    e = next(x for x in ESCENARIOS if x["id"] == "S01")
    r = calcular_resultado_motor(e)
    assert r["Icc_max_kA"] > 0
    assert r["Icc_min_kA"] > 0


def test_S03_motor_calcula_icc_ge_stamford():
    e = next(x for x in ESCENARIOS if x["id"] == "S03")
    r = calcular_resultado_motor(e)
    assert r["Ik3_pp_kA"] > 0
    assert r["Icc_kA"] == r["Ik3_pp_kA"]


def test_S04_motor_calcula_dv_t20_y_t60():
    e = next(x for x in ESCENARIOS if x["id"] == "S04")
    r = calcular_resultado_motor(e)
    assert r["dv_t20_pct"] > 0
    assert r["dv_t60_pct"] > r["dv_t20_pct"]


def test_S06_motor_calcula_demanda_gi_real():
    e = next(x for x in ESCENARIOS if x["id"] == "S06")
    r = calcular_resultado_motor(e)
    assert r["Ib_A"] > e["resultado_simaris"]["Ib_A"]
    assert r["gi_real"] == e["parametros_motor"]["gi_real_datacenter"]


def test_S02_incluye_impedancia_cable():
    e = next(x for x in ESCENARIOS if x["id"] == "S02")
    r = calcular_resultado_motor(e)
    assert r["Zt_cable_ohm"] > 0
    assert r["Icc_kA"] < 40  # menor que bornes trafo por suma de Z_cable


def test_S04_tiene_nota_tecnica():
    e = next(x for x in ESCENARIOS if x["id"] == "S04")
    assert "nota_tecnica" in e
    assert "SIMARIS incluye" in e["nota_tecnica"]


def test_S05_tiene_nota_tecnica():
    e = next(x for x in ESCENARIOS if x["id"] == "S05")
    assert "nota_tecnica" in e
    assert "sumar DeltaU_trafo" in e["nota_tecnica"]


def test_reporte_muestra_nota_tecnica_cuando_existe():
    txt = generar_reporte_divergencias(_resultados())
    assert "S04 - DeltaV circuito C/L 18.1" in txt
    assert "Nota tecnica:" in txt
