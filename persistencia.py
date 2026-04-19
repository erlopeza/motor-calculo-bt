"""
Persistencia de ejecuciones y eventos tecnicos del motor en SQLite.
"""

import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")


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


def _normalizar_status(status: str):
    if status == "OBSERVACIONES":
        return "CON_ADVERTENCIAS"
    return status


def _columnas_tabla(conn: sqlite3.Connection, tabla: str) -> set:
    try:
        rows = conn.execute(f"PRAGMA table_info({tabla})").fetchall()
        return {row[1] for row in rows}
    except Exception:
        return set()


def inicializar_db(ruta_db: str = "motor_bt.db") -> None:
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        with sqlite3.connect(ruta_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(schema_sql)
            columnas_runs = _columnas_tabla(conn, "runs")
            # Compatibilidad con DBs antiguas que no tienen esta columna.
            if "runs" in {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
                if "observaciones" not in columnas_runs:
                    conn.execute("ALTER TABLE runs ADD COLUMN observaciones TEXT")

            # Migracion run_reports para admitir DOCX/PDF en DBs antiguas.
            run_reports_sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='run_reports'"
            ).fetchone()
            if run_reports_sql and run_reports_sql[0]:
                sql_text = run_reports_sql[0].upper()
                if "DOCX" not in sql_text or "PDF" not in sql_text:
                    conn.execute("ALTER TABLE run_reports RENAME TO run_reports_old")
                    conn.execute(
                        """
                        CREATE TABLE run_reports (
                            report_id TEXT PRIMARY KEY,
                            run_id TEXT NOT NULL,
                            report_type TEXT NOT NULL CHECK (report_type IN ('TXT', 'XLSX', 'DOCX', 'PDF')),
                            file_path TEXT NOT NULL,
                            created_at TEXT NOT NULL DEFAULT (datetime('now')),
                            FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
                            UNIQUE (run_id, report_type)
                        )
                        """
                    )
                    conn.execute(
                        """
                        INSERT INTO run_reports (report_id, run_id, report_type, file_path, created_at)
                        SELECT report_id, run_id, report_type, file_path, created_at
                        FROM run_reports_old
                        """
                    )
                    conn.execute("DROP TABLE run_reports_old")
                    conn.execute(
                        "CREATE INDEX IF NOT EXISTS idx_run_reports_run_id ON run_reports(run_id)"
                    )
                    conn.execute(
                        "CREATE INDEX IF NOT EXISTS idx_run_reports_report_type ON run_reports(report_type)"
                    )
            conn.commit()
    except Exception as e:
        print(f"[persistencia] Error inicializando DB: {e}")


def registrar_ejecucion(datos: dict, ruta_db: str = "motor_bt.db") -> str:
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        inicializar_db(ruta_db)
        commit_hash, branch = _obtener_commit_y_branch()

        fila_run = {
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
            "status": _normalizar_status(datos.get("status")),
            "observaciones": datos.get("observaciones"),
        }

        with sqlite3.connect(ruta_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, project_id, revision, timestamp,
                    commit_hash, branch, perfil, norma,
                    n_circuitos, n_ok, n_advertencias, n_fallas,
                    max_dv_pct, max_icc_ka, status, observaciones
                )
                VALUES (
                    :run_id, :project_id, :revision, :timestamp,
                    :commit_hash, :branch, :perfil, :norma,
                    :n_circuitos, :n_ok, :n_advertencias, :n_fallas,
                    :max_dv_pct, :max_icc_ka, :status, :observaciones
                )
                """,
                fila_run,
            )

            reportes = [
                ("TXT", datos.get("ruta_reporte_txt")),
                ("XLSX", datos.get("ruta_reporte_xlsx")),
                ("DOCX", datos.get("ruta_reporte_docx")),
                ("PDF", datos.get("ruta_reporte_pdf")),
            ]
            for report_type, file_path in reportes:
                if file_path:
                    try:
                        conn.execute(
                            """
                            INSERT INTO run_reports (report_id, run_id, report_type, file_path)
                            VALUES (?, ?, ?, ?)
                            """,
                            (str(uuid.uuid4()), run_id, report_type, file_path),
                        )
                    except Exception as e:
                        print(f"[persistencia] Error registrando reporte {report_type}: {e}")

            conn.commit()
            circuitos = datos.get("circuitos")
            if isinstance(circuitos, list):
                registrar_circuitos(run_id=run_id, circuitos=circuitos, ruta_db=ruta_db)
    except Exception as e:
        print(f"[persistencia] Error registrando ejecucion: {e}")

    return run_id


def registrar_evento(run_id: str, datos_evento: dict, ruta_db: str = "motor_bt.db") -> str:
    event_id = str(uuid.uuid4())
    timestamp = datos_evento.get("timestamp") or datetime.now(timezone.utc).isoformat()

    try:
        inicializar_db(ruta_db)

        with sqlite3.connect(ruta_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                INSERT INTO technical_events (
                    event_id, run_id, project_id, revision, timestamp,
                    event_type, title, estado, disciplina,
                    wbs_id, item_id, frente_id, description, observaciones
                )
                VALUES (
                    :event_id, :run_id, :project_id, :revision, :timestamp,
                    :event_type, :title, :estado, :disciplina,
                    :wbs_id, :item_id, :frente_id, :description, :observaciones
                )
                """,
                {
                    "event_id": event_id,
                    "run_id": run_id,
                    "project_id": datos_evento.get("project_id"),
                    "revision": datos_evento.get("revision"),
                    "timestamp": timestamp,
                    "event_type": datos_evento.get("event_type", "CALCULO_BT"),
                    "title": datos_evento.get("title", f"Calculo BT - {datos_evento.get('project_id') or 'N/A'}"),
                    "estado": datos_evento.get("estado", "EN_REVISION"),
                    "disciplina": datos_evento.get("disciplina", "ELC"),
                    "wbs_id": datos_evento.get("WBS_ID"),
                    "item_id": datos_evento.get("ITEM_ID"),
                    "frente_id": None,
                    "description": datos_evento.get("description"),
                    "observaciones": datos_evento.get("observaciones"),
                },
            )
            conn.commit()
        return event_id
    except Exception as e:
        print(f"[persistencia] Error registrando evento: {e}")
        return ""


