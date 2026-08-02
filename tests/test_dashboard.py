import re

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
    """`AppTest.from_file` ejecuta dashboard.py en su propio contexto, aislado
    del proceso de test — no comparte `sys.modules['dashboard']`, así que
    `unittest.mock.patch("dashboard._repo_url_web", ...)` NO tiene efecto sobre
    esta ejecución (verificado empíricamente). Por eso este test verifica el
    comportamiento real contra el remoto real del repo (que sí es GitHub),
    con una regex tolerante al hash exacto en vez de un valor mockeado."""
    at = _app(db_prueba)
    assert not at.exception
    markdowns = " ".join(m.value for m in at.markdown)
    assert re.search(r"\]\(https://github\.com/[\w.-]+/[\w.-]+/commit/[0-9a-f]{7,40}\)", markdowns)


from dashboard import _filtro_fecha


def _df_prueba(ahora: pd.Timestamp) -> pd.DataFrame:
    return pd.DataFrame({
        "run_id": ["a", "b", "c"],
        "timestamp_dt": [ahora - pd.Timedelta(days=1), ahora - pd.Timedelta(days=10), ahora - pd.Timedelta(days=40)],
    })


def test_filtro_fecha_todo_no_filtra():
    ahora = pd.Timestamp("2026-08-01", tz="UTC")
    df = _df_prueba(ahora)
    resultado = _filtro_fecha(df, "Todo", ahora=ahora)
    assert len(resultado) == 3


def test_filtro_fecha_7_dias():
    ahora = pd.Timestamp("2026-08-01", tz="UTC")
    df = _df_prueba(ahora)
    resultado = _filtro_fecha(df, "Últimos 7 días", ahora=ahora)
    assert list(resultado["run_id"]) == ["a"]


def test_filtro_fecha_30_dias():
    ahora = pd.Timestamp("2026-08-01", tz="UTC")
    df = _df_prueba(ahora)
    resultado = _filtro_fecha(df, "Últimos 30 días", ahora=ahora)
    assert list(resultado["run_id"]) == ["a", "b"]


def test_filtro_fecha_dataframe_vacio_no_lanza():
    vacio = pd.DataFrame()
    assert _filtro_fecha(vacio, "Últimos 7 días").empty


def test_filtro_fecha_conserva_filas_con_timestamp_invalido():
    """Una fila con timestamp_dt = NaT (timestamp mal formado en la DB) no debe
    desaparecer silenciosamente al filtrar por rango — no se puede ubicar en
    el tiempo, así que se conserva visible en vez de asumir que queda fuera."""
    ahora = pd.Timestamp("2026-08-01", tz="UTC")
    df = pd.DataFrame({
        "run_id": ["reciente", "invalida", "vieja"],
        "timestamp_dt": [ahora - pd.Timedelta(days=1), pd.NaT, ahora - pd.Timedelta(days=40)],
    })
    resultado = _filtro_fecha(df, "Últimos 7 días", ahora=ahora)
    assert set(resultado["run_id"]) == {"reciente", "invalida"}


def test_filtro_fecha_incluye_borde_exacto():
    """El corte es inclusivo (>=): una fila exactamente en el límite del rango
    debe quedar incluida, no excluida."""
    ahora = pd.Timestamp("2026-08-01", tz="UTC")
    df = pd.DataFrame({
        "run_id": ["borde"],
        "timestamp_dt": [ahora - pd.Timedelta(days=7)],
    })
    resultado = _filtro_fecha(df, "Últimos 7 días", ahora=ahora)
    assert list(resultado["run_id"]) == ["borde"]


def test_filtro_fecha_preset_invalido_falla_ruidosamente():
    ahora = pd.Timestamp("2026-08-01", tz="UTC")
    df = _df_prueba(ahora)
    with pytest.raises(KeyError):
        _filtro_fecha(df, "Últimos 3 años", ahora=ahora)


def test_sidebar_tiene_control_de_rango(db_prueba):
    at = _app(db_prueba)
    assert not at.exception
    assert len(at.sidebar.radio) == 1
    assert at.sidebar.radio[0].options == ["Todo", "Últimos 7 días", "Últimos 30 días"]


from dashboard import _estilo_status
from gui_core.estado import COLORES


def test_estilo_status_ok():
    assert _estilo_status("OK") == f"color: {COLORES['ok']}"


def test_estilo_status_con_fallas():
    assert _estilo_status("CON_FALLAS") == f"color: {COLORES['alerta']}"


def test_estilo_status_error_mismo_color_que_fallas():
    assert _estilo_status("ERROR") == f"color: {COLORES['alerta']}"


def test_estilo_status_advertencias():
    assert _estilo_status("CON_ADVERTENCIAS") == f"color: {COLORES['precaucion']}"


def test_estilo_status_desconocido_sin_estilo():
    assert _estilo_status("ALGO_RARO") == ""
