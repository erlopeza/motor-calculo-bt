import os
import uuid
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from graficos import (
    STYLE,
    _color_dv,
    generar_todos,
    grafico_autonomia_ups,
    grafico_balance_fases,
    grafico_commissioning,
    grafico_decremento_ge,
    grafico_divergencias_simaris,
    grafico_dv_circuitos,
    grafico_tcc,
    grafico_transferencia_ats,
)

CIRC = [
    {"id": "C-01", "dv_pct": 0.9},
    {"id": "C-02", "dv_pct": 2.1},
    {"id": "C-03", "dv_pct": 3.8},
    {"id": "C-04", "dv_pct": 5.5},
]
GE = {
    "Ik3_pp_kA": 18.5,
    "Ik3_p_kA": 12.3,
    "Ik3_kA": 6.1,
    "T_pp_s": 0.012,
    "T_p_s": 0.08,
    "Ta_s": 0.018,
}
PROTS = [
    {"nombre": "F1", "tipo": "ETU600", "In_A": 160, "nivel": 1},
    {"nombre": "F2", "tipo": "C", "In_A": 63, "nivel": 2},
]
BAL = {
    "L1_kW": 48.2,
    "L2_kW": 31.5,
    "L3_kW": 44.7,
    "L1_A": 219.0,
    "L2_A": 143.0,
    "L3_A": 203.0,
    "desequilibrio_pct": 21.4,
}
UPS = {"E_bat_kWh": 50.0, "P_bat_kW": 30.0, "t_minimo_normado_min": 15, "eta_ups": 0.94}
ATS = {
    "t_deteccion_ms": 80,
    "t_arranque_ge_ms": 3200,
    "t_estabilizacion_ms": 1500,
    "t_paralelo_ms": 200,
    "t_total_ms": 4980,
}
SIM = [
    {"descripcion": "ΔV C-03", "divergencia_pct": 2.1, "categoria": "SUPUESTO_CONSERVADOR"},
    {"descripcion": "Icc T1", "divergencia_pct": 5.3, "categoria": "ERROR_MOTOR"},
]
COMM = [
    {"prueba": "P1", "circuito": "C-01", "valor_esperado": 0.1, "valor_medido": 0.09, "estado": "APROBADO"},
    {"prueba": "P2", "circuito": "M-01", "valor_esperado": 14.5, "valor_medido": None, "estado": "PENDIENTE"},
]


def _tmp_dir() -> Path:
    base = Path(__file__).resolve().parent / ".tmp_graficos"
    base.mkdir(parents=True, exist_ok=True)
    run_dir = base / uuid.uuid4().hex
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def test_grafico_dv_genera_archivo_png():
    tmp_dir = _tmp_dir()
    r = grafico_dv_circuitos(CIRC, ruta_salida=str(tmp_dir / "dv.png"))
    assert r and os.path.exists(r)


def test_grafico_dv_colores_por_zona_normativa():
    assert _color_dv(0.9) == STYLE["accent"]
    assert _color_dv(2.0) == STYLE["warning"]
    assert _color_dv(4.0) == "#ff8800"
    assert _color_dv(5.5) == STYLE["danger"]


def test_grafico_ge_genera_curva_decremento():
    tmp_dir = _tmp_dir()
    r = grafico_decremento_ge(GE, ruta_salida=str(tmp_dir / "ge.png"))
    assert r and os.path.exists(r)


def test_grafico_ge_3_niveles_icc():
    assert GE["Ik3_pp_kA"] > GE["Ik3_p_kA"] > GE["Ik3_kA"]


def test_grafico_tcc_escala_log_log():
    tmp_dir = _tmp_dir()
    r = grafico_tcc(PROTS, 10.0, ruta_salida=str(tmp_dir / "tcc.png"))
    assert r and os.path.exists(r)


def test_grafico_balance_3_fases():
    tmp_dir = _tmp_dir()
    r = grafico_balance_fases(BAL, ruta_salida=str(tmp_dir / "bal.png"))
    assert r and os.path.exists(r)


def test_grafico_autonomia_linea_normada():
    tmp_dir = _tmp_dir()
    r = grafico_autonomia_ups(UPS, ruta_salida=str(tmp_dir / "ups.png"))
    assert r and os.path.exists(r)


def test_grafico_ats_timeline():
    tmp_dir = _tmp_dir()
    r = grafico_transferencia_ats(ATS, ruta_salida=str(tmp_dir / "ats.png"))
    assert r and os.path.exists(r)


def test_grafico_divergencias_colores_categoria():
    tmp_dir = _tmp_dir()
    r = grafico_divergencias_simaris(SIM, ruta_salida=str(tmp_dir / "sim.png"))
    assert r and os.path.exists(r)


def test_grafico_commissioning_solo_con_medidos():
    tmp_dir = _tmp_dir()
    r = grafico_commissioning(COMM, ruta_salida=str(tmp_dir / "comm.png"))
    assert r and os.path.exists(r)


def test_generar_todos_retorna_dict():
    tmp_dir = _tmp_dir()
    res = {
        "circuitos": CIRC,
        "generador": GE,
        "protecciones": PROTS,
        "balance": BAL,
        "ups": UPS,
        "ats": ATS,
        "simulaciones": SIM,
    }
    d = generar_todos(res, str(tmp_dir))
    assert isinstance(d, dict) and len(d) > 0


def test_generar_todos_omite_tcc_si_no_hay_icc():
    tmp_dir = _tmp_dir()
    res = {
        "tcc": {
            "dispositivos": [
                {"nombre": "F1", "In_A": 160},
                {"nombre": "F2", "In_A": 63},
            ]
        },
    }
    d = generar_todos(res, str(tmp_dir))
    assert "tcc" not in d


def test_generar_todos_reporta_advertencia_tcc_si_no_hay_icc():
    tmp_dir = _tmp_dir()
    res = {
        "tcc": {
            "dispositivos": [
                {"nombre": "F1", "In_A": 160},
                {"nombre": "F2", "In_A": 63},
            ]
        },
    }
    d = generar_todos(res, str(tmp_dir))
    assert d.get("tcc_advertencia") == "Icc_punto_kA no disponible — gráfico TCC omitido"


def test_grafico_no_falla_si_datos_vacios():
    assert grafico_dv_circuitos([]) is None
    assert grafico_tcc([], 10.0) is None
    assert grafico_divergencias_simaris([]) is None
    assert (
        grafico_commissioning(
            [
                {
                    "prueba": "P1",
                    "circuito": "C-01",
                    "valor_esperado": 1.0,
                    "valor_medido": None,
                    "estado": "PENDIENTE",
                }
            ]
        )
        is None
    )
