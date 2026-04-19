import sqlite3
import uuid
from pathlib import Path

from persistencia import inicializar_db, registrar_ejecucion, obtener_ejecuciones


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
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='runs'"
        ).fetchone()
    assert row is not None
    assert row[0] == "runs"


def test_registrar_ejecucion():
    ruta_db = _ruta_db_local("registrar")
    run_id = registrar_ejecucion(_datos_base(), ruta_db=ruta_db)

    ejecuciones = obtener_ejecuciones(ruta_db=ruta_db)
    assert len(ejecuciones) == 1
    assert ejecuciones[0]["run_id"] == run_id
    assert ejecuciones[0]["project_id"] == "LEO-ARICA"


def test_fallo_silencioso():
    # Directorio intermedio no existente: SQLite no puede crear DB ahí.
    ruta_db_invalida = str(
        Path(__file__).resolve().parent / ".tmp_persistencia_tests" / "inexistente" / "test_motor_bt.db"
    )
    try:
        registrar_ejecucion(_datos_base(), ruta_db=ruta_db_invalida)
    except Exception as e:
        raise AssertionError(f"No debía lanzar excepción: {e}")


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
