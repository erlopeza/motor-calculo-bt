import csv
import json
import uuid
from pathlib import Path

from exportar_eventos import derivar_evento, exportar_json, exportar_csv
from persistencia import registrar_ejecucion


def _ruta_local(nombre: str, extension: str) -> str:
    base = Path(__file__).resolve().parent / ".tmp_exportar_eventos_tests"
    base.mkdir(parents=True, exist_ok=True)
    return str(base / f"{nombre}_{uuid.uuid4().hex}.{extension}")


def _datos_run_base():
    return {
        "project_id": "LEO-ARICA",
        "revision": "Rev12",
        "perfil": "industrial",
        "norma": "AWG",
        "n_circuitos": 10,
        "n_ok": 9,
        "n_advertencias": 0,
        "n_fallas": 0,
        "max_dv_pct": 2.5,
        "max_icc_ka": 30.39,
        "status": "OK",
        "ruta_reporte_txt": "reporte.txt",
        "ruta_reporte_xlsx": "reporte.xlsx",
    }


def test_derivar_evento_ok():
    run = {
        "run_id": "abc",
        "project_id": "P1",
        "revision": "Rev01",
        "timestamp": "2026-04-18T16:49:00",
        "status": "OK",
        "n_fallas": 0,
        "ruta_reporte_txt": None,
    }
    evento = derivar_evento(run)
    assert evento["estado"] == "COMPLETADO"
    assert evento["event_type"] == "CALCULO_BT"


def test_derivar_evento_falla():
    run = {
        "run_id": "def",
        "project_id": "P1",
        "revision": "Rev02",
        "timestamp": "2026-04-18T16:50:00",
        "status": "CON_FALLAS",
        "n_fallas": 2,
        "ruta_reporte_txt": None,
    }
    evento = derivar_evento(run)
    assert evento["event_type"] == "ALERTA"
    assert evento["estado"] == "EN_REVISION"


def test_exportar_json():
    ruta_db = _ruta_local("runs_json", "db")
    registrar_ejecucion(_datos_run_base(), ruta_db=ruta_db)

    ruta_json = _ruta_local("eventos", "json")
    exportar_json(ruta_json, ruta_db=ruta_db)

    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 1
    assert "run_id" in data[0]
    assert "event_type" in data[0]


def test_exportar_csv():
    ruta_db = _ruta_local("runs_csv", "db")
    registrar_ejecucion(_datos_run_base(), ruta_db=ruta_db)

    ruta_csv = _ruta_local("eventos", "csv")
    exportar_csv(ruta_csv, ruta_db=ruta_db)

    with open(ruta_csv, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert "run_id" in rows[0]
    assert "estado" in rows[0]
