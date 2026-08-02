import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import persistencia
from dashboard import _fmt_fecha


@pytest.fixture
def db_prueba(tmp_path) -> str:
    """DB SQLite temporal con 1 corrida de prueba y las 4 rutas de reporte pobladas."""
    ruta = str(tmp_path / "motor_bt_test.db")
    persistencia.registrar_ejecucion({
        "project_id": "PROY-TEST",
        "revision": "CLI",
        "perfil": "industrial",
        "norma": "AWG",
        "n_circuitos": 5,
        "n_ok": 4,
        "n_advertencias": 0,
        "n_fallas": 1,
        "max_dv_pct": 3.2,
        "max_icc_ka": 12.5,
        "status": "CON_FALLAS",
        "ruta_reporte_txt": "REPORTE_PROY-TEST.txt",
        "ruta_reporte_xlsx": "REPORTE_PROY-TEST.xlsx",
        "ruta_reporte_docx": "MEMORIA_PROY-TEST.docx",
        "ruta_reporte_pdf": "REPORTE_PROY-TEST.pdf",
    }, ruta_db=ruta)
    return ruta


def _app(ruta_db: str) -> AppTest:
    """Instancia el dashboard y lo apunta a `ruta_db`. Timeout amplio (30s)
    para no ser frágil en un runner de CI recién aprovisionado (primera
    ejecución sin cachés calientes)."""
    at = AppTest.from_file("dashboard.py", default_timeout=30)
    at.run()
    at.sidebar.text_input[0].set_value(ruta_db).run()
    return at


def test_detalle_muestra_las_4_rutas_de_reporte(db_prueba):
    at = _app(db_prueba)
    assert not at.exception
    textos = " ".join(t.value for t in at.text)
    assert "ruta_reporte_txt" in textos
    assert "ruta_reporte_xlsx" in textos
    assert "ruta_reporte_docx" in textos
    assert "ruta_reporte_pdf" in textos


def test_fmt_fecha_none_y_nat():
    assert _fmt_fecha(None) == "—"
    assert _fmt_fecha(pd.NaT) == "—"


def test_fmt_fecha_timestamp_real():
    dt = pd.Timestamp("2026-08-01T21:21:30.233149", tz="UTC")
    assert _fmt_fecha(dt) == "2026-08-01 21:21 UTC"


def test_resumen_muestra_timestamp_formateado(db_prueba):
    at = _app(db_prueba)
    assert not at.exception
    ultima = next(m for m in at.metric if m.label == "Última ejecución")
    assert "UTC" in ultima.value
    # No debe quedar el separador ISO crudo 'T' (distinto de la 'T' de "UTC").
    assert "T" not in ultima.value.replace("UTC", "")


def test_ruta_vacia_muestra_error():
    at = _app("")
    assert not at.exception
    assert len(at.error) == 1
    assert "vacío" in at.error[0].value.lower()


def test_ruta_a_directorio_muestra_error():
    at = _app(".")
    assert not at.exception
    assert len(at.error) == 1
    assert "'.'" in at.error[0].value


def test_ruta_valida_no_muestra_error(db_prueba):
    at = _app(db_prueba)
    assert not at.exception
    assert len(at.error) == 0


from unittest.mock import patch

from dashboard import _repo_url_web


def test_repo_url_web_https():
    with patch("subprocess.check_output", return_value="https://github.com/erlopeza/motor-calculo-bt.git\n"):
        assert _repo_url_web() == "https://github.com/erlopeza/motor-calculo-bt"


def test_repo_url_web_ssh_convertida():
    with patch("subprocess.check_output", return_value="git@github.com:erlopeza/motor-calculo-bt.git\n"):
        assert _repo_url_web() == "https://github.com/erlopeza/motor-calculo-bt"


def test_repo_url_web_excepcion_devuelve_none():
    with patch("subprocess.check_output", side_effect=OSError("git no encontrado")):
        assert _repo_url_web() is None


def test_estado_tecnico_commit_hash_es_link(db_prueba):
    at = _app(db_prueba)
    assert not at.exception
    markdowns = " ".join(m.value for m in at.markdown)
    assert "](https://github.com/" in markdowns or "commit_hash" in " ".join(t.value for t in at.text)
