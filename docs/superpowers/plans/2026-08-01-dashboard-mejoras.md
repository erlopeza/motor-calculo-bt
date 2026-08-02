# Dashboard: correcciones (P0) + filtro de fecha y paleta (P1) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir 4 huecos de bajo riesgo en `dashboard.py` (rutas DOCX/PDF ocultas, commit_hash sin link, timestamp crudo, ruta de DB inválida mal detectada) y añadir 2 mejoras de diseño (filtro de rango de fecha, paleta alineada con Tokyo Night), sin tocar `persistencia.py`, `gui_core/`, `gui/` ni el motor.

**Architecture:** Todos los cambios de código viven en `dashboard.py` (helpers nuevos + modificaciones puntuales en `main()`). Un archivo nuevo `.streamlit/config.toml` aplica el tema base sin código. `pyproject.toml`/`requirements.txt` ganan pandas/streamlit como dependencias declaradas (extra `dashboard`). Tests nuevos en `tests/test_dashboard.py`, dos niveles: unit tests puros sobre los helpers + smoke con `streamlit.testing.v1.AppTest` (verificado disponible y funcional en Streamlit 1.56.0 instalado).

**Tech Stack:** Python 3.13, streamlit 1.56, pandas 2.3, pytest. Sin dependencias nuevas más allá de declarar las dos que ya se usaban implícitamente.

**Spec:** `docs/superpowers/specs/2026-08-01-dashboard-mejoras-design.md`

**Contexto verificado antes de escribir este plan (no re-verificar):**
- `streamlit.testing.v1.AppTest` funciona contra `dashboard.py` tal cual está hoy: `AppTest.from_file("dashboard.py", default_timeout=10).run()` no marca ninguna excepción (`at.exception` vacío). `at.sidebar.text_input[0].set_value("...").run()` cambia la ruta de DB y vuelve a ejecutar. `at.error`/`at.info` son listas iterables con `.value` como string.
- Con una ruta inexistente, HOY el dashboard muestra `at.info[0].value == "sin ejecuciones registradas"` (no `at.error`) — es exactamente el comportamiento que la Tarea 4 de este plan corrige.
- Hay un warning de PyArrow ya presente HOY en la tabla "Campos del registro" (tab Detalle): la columna `valor` mezcla strings y enteros (viene de `_fmt_val`, que devuelve el valor crudo sin convertir a string cuando no es None/NaN/vacío) y Streamlit lo resuelve solo internamente ("Applying automatic fixes for column types"), sin crashear (`at.exception` sigue vacío). **No se toca en este plan** — es preexistente, no forma parte de los P0/P1 aprobados, y no rompe nada.
- Consola de este entorno es cp1252 — si algún test imprime directamente un carácter como "Δ" a stdout (no vía `assert`, sino con `print()`), puede fallar por el mismo motivo que ya se corrigió en `main.py`. Los tests de este plan usan `assert`, no `print()`, así que no aplica — se deja anotado por si el ejecutor depura con prints sueltos.

---

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `pyproject.toml` | + extra `dashboard` (pandas, streamlit) | Modificar |
| `requirements.txt` | + pandas/streamlit pineados | Modificar |
| `dashboard.py` | Todos los helpers y wiring de P0+P1 | Modificar |
| `.streamlit/config.toml` | Tema Tokyo Night base | Crear |
| `tests/test_dashboard.py` | Unit tests + smoke AppTest | Crear |

Reglas: `gui_core/estado.COLORES` es la fuente única de verdad de color (se importa, no se duplica en Python; el TOML sí duplica los 4 hex base porque no puede importar Python, y queda comentado como tal). `dashboard.py` no importa `gui/` ni depende de tkinter.

---

