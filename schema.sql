PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    project_id TEXT,
    revision TEXT,
    timestamp TEXT NOT NULL,
    commit_hash TEXT,
    branch TEXT,
    perfil TEXT,
    norma TEXT,
    n_circuitos INTEGER CHECK (n_circuitos IS NULL OR n_circuitos >= 0),
    n_ok INTEGER CHECK (n_ok IS NULL OR n_ok >= 0),
    n_advertencias INTEGER CHECK (n_advertencias IS NULL OR n_advertencias >= 0),
    n_fallas INTEGER CHECK (n_fallas IS NULL OR n_fallas >= 0),
    max_dv_pct REAL CHECK (max_dv_pct IS NULL OR max_dv_pct >= 0),
    max_icc_ka REAL CHECK (max_icc_ka IS NULL OR max_icc_ka >= 0),
    status TEXT CHECK (status IN ('OK', 'CON_FALLAS', 'CON_ADVERTENCIAS', 'ERROR')),
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS run_reports (
    report_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    report_type TEXT NOT NULL CHECK (report_type IN ('TXT', 'XLSX', 'DOCX', 'PDF')),
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    UNIQUE (run_id, report_type)
);

CREATE TABLE IF NOT EXISTS technical_events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    project_id TEXT,
    revision TEXT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('CALCULO_BT', 'ALERTA', 'REPORTE')),
    title TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('COMPLETADO', 'EN_REVISION', 'BLOQUEADO')),
    disciplina TEXT,
    wbs_id TEXT,
    item_id TEXT,
    frente_id TEXT,
    description TEXT,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    UNIQUE (run_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_project_id ON runs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs(timestamp);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);

CREATE INDEX IF NOT EXISTS idx_run_reports_run_id ON run_reports(run_id);
CREATE INDEX IF NOT EXISTS idx_run_reports_report_type ON run_reports(report_type);

CREATE INDEX IF NOT EXISTS idx_technical_events_project_id ON technical_events(project_id);
CREATE INDEX IF NOT EXISTS idx_technical_events_timestamp ON technical_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_technical_events_event_type ON technical_events(event_type);

CREATE TABLE IF NOT EXISTS run_circuits (
    circuit_id      TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    nombre          TEXT NOT NULL,
    conductor       TEXT,
    norma           TEXT,
    S_mm2           REAL,
    I_diseno        REAL,
    I_max           REAL,
    cos_phi         REAL,
    L_m             REAL,
    paralelos       INTEGER,
    sistema         TEXT,
    dv_v            REAL,
    dv_pct          REAL,
    icc_ka          REAL,
    estado          TEXT,
    observaciones   TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_run_circuits_run_id
    ON run_circuits(run_id);