def obtener_ejecuciones(ruta_db: str = "motor_bt.db") -> list:
    try:
        inicializar_db(ruta_db)
        with sqlite3.connect(ruta_db) as conn:
            conn.row_factory = sqlite3.Row
            columnas_runs = _columnas_tabla(conn, "runs")
            expr_obs = "r.observaciones" if "observaciones" in columnas_runs else "NULL AS observaciones"
            expr_txt = "MAX(CASE WHEN rr.report_type = 'TXT' THEN rr.file_path END)"
            expr_xlsx = "MAX(CASE WHEN rr.report_type = 'XLSX' THEN rr.file_path END)"
            if "ruta_reporte_txt" in columnas_runs:
                expr_txt = f"COALESCE({expr_txt}, r.ruta_reporte_txt)"
            if "ruta_reporte_xlsx" in columnas_runs:
                expr_xlsx = f"COALESCE({expr_xlsx}, r.ruta_reporte_xlsx)"

            filas = conn.execute(
                f"""
                SELECT
                    r.run_id,
                    r.project_id,
                    r.revision,
                    r.timestamp,
                    r.commit_hash,
                    r.branch,
                    r.perfil,
                    r.norma,
                    r.n_circuitos,
                    r.n_ok,
                    r.n_advertencias,
                    r.n_fallas,
                    r.max_dv_pct,
                    r.max_icc_ka,
                    r.status,
                    {expr_obs},
                    {expr_txt} AS ruta_reporte_txt,
                    {expr_xlsx} AS ruta_reporte_xlsx,
                    MAX(CASE WHEN rr.report_type = 'DOCX' THEN rr.file_path END) AS ruta_reporte_docx,
                    MAX(CASE WHEN rr.report_type = 'PDF' THEN rr.file_path END) AS ruta_reporte_pdf
                FROM runs r
                LEFT JOIN run_reports rr ON rr.run_id = r.run_id
                GROUP BY
                    r.run_id,
                    r.project_id,
                    r.revision,
                    r.timestamp,
                    r.commit_hash,
                    r.branch,
                    r.perfil,
                    r.norma,
                    r.n_circuitos,
                    r.n_ok,
                    r.n_advertencias,
                    r.n_fallas,
                    r.max_dv_pct,
                    r.max_icc_ka,
                    r.status
                    {", r.observaciones" if "observaciones" in columnas_runs else ""}
                    {", r.ruta_reporte_txt" if "ruta_reporte_txt" in columnas_runs else ""}
                    {", r.ruta_reporte_xlsx" if "ruta_reporte_xlsx" in columnas_runs else ""}
                ORDER BY r.timestamp ASC
                """
            ).fetchall()
            return [dict(fila) for fila in filas]
    except Exception as e:
        print(f"[persistencia] Error obteniendo ejecuciones: {e}")
        return []