## Task 1: Declarar dependencias (pandas, streamlit)

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`

- [ ] **Step 1: Añadir el extra `dashboard` a `pyproject.toml`**

Localizar el bloque `[project.optional-dependencies]` (contiene los extras `rag`, `dev`, `build`) y añadir un extra nuevo `dashboard` inmediatamente después de `rag` y antes de `dev`:

```toml
dashboard = [
    "pandas>=2.3",
    "streamlit>=1.56",
]
```

- [ ] **Step 2: Añadir pandas/streamlit a `requirements.txt`**

Añadir estas dos líneas al final del archivo (después de `numpy>=1.26`):

```
pandas==2.3.2
streamlit==1.56.0
```

- [ ] **Step 3: Verificar instalación**

Run: `pip install -e ".[dashboard]" --dry-run 2>&1 | tail -5` (o, si `--dry-run` no está disponible en el pip instalado, simplemente `python -c "import pandas, streamlit; print('ok')"` ya que ambos están instalados en este entorno de desarrollo)
Expected: `ok` (o instalación sin errores de resolución de dependencias).

- [ ] **Step 4: Commit**

```bash
git checkout -b feat/dashboard-mejoras
git add pyproject.toml requirements.txt
git commit -m "build: declarar pandas/streamlit como dependencias reales de dashboard.py

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: P0-1 — Mostrar rutas DOCX/PDF en el detalle de ejecución

**Files:**
- Modify: `dashboard.py` (sección "Rutas de reporte" dentro de `tab_detalle`)
- Modify: `.github/workflows/ci.yml` (instalar pandas/streamlit para que la colección de pytest no falle en CI)
- Test: `tests/test_dashboard.py` (se crea aquí con el primer uso, incluye el fixture `db_prueba` reutilizado por TODAS las tareas siguientes)

**Corrección importante (hallazgo de revisión de calidad sobre un borrador anterior de este plan):** los tests NO deben apuntar a `motor_bt.db` (el archivo de trabajo real del desarrollador — no está versionado, `.gitignore` lo excluye, y su contenido es mutable). Cada test usa una DB SQLite temporal (`tmp_path` de pytest) sembrada con `persistencia.registrar_ejecucion(...)`, que ya sabe escribir las 4 rutas de reporte. Esto es determinista y reproducible en cualquier máquina/CI.

- [ ] **Step 1: Escribir el test (smoke AppTest) + fixture reutilizable**

Crear `tests/test_dashboard.py`:

```python
import pytest
from streamlit.testing.v1 import AppTest

import persistencia


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
```

- [ ] **Step 2: Correr → FAIL** (faltan `ruta_reporte_docx`/`ruta_reporte_pdf` en el texto renderizado)

Run: `python -m pytest tests/test_dashboard.py::test_detalle_muestra_las_4_rutas_de_reporte -v`
Expected: FAIL — `assert "ruta_reporte_docx" in textos` no se cumple.

- [ ] **Step 3: Implementar — añadir las 2 líneas faltantes**

En `dashboard.py`, dentro de `with tab_detalle:`, localizar:

```python
        st.subheader("Rutas de reporte")
        st.text(f"ruta_reporte_txt: {_fmt_val(fila.get('ruta_reporte_txt'))}")
        st.text(f"ruta_reporte_xlsx: {_fmt_val(fila.get('ruta_reporte_xlsx'))}")
```

Reemplazar por:

```python
        st.subheader("Rutas de reporte")
        st.text(f"ruta_reporte_txt: {_fmt_val(fila.get('ruta_reporte_txt'))}")
        st.text(f"ruta_reporte_xlsx: {_fmt_val(fila.get('ruta_reporte_xlsx'))}")
        st.text(f"ruta_reporte_docx: {_fmt_val(fila.get('ruta_reporte_docx'))}")
        st.text(f"ruta_reporte_pdf: {_fmt_val(fila.get('ruta_reporte_pdf'))}")
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_dashboard.py -v`
Expected: 1 passed.

- [ ] **Step 5: Arreglar CI — instalar pandas/streamlit (si no, la colección de pytest falla en el próximo push)**

En `.github/workflows/ci.yml`, localizar el paso `Install core + dev dependencies`:

```yaml
      - name: Install core + dev dependencies
        run: |
          python -m pip install --upgrade pip
          pip install "openpyxl>=3.1" "python-docx>=1.2" "reportlab>=4.4" \
                      "matplotlib>=3.8" "numpy>=1.26" "pytest>=9.0" "pytest-cov>=4.0" \
                      "hypothesis>=6.0"
```

Reemplazar por (se añaden `pandas` y `streamlit` a la misma línea de instalación):

```yaml
      - name: Install core + dev dependencies
        run: |
          python -m pip install --upgrade pip
          pip install "openpyxl>=3.1" "python-docx>=1.2" "reportlab>=4.4" \
                      "matplotlib>=3.8" "numpy>=1.26" "pytest>=9.0" "pytest-cov>=4.0" \
                      "hypothesis>=6.0" "pandas>=2.3" "streamlit>=1.56"
```

- [ ] **Step 6: Commit**

```bash
git add dashboard.py tests/test_dashboard.py .github/workflows/ci.yml
git commit -m "feat(dashboard): mostrar rutas DOCX/PDF en el detalle de ejecución

Añade fixture db_prueba (DB SQLite temporal vía persistencia.registrar_ejecucion)
para que los tests de dashboard.py no dependan del archivo motor_bt.db real
del desarrollador (no versionado, mutable). Instala pandas/streamlit en CI —
tests/test_dashboard.py los importa y CI no los tenía declarados.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: P0-3 — Timestamp legible en "Última ejecución"

**Files:**
- Modify: `dashboard.py` (nuevo helper `_fmt_fecha` + uso en `tab_resumen`)
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: Escribir tests (unit + smoke)**

Añadir a `tests/test_dashboard.py`:

```python
import pandas as pd

from dashboard import _fmt_fecha


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
    assert "T" not in ultima.value  # no debe quedar el ISO crudo con separador 'T'
    assert "UTC" in ultima.value
```

- [ ] **Step 2: Correr → FAIL** (`ImportError: cannot import name '_fmt_fecha'`)

Run: `python -m pytest tests/test_dashboard.py -v`

- [ ] **Step 3: Implementar el helper**

En `dashboard.py`, añadir inmediatamente después de la función `_fmt_val` (antes de `_tabla_presentacion`):

```python
def _fmt_fecha(dt) -> str:
    """Formatea un datetime (o None/NaT) a 'YYYY-MM-DD HH:MM UTC'; '—' si no hay valor."""
    if dt is None or pd.isna(dt):
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M UTC")
```

- [ ] **Step 4: Usar el helper en `tab_resumen`**

Localizar, dentro de `with tab_resumen:`:

```python
        total_runs = len(df)
        ultima_ejecucion = _fmt_val(df.iloc[0].get("timestamp"))
```

Reemplazar la segunda línea por:

```python
        total_runs = len(df)
        ultima_ejecucion = _fmt_fecha(df.iloc[0].get("timestamp_dt"))
```

(la línea `c2.metric("Última ejecución", str(ultima_ejecucion))` más abajo no cambia — sigue usando la variable `ultima_ejecucion`, que ahora ya viene formateada).

- [ ] **Step 5: Correr → PASS**

Run: `python -m pytest tests/test_dashboard.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "feat(dashboard): timestamp legible en 'Última ejecución' (_fmt_fecha)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: P0-4 — Validar ruta de DB (archivo real, no directorio ni vacía)

**Files:**
- Modify: `dashboard.py` (import `Path` + validación al inicio de `main()`)
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: Escribir tests (smoke AppTest, 3 casos)**

Añadir a `tests/test_dashboard.py`:

```python
def test_ruta_vacia_muestra_error():
    at = _app("")
    assert not at.exception
    assert len(at.error) == 1
    assert "vacío" in at.error[0].value.lower()


def test_ruta_a_directorio_muestra_error():
    at = _app(".")
    assert not at.exception
    assert len(at.error) == 1
    assert "." in at.error[0].value


def test_ruta_valida_no_muestra_error(db_prueba):
    at = _app(db_prueba)
    assert not at.exception
    assert len(at.error) == 0
```

