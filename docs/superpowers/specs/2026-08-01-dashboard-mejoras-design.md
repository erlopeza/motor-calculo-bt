# Diseño — Dashboard: correcciones (P0) + filtro de fecha y paleta (P1)

**Fecha:** 2026-08-01 · **Rama base:** `main` (se creará rama de trabajo) · **Estado:** aprobado para plan
**Ámbito:** `dashboard.py` (Streamlit) únicamente. No toca `persistencia.py`, `gui_core/`, `gui/` ni el motor de cálculo.

---

## 1. Objetivo

Probar el flujo completo del proyecto de principio a fin reveló que `dashboard.py` (nunca antes verificado en el ciclo de rediseño de GUI) tenía un bug real de mojibake que lo hacía ilegible (ya corregido, commit `0e72909`). Al comparar su diseño contra herramientas técnicas equivalentes (MLflow/W&B, CI/CD, ETAP, Grafana) surgieron 6 huecos concretos, agrupados en dos bloques por costo/riesgo:

- **P0** — correcciones directas, bajo riesgo: exponer rutas DOCX/PDF, `commit_hash` como link, timestamp legible, error específico de ruta de DB inválida.
- **P1** — mejoras de diseño con decisión propia: filtro de rango de fecha, alineación de paleta con Tokyo Night.
- **P2** (diferido, no en este plan): comparación multi-proyecto/multi-corrida, endurecer exposición de red, **y ahora también coordinar colores de gráficos nativos con la paleta de estado (requeriría migrar a Altair)** — surgido durante el brainstorming de P1b, explícitamente fuera de alcance por costo/beneficio.

## 2. Arquitectura

Todos los cambios viven en `dashboard.py` (helpers nuevos + modificaciones puntuales dentro de `main()`), más un archivo nuevo `.streamlit/config.toml` para el tema base. `dashboard.py` importa `COLORES` de `gui_core.estado` como fuente única de verdad para los colores de estado (verificado: `gui_core` no depende de tkinter, es seguro importarlo desde un script Streamlit). Sin cambios en `persistencia.py`, `gui_core/`, `gui/` ni el motor.

## 3. P0 — Correcciones puntuales

1. **Rutas DOCX/PDF visibles.** `obtener_ejecuciones()` ya retorna `ruta_reporte_docx`/`ruta_reporte_pdf` (confirmado leyendo `persistencia.py`), pero la sección "Rutas de reporte" (tab Detalle) solo muestra TXT/XLSX. Se agregan las 2 líneas faltantes, mismo patrón (`st.text(f"ruta_reporte_docx: {_fmt_val(fila.get('ruta_reporte_docx'))}")` y análogo para PDF).

2. **`commit_hash` como link clickeable.** Nuevo helper:
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
   En la pestaña "Estado técnico", si `_repo_url_web()` devuelve una URL y `commit_hash` no es el placeholder `"—"`, renderizar con `st.markdown(f"commit_hash: [{hash}]({url}/commit/{hash})")`; si no, mantener el `st.text` plano actual (degradación segura).

3. **Timestamp legible.** Nuevo helper:
   ```python
   def _fmt_fecha(dt) -> str:
       """Formatea un datetime (o None/NaT) a 'YYYY-MM-DD HH:MM UTC'; '—' si no hay valor."""
       if dt is None or pd.isna(dt):
           return "—"
       return dt.strftime("%Y-%m-%d %H:%M UTC")
   ```
   Se usa sobre la columna ya parseada `timestamp_dt` (no sobre el string crudo `timestamp`) en el metric "Última ejecución" (tab Resumen). El resto de las tablas conserva el timestamp crudo en la columna `timestamp` (son datos tabulares para inspección/exportación, no una métrica destacada — cambiar el formato ahí no aporta y complica el CSV exportado).

4. **Error específico de ruta de DB inválida.** Antes de llamar a `_normalizar_dataframe`, en `main()`:
   ```python
   from pathlib import Path
   ...
   if not Path(ruta_db).exists():
       st.error(f"El archivo '{ruta_db}' no existe.")
       return
   df = _normalizar_dataframe(ruta_db=ruta_db)
   ```
   Si el archivo existe pero no tiene corridas, se mantiene el `st.info("sin ejecuciones registradas")` actual sin cambios — los dos casos ahora son distinguibles.

## 4. P1a — Filtro de rango de fecha

Control global en `st.sidebar`, justo debajo del input "Ruta DB" — se aplica una sola vez sobre `df` antes de repartirlo a las 4 pestañas, para que "Resumen", "Por proyecto", "Detalle" y "Estado técnico" queden consistentes entre sí (incluido el selector de `run_id` en "Detalle", que solo debe listar corridas dentro del rango activo).