def obtener_eventos(project_id: str = None, ruta_db: str = "motor_bt.db") -> list:
    try:
        inicializar_db(ruta_db)
        with sqlite3.connect(ruta_db) as conn:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT
                    event_id,
                    run_id,
                    project_id,
                    revision,
                    timestamp,
                    event_type,
                    title,
                    estado,
                    disciplina,
                    wbs_id AS WBS_ID,
                    item_id AS ITEM_ID,
                    frente_id,
                    description,
                    observaciones
                FROM technical_events
            """
            params = []
            if project_id is not None:
                sql += " WHERE project_id = ?"
                params.append(project_id)
            sql += " ORDER BY timestamp ASC"

            filas = conn.execute(sql, params).fetchall()
            return [dict(fila) for fila in filas]
    except Exception as e:
        print(f"[persistencia] Error obteniendo eventos: {e}")
        return []


def registrar_circuitos(
    run_id: str,
    circuitos: list,
    ruta_db: str = "motor_bt.db"
) -> int:
    insertados = 0
    try:
        if not isinstance(circuitos, list):
            return 0
        inicializar_db(ruta_db)
        with sqlite3.connect(ruta_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            for circuito in circuitos:
                conn.execute(
                    """
                    INSERT INTO run_circuits (
                        circuit_id, run_id, nombre, conductor, norma, S_mm2,
                        I_diseno, I_max, cos_phi, L_m, paralelos, sistema,
                        dv_v, dv_pct, icc_ka, estado, observaciones
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        run_id,
                        circuito.get("nombre"),
                        circuito.get("conductor"),
                        circuito.get("norma"),
                        circuito.get("S_mm2"),
                        circuito.get("I_diseno"),
                        circuito.get("I_max"),
                        circuito.get("cos_phi"),
                        circuito.get("L_m"),
                        circuito.get("paralelos"),
                        circuito.get("sistema"),
                        circuito.get("dv_v"),
                        circuito.get("dv_pct"),
                        circuito.get("icc_ka"),
                        circuito.get("estado"),
                        circuito.get("observaciones"),
                    ),
                )
                insertados += 1
            conn.commit()
    except Exception as e:
        print(f"[persistencia] Error registrando circuitos: {e}")
    return insertados


def obtener_circuitos(
    run_id: str,
    ruta_db: str = "motor_bt.db"
) -> list:
    try:
        inicializar_db(ruta_db)
        with sqlite3.connect(ruta_db) as conn:
            conn.row_factory = sqlite3.Row
            filas = conn.execute(
                """
                SELECT
                    circuit_id,
                    run_id,
                    nombre,
                    conductor,
                    norma,
                    S_mm2,
                    I_diseno,
                    I_max,
                    cos_phi,
                    L_m,
                    paralelos,
                    sistema,
                    dv_v,
                    dv_pct,
                    icc_ka,
                    estado,
                    observaciones
                FROM run_circuits
                WHERE run_id = ?
                ORDER BY nombre ASC
                """,
                (run_id,),
            ).fetchall()
            return [dict(fila) for fila in filas]
    except Exception as e:
        print(f"[persistencia] Error obteniendo circuitos: {e}")
        return []