- [ ] **Step 2: Correr → FAIL** (con ruta vacía o `.`, hoy se muestra `st.info("sin ejecuciones registradas")`, no `st.error`)

Run: `python -m pytest tests/test_dashboard.py -v`
Expected: `test_ruta_vacia_muestra_error` y `test_ruta_a_directorio_muestra_error` fallan con `assert len(at.error) == 1` (hoy es 0).

- [ ] **Step 3: Implementar la validación**

Añadir el import al inicio de `dashboard.py` (junto a los imports existentes):

```python
from pathlib import Path
```

Localizar en `main()`:

```python
    ruta_db = st.sidebar.text_input("Ruta DB", value="motor_bt.db")
    df = _normalizar_dataframe(ruta_db=ruta_db)

    if df.empty:
        st.info("sin ejecuciones registradas")
        return
```

Reemplazar por:

```python
    ruta_db = st.sidebar.text_input("Ruta DB", value="motor_bt.db").strip()
    if not ruta_db or not Path(ruta_db).is_file():
        st.error(f"'{ruta_db or '(vacío)'}' no es un archivo válido.")
        return

    df = _normalizar_dataframe(ruta_db=ruta_db)

    if df.empty:
        st.info("sin ejecuciones registradas")
        return
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_dashboard.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "fix(dashboard): validar ruta de DB con is_file(); distinguir de DB vacía real

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: P0-2 — `commit_hash` como link clickeable

**Files:**
- Modify: `dashboard.py` (nuevo helper `_repo_url_web` + uso en `tab_estado`)
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: Escribir tests (unit con mock + smoke)**

Añadir a `tests/test_dashboard.py`:

```python
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
```

Nota sobre el último test: si `_repo_url_web()` no logra resolver una URL en el entorno de CI (por ejemplo, checkout sin `.git` o sin remoto configurado), el assert cae al `or` y verifica que al menos el texto plano de `commit_hash` sigue presente — cubre la degradación segura sin volver el test frágil ante el entorno de ejecución.

- [ ] **Step 2: Correr → FAIL** (`ImportError: cannot import name '_repo_url_web'`)

Run: `python -m pytest tests/test_dashboard.py -v`

- [ ] **Step 3: Implementar el helper**

Añadir a `dashboard.py`, después de `_fmt_fecha`:

```python
def _repo_url_web() -> str | None:
    """Resuelve la URL web del repo desde 'git remote get-url origin'.
    Devuelve None ante cualquier fallo (sin git, sin remoto, etc.) — nunca crashea."""
    try:
        import subprocess
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], text=True, timeout=2
        ).strip()
        if url.endswith(".git"):
            url = url[:-4]
        if url.startswith("git@github.com:"):
            url = "https://github.com/" + url[len("git@github.com:"):]
        return url
    except Exception:
        return None
```

- [ ] **Step 4: Usar el helper en `tab_estado`**

Localizar:

```python
        st.text(f"commit_hash: {_fmt_val(ultimo.get('commit_hash'))}")
        st.text(f"branch: {_fmt_val(ultimo.get('branch'))}")
```

Reemplazar por:

```python
        hash_commit = _fmt_val(ultimo.get("commit_hash"))
        url_repo = _repo_url_web()
        if url_repo and hash_commit != "—":
            st.markdown(f"commit_hash: [{hash_commit}]({url_repo}/commit/{hash_commit})")
        else:
            st.text(f"commit_hash: {hash_commit}")
        st.text(f"branch: {_fmt_val(ultimo.get('branch'))}")
```

- [ ] **Step 5: Correr → PASS**

Run: `python -m pytest tests/test_dashboard.py -v`
Expected: 11 passed.

- [ ] **Step 6: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "feat(dashboard): commit_hash como link clickeable al repo (_repo_url_web)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: P1a — Filtro de rango de fecha

**Files:**
- Modify: `dashboard.py` (nuevo helper `_filtro_fecha` + control en sidebar + wiring en `main()`)
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: Escribir tests (unit con reloj inyectado + smoke)**

Añadir a `tests/test_dashboard.py`:

```python
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


