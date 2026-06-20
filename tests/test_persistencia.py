import sqlite3
import uuid
from pathlib import Path

from persistencia import (
    inicializar_db,
    obtener_circuitos,
    obtener_ejecuciones,
    obtener_eventos,
    registrar_circuitos,
    registrar_ejecucion,
    registrar_evento,
)


def _datos_base():
    return {
        "project_id": "LEO-ARICA",
        "revision": "CLI",
        "perfil": "industrial",
        "norma": "AWG",
        "n_circuitos": 10,
        "n_ok": 9,
        "n_advertencias": 0,
        "n_fallas": 1,
        "max_dv_pct": 6.152,
        "max_icc_ka": 30.39,
        "status": "CON_FALLAS",
        "ruta_reporte_txt": "REPORTE_LEO-ARICA.txt",
        "ruta_reporte_xlsx": "REPORTE_LEO-ARICA.xlsx",
    }


def _ruta_db_local(nombre: str) -> str:
    base = Path(__file__).resolve().parent / ".tmp_persistencia_tests"
    base.mkdir(parents=True, exist_ok=True)
    return str(base / f"{nombre}_{uuid.uuid4().hex}.db")


def test_crear_tabla():
    ruta_db = _ruta_db_local("crear_tabla")
    inicializar_db(ruta_db)

    with sqlite3.connect(ruta_db) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    tablas = {row[0] for row in rows}
    assert "runs" in tablas
    assert "run_reports" in tablas
    assert "technical_events" in tablas
    assert "run_circuits" in tablas


def test_registrar_ejecucion():
    ruta_db = _ruta_db_local("registrar")
    run_id = registrar_ejecucion(_datos_base(), ruta_db=ruta_db)

    ejecuciones = obtener_ejecuciones(ruta_db=ruta_db)
    assert len(ejecuciones) == 1
    assert ejecuciones[0]["run_id"] == run_id
    assert ejecuciones[0]["project_id"] == "LEO-ARICA"
    assert ejecuciones[0]["ruta_reporte_txt"] == "REPORTE_LEO-ARICA.txt"
    assert ejecuciones[0]["ruta_reporte_xlsx"] == "REPORTE_LEO-ARICA.xlsx"

    with sqlite3.connect(ruta_db) as conn:
        n_reports = conn.execute(
            "SELECT COUNT(*) FROM run_reports WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
    assert n_reports == 2


def test_fallo_silencioso():
    # Directorio intermedio no existente: SQLite no puede crear DB ahi.
    ruta_db_invalida = str(
        Path(__file__).resolve().parent / ".tmp_persistencia_tests" / "inexistente" / "test_motor_bt.db"
    )
    try:
        registrar_ejecucion(_datos_base(), ruta_db=ruta_db_invalida)
    except Exception as e:
        raise AssertionError(f"No debia lanzar excepcion: {e}")


def test_commit_none(monkeypatch):
    def _fallar_git(*args, **kwargs):
        raise RuntimeError("sin git")

    monkeypatch.setattr("persistencia.subprocess.check_output", _fallar_git)

    ruta_db = _ruta_db_local("commit_none")
    registrar_ejecucion(_datos_base(), ruta_db=ruta_db)
    ejecuciones = obtener_ejecuciones(ruta_db=ruta_db)

    assert len(ejecuciones) == 1
    assert ejecuciones[0]["commit_hash"] is None
    assert ejecuciones[0]["branch"] is None


def test_registrar_evento():
    ruta_db = _ruta_db_local("registrar_evento")
    run_id = registrar_ejecucion(_datos_base(), ruta_db=ruta_db)

    event_id = registrar_evento(
        run_id,
        {
            "project_id": "LEO-ARICA",
            "revision": "CLI",
            "event_type": "ALERTA",
            "title": "Calculo BT - LEO-ARICA CLI",
            "estado": "EN_REVISION",
            "description": "falla detectada",
            "observaciones": "1 circuito en falla",
        },
        ruta_db=ruta_db,
    )

    assert event_id
    eventos = obtener_eventos(ruta_db=ruta_db)
    assert len(eventos) == 1
    assert eventos[0]["event_id"] == event_id
    assert eventos[0]["run_id"] == run_id


def test_obtener_eventos():
    ruta_db = _ruta_db_local("obtener_eventos")

    run_id_1 = registrar_ejecucion({**_datos_base(), "project_id": "P1"}, ruta_db=ruta_db)
    run_id_2 = registrar_ejecucion({**_datos_base(), "project_id": "P2"}, ruta_db=ruta_db)

    registrar_evento(
        run_id_1,
        {
            "project_id": "P1",
            "revision": "R1",
            "event_type": "CALCULO_BT",
            "title": "Calculo BT - P1 R1",
            "estado": "COMPLETADO",
        },
        ruta_db=ruta_db,
    )
    registrar_evento(
        run_id_2,
        {
            "project_id": "P2",
            "revision": "R1",
            "event_type": "CALCULO_BT",
            "title": "Calculo BT - P2 R1",
            "estado": "COMPLETADO",
        },
        ruta_db=ruta_db,
    )

    eventos_p1 = obtener_eventos(project_id="P1", ruta_db=ruta_db)
    assert len(eventos_p1) == 1
    assert eventos_p1[0]["project_id"] == "P1"


def test_registrar_circuitos():
    ruta_db = _ruta_db_local("registrar_circuitos")
    run_id = registrar_ejecucion(_datos_base(), ruta_db=ruta_db)

    n = registrar_circuitos(
        run_id=run_id,
        circuitos=[
            {
                "nombre": "C-01",
                "conductor": "6AWG",
                "norma": "AWG",
                "S_mm2": 13.3,
                "I_diseno": 50.0,
                "I_max": 65.0,
                "cos_phi": 0.9,
                "L_m": 20.0,
                "paralelos": 1,
                "sistema": "3F",
                "dv_v": 1.2,
                "dv_pct": 0.31,
                "icc_ka": 12.3,
                "estado": "OK",
                "observaciones": "sin observaciones",
            }
        ],
        ruta_db=ruta_db,
    )

    assert n == 1
    circuitos = obtener_circuitos(run_id=run_id, ruta_db=ruta_db)
    assert len(circuitos) == 1
    assert circuitos[0]["nombre"] == "C-01"


def test_circuitos_en_registrar_ejecucion():
    ruta_db = _ruta_db_local("circuitos_en_run")
    datos = _datos_base()
    datos["circuitos"] = [
        {
            "nombre": "C-02",
            "conductor": "4AWG",
            "norma": "AWG",
            "S_mm2": 21.1,
            "I_diseno": 60.0,
            "I_max": 85.0,
            "cos_phi": 0.92,
            "L_m": 18.0,
            "paralelos": 1,
            "sistema": "3F",
            "dv_v": 1.1,
            "dv_pct": 0.29,
            "icc_ka": 14.2,
            "estado": "OK",
            "observaciones": "ok",
        }
    ]

    run_id = registrar_ejecucion(datos, ruta_db=ruta_db)
    circuitos = obtener_circuitos(run_id=run_id, ruta_db=ruta_db)
    assert len(circuitos) == 1
    assert circuitos[0]["nombre"] == "C-02"