```python
def _filtro_fecha(df: pd.DataFrame, preset: str) -> pd.DataFrame:
    """preset in {'Todo', 'Últimos 7 días', 'Últimos 30 días'}."""
    if preset == "Todo" or df.empty:
        return df
    dias = 7 if preset == "Últimos 7 días" else 30
    corte = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=dias)
    return df[df["timestamp_dt"] >= corte]
```

En `main()`, tras cargar `df` (y después del chequeo de existencia de archivo del punto P0-4):
```python
preset = st.sidebar.radio("Rango", ["Todo", "Últimos 7 días", "Últimos 30 días"], index=0)
df = _filtro_fecha(df, preset)
if df.empty:
    st.info("sin ejecuciones registradas")
    return
```
Default = "Todo" (comportamiento actual sin cambios si el usuario no toca el control). Si el filtro deja el DataFrame vacío, se reutiliza el mismo mensaje de "sin ejecuciones registradas" — no se introduce un tercer estado de error distinto.

## 5. P1b — Alineación de paleta (Tokyo Night)

**Tema base (`.streamlit/config.toml`, archivo nuevo, sin código):**
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
Streamlit aplica esto automáticamente a fondo, sidebar, texto base y acento de botones/controles — sin tocar `dashboard.py`.

**Color de estado en tablas (código, en `dashboard.py`):**
```python
from gui_core.estado import COLORES

_COLOR_STATUS = {
    "OK": COLORES["ok"],
    "CON_FALLAS": COLORES["alerta"],
    "ERROR": COLORES["alerta"],
    "CON_ADVERTENCIAS": COLORES["precaucion"],
}

def _estilo_status(val):
    color = _COLOR_STATUS.get(val)
    return f"color: {color}" if color else ""
```
Aplicado vía `pandas.Styler` a la columna `status` en las tablas "Últimas 10 ejecuciones" (tab Resumen) y "Runs del proyecto" (tab Por proyecto):
```python
st.dataframe(
    _tabla_presentacion(df.head(10), cols).style.map(_estilo_status, subset=["status"]),
    use_container_width=True,
)
```
(mismo criterio de mapeo que ya usa `_estado_gantt_desde_status`, reutilizando `COLORES` en vez de duplicar hex).

**Límite de alcance explícito:** los gráficos nativos (`st.bar_chart`/`st.line_chart` de "Distribución status", "Distribución norma", "Evolución por revisión") **quedan con la paleta categórica por defecto de Streamlit**, no con colores por status/norma específicos — coordinarlos requeriría migrar a Altair con escalas de color explícitas. **Diferido a P2**, según decisión explícita durante el brainstorming.

## 6. Manejo de errores

- `_repo_url_web()`: cualquier fallo (sin git instalado, sin remoto configurado, timeout) degrada a `None` → texto plano, nunca crashea el dashboard.
- `_fmt_fecha`: `None`/`NaT` → `"—"`, igual que el resto de los helpers `_fmt_val`.
- `_filtro_fecha`: DataFrame vacío de entrada se retorna sin tocar (evita error de comparación sobre DataFrame vacío).
- Verificación de ruta de DB: se hace con `Path.exists()` antes de cualquier intento de conexión SQLite — evita que `obtener_ejecuciones` tenga que distinguir el caso (ya tiene su propio try/except interno para errores de conexión, sin cambios ahí).

## 7. Estrategia de pruebas

`dashboard.py` no tiene tests hoy (confirmado). Dos niveles, ambos ejecutables sin display (a diferencia de los tests Tk, Streamlit no necesita GUI real):

1. **Unit tests puros** sobre los helpers nuevos/modificados — no requieren Streamlit en absoluto: `_fmt_fecha`, `_repo_url_web` (mockeando `subprocess.check_output`), `_filtro_fecha`, `_estilo_status`.
2. **Smoke con `streamlit.testing.v1.AppTest`** (disponible en Streamlit ≥1.28, confirmado 1.56.0 instalado): instancia `main()` sin servidor real, verifica que no crashea con una DB real de prueba, que el error de ruta inválida se muestra (`at.error` no vacío) cuando corresponde, y que el filtro de fecha reduce el número de filas mostradas.

Nuevo archivo: `tests/test_dashboard.py`.

## 8. Fuera de alcance (explícitamente diferido)

- Comparación multi-proyecto/multi-corrida lado a lado (P2, backlog previo).
- Endurecer exposición de red — bind a localhost por defecto (P2, backlog previo, es más decisión de despliegue/documentación que de código).
- **Coordinar colores de gráficos nativos con la paleta de estado** (P2, nuevo — requeriría migrar a Altair).
- Fase 5 de la GUI Tkinter (Emergencia) — sin relación con este plan, ya diferida por separado.