def test_sidebar_tiene_control_de_rango(db_prueba):
    at = _app(db_prueba)
    assert not at.exception
    assert len(at.sidebar.radio) == 1
    assert at.sidebar.radio[0].options == ["Todo", "Últimos 7 días", "Últimos 30 días"]
```

- [ ] **Step 2: Correr → FAIL** (`ImportError: cannot import name '_filtro_fecha'`)

Run: `python -m pytest tests/test_dashboard.py -v`

- [ ] **Step 3: Implementar el helper**

Añadir a `dashboard.py`, después de `_repo_url_web`:

```python
def _filtro_fecha(df: pd.DataFrame, preset: str, ahora: pd.Timestamp | None = None) -> pd.DataFrame:
    """preset in {'Todo', 'Últimos 7 días', 'Últimos 30 días'}.

    `ahora` es inyectable para que los tests no dependan de pd.Timestamp.now()
    real. En producción se omite y usa el reloj real.
    """
    if preset == "Todo" or df.empty:
        return df
    ahora = ahora if ahora is not None else pd.Timestamp.now(tz="UTC")
    dias = 7 if preset == "Últimos 7 días" else 30
    corte = ahora - pd.Timedelta(days=dias)
    return df[df["timestamp_dt"] >= corte]
```

- [ ] **Step 4: Wiring en `main()`**

Localizar (ya modificado por la Tarea 4):

```python
    ruta_db = st.sidebar.text_input("Ruta DB", value="motor_bt.db").strip()
    if not ruta_db or not Path(ruta_db).is_file():
        st.error(f"'{ruta_db or '(vacío)'}' no es un archivo válido.")
        return

    df = _normalizar_dataframe(ruta_db=ruta_db)

    if df.empty:
        st.info("sin ejecuciones registradas")
        return
```

Reemplazar por:

```python
    ruta_db = st.sidebar.text_input("Ruta DB", value="motor_bt.db").strip()
    if not ruta_db or not Path(ruta_db).is_file():
        st.error(f"'{ruta_db or '(vacío)'}' no es un archivo válido.")
        return

    df = _normalizar_dataframe(ruta_db=ruta_db)

    if df.empty:
        st.info("sin ejecuciones registradas")
        return

    preset = st.sidebar.radio("Rango", ["Todo", "Últimos 7 días", "Últimos 30 días"], index=0)
    df = _filtro_fecha(df, preset)

    if df.empty:
        st.info("sin ejecuciones registradas")
        return
```

- [ ] **Step 5: Correr → PASS**

Run: `python -m pytest tests/test_dashboard.py -v`
Expected: 16 passed.

- [ ] **Step 6: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "feat(dashboard): filtro de rango de fecha (Todo/7 días/30 días)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: P1b — Paleta Tokyo Night (tema base + color de estado en tablas)

**Files:**
- Create: `.streamlit/config.toml`
- Modify: `dashboard.py` (import `COLORES`, nuevo helper `_estilo_status`, Styler en 2 tablas)
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: Escribir tests (unit)**

Añadir a `tests/test_dashboard.py`:

```python
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
```

- [ ] **Step 2: Correr → FAIL** (`ImportError: cannot import name '_estilo_status'`)

Run: `python -m pytest tests/test_dashboard.py -v`

- [ ] **Step 3: Crear `.streamlit/config.toml`**

```toml
# Colores tomados de gui_core.estado.COLORES — mantener sincronizado si esa paleta cambia.
# TOML no puede importar Python, así que estos valores están duplicados intencionalmente.
[theme]
base = "dark"
primaryColor = "#7aa2f7"
backgroundColor = "#1a1b26"
secondaryBackgroundColor = "#16161e"
textColor = "#c0caf5"
```

- [ ] **Step 4: Añadir el import y el helper en `dashboard.py`**

Añadir el import junto a los demás, al inicio del archivo:

```python
from gui_core.estado import COLORES
```

Añadir el helper después de `_filtro_fecha`:

```python
_COLOR_STATUS = {
    "OK": COLORES["ok"],
    "CON_FALLAS": COLORES["alerta"],
    "ERROR": COLORES["alerta"],
    "CON_ADVERTENCIAS": COLORES["precaucion"],
}


