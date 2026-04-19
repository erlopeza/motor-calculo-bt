"""
Persistencia de ejecuciones del motor en SQLite.
Diseñado con tipos y esquema compatibles con migración a PostgreSQL.
"""

import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone


CREATE_RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id             TEXT PRIMARY KEY,
    project_id         TEXT,
    revision           TEXT,
    timestamp          TEXT,
    commit_hash        TEXT,
    branch             TEXT,
    perfil             TEXT,
    norma              TEXT,
    n_circuitos        INTEGER,
    n_ok               INTEGER,
    n_advertencias     INTEGER,
    n_fallas           INTEGER,
    max_dv_pct         REAL,
    max_icc_ka         REAL,
    status             TEXT,
    ruta_reporte_txt   TEXT,
    ruta_reporte_xlsx  TEXT
)
"""


def _obtener_commit_y_branch():
    commit_hash = None
    branch = None

    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.STDOUT, text=True
        ).strip() or None
    except Exception:
        commit_hash = None

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip() or None
    except Exception:
        branch = None

    return commit_hash, branch


def inicializar_db(ruta_db: str = "motor_bt.db") -> None:
    try:
        with sqlite3.connect(ruta_db) as conn:
            conn.execute(CREATE_RUNS_TABLE_SQL)
            conn.commit()
    except Exception as e:
        print(f"[persistencia] Error inicializando DB: {e}")


def registrar_ejecucion(datos: dict, ruta_db: str = "motor_bt.db") -> str:
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        inicializar_db(ruta_db)
        commit_hash, branch = _obtener_commit_y_branch()

        fila = {
            "run_id": run_id,
            "project_id": datos.get("project_id"),
            "revision": datos.get("revision"),
            "timestamp": timestamp,
            "commit_hash": commit_hash,
            "branch": branch,
            "perfil": datos.get("perfil"),
            "norma": datos.get("norma"),
            "n_circuitos": datos.get("n_circuitos"),
            "n_ok": datos.get("n_ok"),
            "n_advertencias": datos.get("n_advertencias"),
            "n_fallas": datos.get("n_fallas"),
            "max_dv_pct": datos.get("max_dv_pct"),
            "max_icc_ka": datos.get("max_icc_ka"),
            "status": datos.get("status"),
            "ruta_reporte_txt": datos.get("ruta_reporte_txt"),
            "ruta_reporte_xlsx": datos.get("ruta_reporte_xlsx"),
        }

        with sqlite3.connect(ruta_db) as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, project_id, revision, timestamp,
                    commit_hash, branch, perfil, norma,
                    n_circuitos, n_ok, n_advertencias, n_fallas,
                    max_dv_pct, max_icc_ka, status,
                    ruta_reporte_txt, ruta_reporte_xlsx
                )
                VALUES (
                    :run_id, :project_id, :revision, :timestamp,
                    :commit_hash, :branch, :perfil, :norma,
                    :n_circuitos, :n_ok, :n_advertencias, :n_fallas,
                    :max_dv_pct, :max_icc_ka, :status,
                    :ruta_reporte_txt, :ruta_reporte_xlsx
                )
                """,
                fila,
            )
            conn.commit()
    except Exception as e:
        print(f"[persistencia] Error registrando ejecución: {e}")

    return run_id


def obtener_ejecuciones(ruta_db: str = "motor_bt.db") -> list:
    try:
        with sqlite3.connect(ruta_db) as conn:
            conn.row_factory = sqlite3.Row
            filas = conn.execute("SELECT * FROM runs ORDER BY timestamp ASC").fetchall()
            return [dict(fila) for fila in filas]
    except Exception as e:
        print(f"[persistencia] Error obteniendo ejecuciones: {e}")
        return []