def _estilo_status(val) -> str:
    color = _COLOR_STATUS.get(val)
    return f"color: {color}" if color else ""
```

- [ ] **Step 5: Aplicar el Styler en las 2 tablas con columna `status`**

En `tab_resumen`, localizar:

```python
        st.subheader("Últimas 10 ejecuciones")
        cols = [
            "timestamp", "run_id", "project_id", "revision", "status",
            "n_ok", "n_fallas", "max_dv_pct", "max_icc_ka",
        ]
        cols = [c for c in cols if c in df.columns]
        st.dataframe(_tabla_presentacion(df.head(10), cols), use_container_width=True)
```

Reemplazar la última línea por:

```python
        st.dataframe(
            _tabla_presentacion(df.head(10), cols).style.map(_estilo_status, subset=["status"]),
            use_container_width=True,
        )
```

En `tab_proyecto`, localizar:

```python
            st.subheader("Runs del proyecto")
            cols = [
                "timestamp", "run_id", "revision", "status", "norma",
                "n_circuitos", "n_ok", "n_fallas", "max_dv_pct", "max_icc_ka",
            ]
            cols = [c for c in cols if c in df_p.columns]
            st.dataframe(_tabla_presentacion(df_p, cols), use_container_width=True)
```

Reemplazar la última línea por:

```python
            st.dataframe(
                _tabla_presentacion(df_p, cols).style.map(_estilo_status, subset=["status"]),
                use_container_width=True,
            )
```

- [ ] **Step 6: Correr → PASS**

Run: `python -m pytest tests/test_dashboard.py -v`
Expected: 21 passed.

- [ ] **Step 7: Commit**

```bash
git add dashboard.py .streamlit/config.toml tests/test_dashboard.py
git commit -m "feat(dashboard): paleta Tokyo Night (tema base + color de estado en tablas)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Regresión final

**Files:** sin archivos nuevos; solo verificación.

- [ ] **Step 1: Suite completa del proyecto**

Run: `python -m pytest tests/ -q -p no:cacheprovider`
Expected: verde, sin fallos nuevos (los 21 tests de `test_dashboard.py` se suman a los ya existentes).

- [ ] **Step 2: pyflakes**

Run: `python -m pyflakes dashboard.py tests/test_dashboard.py`
Expected: sin salida.

- [ ] **Step 3: Smoke visual real (streamlit run)**

Run: `python -m streamlit run dashboard.py --server.headless true` (dejarlo correr ~5s, confirmar que no crashea al arrancar, luego detenerlo)
Expected: arranca sin traceback; abrir `http://localhost:8501` y confirmar visualmente: tema oscuro Tokyo Night aplicado, columna `status` coloreada en las 2 tablas, control "Rango" visible en el sidebar, rutas DOCX/PDF visibles en Detalle, `commit_hash` como link en Estado técnico.

- [ ] **Step 4: Si todo pasa, no hay commit adicional en esta tarea** (es solo verificación de lo ya commiteado en las Tareas 1-7).

---

## Notas para el ejecutor

- `gui_core/` no se toca en este plan — solo se importa `COLORES` desde `dashboard.py`.
- El warning de PyArrow en "Campos del registro" (columna `valor` con tipos mixtos) es preexistente y no forma parte de este plan — no lo arregles, no está en el alcance aprobado.
- Los tests usan `assert`, nunca `print()` de caracteres no-ASCII — evita el problema de encoding de consola que ya se corrigió en `main.py`.
- Cada tarea es aditiva sobre la anterior — verificar el estado real de `dashboard.py` con Read antes de aplicar el `Reemplazar por` de cada Step 3/4, en caso de que el ejecutor lea las tareas fuera de orden.
