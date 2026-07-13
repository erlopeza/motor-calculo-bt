# GUI Plan 3-A — render de resultados no tabulares — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que los 5 módulos no tabulares de la GUI (`icc_trafo`, `balance`, `demanda`, `flujo_nodal`, `reporte`) muestren su resultado en el panel al pulsar Calcular, en vez de solo cambiar el badge.

**Architecture:** `PanelModulo` (en `gui/componentes.py`) gana primitivas aditivas `mostrar_fichas`, `agregar_accion` y `limpiar_resultados`; `mostrar_tabla` deja de auto-limpiar. En `gui/app.py` un registro `RENDER[id] = fn(panel, resultado)` reemplaza a `_COLUMNAS`: los 8 tabulares se generan con una fábrica `_tabla(...)`, los 5 nuevos son adaptadores explícitos. `ejecutar_modulo` limpia el panel una vez y delega al adaptador. `gui_core` no se toca.

**Tech Stack:** Python 3.13, tkinter/ttk, pytest. Sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-07-12-gui-resultados-no-tabulares-design.md`

**Contexto de datos (formas reales verificadas contra `circuitos.xlsx`):**
- `presentar_icc_trafo` → `{"Icc_kA": float, "Zt_ohm": float, "alertas": []}`
- `presentar_balance` → `{"resultado": {...,"uso_trafo_pct","estado_trafo"}, "tableros": {nombre: {"S_total_kva","uso_pct","desequilibrio_pct","estado",...}}, "alertas": []}`
- `presentar_demanda` → `{"resultado": {"tipo_instalacion","P_total_kw","S_total_kva","I_alim_A","factor_crecimiento",...}, "alertas": []}`
- `presentar_flujo_nodal` → `{"buses": [{"id","V_pu","V_kV","P_kW"}], "convergido": bool, "perdidas_kW": float, "alertas": [...]}`
- `presentar_reporte(sesion, carpeta_salida=None)` → `{"apto_emision": bool, "nivel": str, "alertas": [...], "ruta_docx": str, "ruta_pdf": str, "ruta_json": str}`

---

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `gui/componentes.py` | `PanelModulo`: + `mostrar_fichas`, `agregar_accion`, `limpiar_resultados`; `mostrar_tabla` aditiva | Modificar |
| `gui/app.py` | `RENDER` (fábrica `_tabla` + 5 adaptadores + `_fmt`/`_abrir_carpeta`), `carpeta_reportes`, `ejecutar_modulo` reescrito | Modificar |
| `tests/test_gui_componentes.py` | smokes de las primitivas nuevas | Modificar |
| `tests/test_gui_app.py` | wiring: los 5 no tabulares dejan el panel no vacío; regresión tabulares | Modificar |

Reglas: colores solo desde `COLORES`; `gui/` importa `gui_core`, nunca al revés; cada módulo importable sin display.

---

## Task 1: Primitivas de render en `PanelModulo`

**Files:**
- Modify: `gui/componentes.py` (clase `PanelModulo`, método `mostrar_tabla` actual)
- Test: `tests/test_gui_componentes.py` (añadir al final)

- [ ] **Step 1: Escribir smokes (añadir al final de `tests/test_gui_componentes.py`)**

```python
@requiere_display
def test_panel_mostrar_fichas_y_limpiar():
    import tkinter as tk
    from gui.componentes import PanelModulo
    from gui_core.fases import buscar_modulo
    from gui_core.sesion import SesionProyecto
    root = tk.Tk(); root.withdraw()
    try:
        s = SesionProyecto(circuitos=[{"nombre": "C1", "sistema": "3F", "conductor": "6AWG",
            "S_mm2": 13.3, "I_max": 65, "paralelos": 1, "I_diseno": 40, "cos_phi": 0.9,
            "L_m": 15, "temp_amb": 30}])
        panel = PanelModulo(root, buscar_modulo("dv"), s, on_calcular=lambda mid: None)
        panel.mostrar_fichas([("Icc (kA)", "10.8", None), ("Estado", "FALLA", "alerta")])
        assert len(panel.contenedor_resultados.winfo_children()) >= 1
        panel.limpiar_resultados()
        assert len(panel.contenedor_resultados.winfo_children()) == 0
    finally:
        root.destroy()


@requiere_display
def test_panel_agregar_accion_invocable():
    import tkinter as tk
    from gui.componentes import PanelModulo
    from gui_core.fases import buscar_modulo
    from gui_core.sesion import SesionProyecto
    root = tk.Tk(); root.withdraw()
    try:
        s = SesionProyecto(circuitos=[{"nombre": "C1", "sistema": "3F", "conductor": "6AWG",
            "S_mm2": 13.3, "I_max": 65, "paralelos": 1, "I_diseno": 40, "cos_phi": 0.9,
            "L_m": 15, "temp_amb": 30}])
        panel = PanelModulo(root, buscar_modulo("dv"), s, on_calcular=lambda mid: None)
        clic = []
        btn = panel.agregar_accion("Abrir carpeta", lambda: clic.append(1))
        btn.invoke()
        assert clic == [1]
    finally:
        root.destroy()


@requiere_display
def test_panel_fichas_y_tabla_coexisten():
    import tkinter as tk
    from gui.componentes import PanelModulo
    from gui_core.fases import buscar_modulo
    from gui_core.sesion import SesionProyecto
    root = tk.Tk(); root.withdraw()
    try:
        s = SesionProyecto(circuitos=[{"nombre": "C1", "sistema": "3F", "conductor": "6AWG",
            "S_mm2": 13.3, "I_max": 65, "paralelos": 1, "I_diseno": 40, "cos_phi": 0.9,
            "L_m": 15, "temp_amb": 30}])
        panel = PanelModulo(root, buscar_modulo("dv"), s, on_calcular=lambda mid: None)
        panel.mostrar_fichas([("Convergió", "sí", "ok")])
        panel.mostrar_tabla(["A", "B"], [["1", "2"]])
        # fichas (1 frame) + tabla (1 frame) → al menos 2 hijos, no se pisan
        assert len(panel.contenedor_resultados.winfo_children()) >= 2
    finally:
        root.destroy()
```

- [ ] **Step 2: Correr → FAIL** (`AttributeError: 'PanelModulo' object has no attribute 'mostrar_fichas'`)

Run: `python -m pytest tests/test_gui_componentes.py -q`

- [ ] **Step 3: Modificar `PanelModulo.mostrar_tabla` y añadir las primitivas**

En `gui/componentes.py`, reemplazar el método actual:
```python
    def mostrar_tabla(self, columnas: list[str], filas: list[list]) -> None:
        for w in self.contenedor_resultados.winfo_children():
            w.destroy()
        tabla = TablaResultados(self.contenedor_resultados, columnas)
        tabla.configure(bg=COLORES["fondo"])
        tabla.set_filas(filas)
        tabla.pack(fill="both", expand=True)
```
por (mostrar_tabla ya NO limpia; se añaden `limpiar_resultados`, `mostrar_fichas`, `agregar_accion`):
```python
    def limpiar_resultados(self) -> None:
        for w in self.contenedor_resultados.winfo_children():
            w.destroy()

    def mostrar_tabla(self, columnas: list[str], filas: list[list]) -> None:
        tabla = TablaResultados(self.contenedor_resultados, columnas)
        tabla.configure(bg=COLORES["fondo"])
        tabla.set_filas(filas)
        tabla.pack(fill="both", expand=True)

    def mostrar_fichas(self, pares: list[tuple]) -> None:
        """pares: lista de (etiqueta, valor, rol) con rol in {None,'ok','alerta','precaucion'}."""
        roles = {"ok": COLORES["ok"], "alerta": COLORES["alerta"],
                 "precaucion": COLORES["precaucion"]}
        cont = tk.Frame(self.contenedor_resultados, bg=COLORES["fondo"])
        cont.pack(fill="x", anchor="w")
        for par in pares:
            etiqueta, valor = par[0], par[1]
            rol = par[2] if len(par) > 2 else None
            fila = tk.Frame(cont, bg=COLORES["fondo"]); fila.pack(fill="x", anchor="w", pady=1)
            tk.Label(fila, text=f"{etiqueta}:", bg=COLORES["fondo"], fg=COLORES["texto_tenue"],
                     font=("Segoe UI", 10), width=22, anchor="w").pack(side="left")
            tk.Label(fila, text=str(valor), bg=COLORES["fondo"],
                     fg=roles.get(rol, COLORES["texto"]), font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(side="left")

    def agregar_accion(self, texto: str, comando):
        btn = BotonAccion(self.contenedor_resultados, texto, comando)
        btn.pack(anchor="w", pady=(8, 0))
        return btn
```

- [ ] **Step 4: Correr → PASS/skip**

Run: `python -m pytest tests/test_gui_componentes.py -q`
Expected: passed (con display) o skipped (headless); nunca error de import.

- [ ] **Step 5: Verificar import sin display**

Run: `python -c "import gui.componentes; print('ok')"`
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add gui/componentes.py tests/test_gui_componentes.py
git commit -m "feat(gui): PanelModulo — mostrar_fichas/agregar_accion/limpiar_resultados (tabla aditiva)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Registro `RENDER` + rewire `ejecutar_modulo` en `gui/app.py`

**Files:**
- Modify: `gui/app.py` (import `os`; `_COLUMNAS` → `RENDER`; `__init__` + `carpeta_reportes`; `ejecutar_modulo`)
- Test: `tests/test_gui_app.py` (añadir al final)

- [ ] **Step 1: Escribir tests de wiring (añadir al final de `tests/test_gui_app.py`)**

```python
@requiere_display
def test_app_render_no_tabulares_no_vacio(tmp_path):
    from gui.app import AppBT
    from gui.cargador import cargar_excel_a_sesion
    from pathlib import Path
    import gui.app as app_mod
    LIBRO = str(Path(app_mod.__file__).resolve().parents[1] / "circuitos.xlsx")
    app = AppBT()
    app.withdraw()
    app.carpeta_reportes = str(tmp_path)   # no ensuciar el repo
    try:
        cargar_excel_a_sesion(LIBRO, app.sesion)
        for fase, mid in [(2, "icc_trafo"), (4, "balance"), (4, "demanda"),
                          (4, "flujo_nodal"), (6, "reporte")]:
            app.mostrar_fase(fase)
            app.ejecutar_modulo(mid)
            assert mid in app.sesion.resultados
            panel = next(p for p in app.paneles_actuales if p.modulo.id == mid)
            assert len(panel.contenedor_resultados.winfo_children()) >= 1, f"{mid} sin render"
    finally:
        app.destroy()


@requiere_display
def test_app_render_tabular_sigue_funcionando():
    from gui.app import AppBT
    app = AppBT()
    app.withdraw()
    try:
        app.sesion.cargar({"circuitos": [{"nombre": "C1", "sistema": "3F",
            "conductor": "6AWG", "S_mm2": 13.3, "I_max": 65, "paralelos": 1,
            "I_diseno": 40, "cos_phi": 0.9, "L_m": 15, "temp_amb": 30}]})
        app.mostrar_fase(1)
        app.ejecutar_modulo("dv")
        panel = next(p for p in app.paneles_actuales if p.modulo.id == "dv")
        assert len(panel.contenedor_resultados.winfo_children()) >= 1
    finally:
        app.destroy()
```

- [ ] **Step 2: Correr → FAIL** (`AttributeError: 'AppBT' object has no attribute 'carpeta_reportes'` y/o render vacío)

Run: `python -m pytest tests/test_gui_app.py -q`

- [ ] **Step 3: Reescribir la cabecera de `gui/app.py` (imports + `_COLUMNAS` → `RENDER` + helpers)**

Reemplazar las líneas de import superiores y TODO el bloque `_COLUMNAS = {...}` por:
```python
"""Ventana principal de la GUI por fases (Tokyo Night) sobre gui_core."""
from __future__ import annotations

import os
import traceback
import tkinter as tk
from tkinter import filedialog

from gui_core.estado import COLORES
from gui_core.fases import modulos_de_fase, PRESENTADOR
from gui_core.sesion import SesionProyecto
from gui.componentes import BarraSuperior, RielFases, PanelModulo
from gui.cargador import cargar_excel_a_sesion


def _fmt(v, dec: int = 2) -> str:
    """Formato seguro de número; '—' si None, str crudo si no es numérico."""
    if v is None:
        return "—"
    try:
        return f"{float(v):.{dec}f}"
    except (TypeError, ValueError):
        return str(v)


def _abrir_carpeta(carpeta: str) -> None:
    try:
        os.startfile(carpeta)  # solo Windows; no-op controlado si no existe
    except Exception:
        pass


def _tabla(columnas, extractor):
    """Fábrica de adaptador tabular: renderiza resultado['filas'] como tabla."""
    def adaptador(panel, resultado):
        panel.mostrar_tabla(columnas, [extractor(f) for f in resultado.get("filas", [])])
    return adaptador


def _render_icc_trafo(panel, r):
    panel.mostrar_fichas([
        ("Icc (kA)", _fmt(r.get("Icc_kA")), None),
        ("Zt (Ω)", _fmt(r.get("Zt_ohm"), 5), None),
    ])


def _render_flujo_nodal(panel, r):
    conv = bool(r.get("convergido"))
    panel.mostrar_fichas([
        ("Convergió", "sí" if conv else "no", "ok" if conv else "alerta"),
        ("Pérdidas (kW)", _fmt(r.get("perdidas_kW"), 3), None),
    ])
    buses = r.get("buses", [])
    if buses:
        panel.mostrar_tabla(
            ["Barra", "V (pu)", "V (kV)", "P (kW)"],
            [[b.get("id"), _fmt(b.get("V_pu"), 4), _fmt(b.get("V_kV"), 4), _fmt(b.get("P_kW"))]
             for b in buses],
        )


def _render_balance(panel, r):
    tableros = r.get("tableros", {})
    panel.mostrar_tabla(
        ["Tablero", "S dem (kVA)", "Uso %", "Deseq. %", "Estado"],
        [[nombre, _fmt(t.get("S_total_kva")), _fmt(t.get("uso_pct"), 1),
          _fmt(t.get("desequilibrio_pct"), 1), t.get("estado", "—")]
         for nombre, t in tableros.items()],
    )
    res = r.get("resultado", {})
    estado_tr = res.get("estado_trafo", "")
    rol = "alerta" if str(estado_tr).upper() not in ("OK", "") else "ok"
    panel.mostrar_fichas([
        ("Uso trafo %", _fmt(res.get("uso_trafo_pct"), 1), None),
        ("Estado trafo", estado_tr or "—", rol),
    ])


def _render_demanda(panel, r):
    res = r.get("resultado", {})
    panel.mostrar_fichas([
        ("Tipo instalación", res.get("tipo_instalacion", "—"), None),
        ("P total (kW)", _fmt(res.get("P_total_kw")), None),
        ("S total (kVA)", _fmt(res.get("S_total_kva")), None),
        ("I alim (A)", _fmt(res.get("I_alim_A"), 1), None),
        ("Factor crecimiento", _fmt(res.get("factor_crecimiento")), None),
    ])


def _render_reporte(panel, r):
    nivel = r.get("nivel", "—")
    rol = {"FINAL": "ok", "BORRADOR": "precaucion", "INCOMPLETO": "alerta"}.get(nivel)
    fichas = [("Nivel emisión", nivel, rol)]
    for etq, key in [("DOCX", "ruta_docx"), ("PDF", "ruta_pdf"), ("JSON", "ruta_json")]:
        ruta = r.get(key) or ""
        fichas.append((etq, os.path.basename(ruta) if ruta else "—", None))
    panel.mostrar_fichas(fichas)
    carpeta = os.path.dirname(r.get("ruta_docx") or "")
    if carpeta:
        panel.agregar_accion("Abrir carpeta", lambda c=carpeta: _abrir_carpeta(c))


RENDER = {
    "dv": _tabla(["Circuito", "ΔV (V)", "ΔV (%)", "Estado"],
                 lambda f: [f["nombre"], f["dv_v"], f["dv_pct"], f["estado"]]),
    "capacidad": _tabla(["Circuito", "I diseño", "Cap (A)", "OK"],
                        lambda f: [f["nombre"], f["I_diseno"], f["cap_A"], f["ok"]]),
    "sugerencia": _tabla(["Circuito", "Sugerido", "Cap (A)", "ΔV (%)"],
                         lambda f: [f["nombre"], f["sugerido"], f["cap_A"], f["dv_pct"]]),
    "icc_punto": _tabla(["Circuito", "Icc (kA)", "Zt total"],
                        lambda f: [f["nombre"], f["Icc_kA"], f["Zt_total"]]),
    "aporte_motores": _tabla(["Motor", "P (kW)", "Aporte (A)"],
                             lambda f: [f["nombre"], f["P_kW"], f["I_aporte_A"]]),
    "protecciones": _tabla(["Circuito", "Estado", "Icc (kA)"],
                           lambda f: [f["nombre"], f["estado"], f["Icc_kA"]]),
    "coordinacion": _tabla(["Dispositivo", "t (s)", "Región"],
                           lambda f: [f["nombre"], f["t_s"], f["region"]]),
    "arc_flash": _tabla(["Circuito", "E (cal/cm²)", "Frontera (mm)", "Cat EPP"],
                        lambda f: [f["nombre"], f["E_cal_cm2"], f["D_afb_mm"], f["categoria_ppe"]]),
    "icc_trafo": _render_icc_trafo,
    "flujo_nodal": _render_flujo_nodal,
    "balance": _render_balance,
    "demanda": _render_demanda,
    "reporte": _render_reporte,
}
```

- [ ] **Step 4: Añadir `carpeta_reportes` en `AppBT.__init__`**

Tras la línea `self.paneles_actuales: list[PanelModulo] = []` añadir:
```python
        self.carpeta_reportes = os.path.join(os.getcwd(), "salida_reportes")
```

- [ ] **Step 5: Reescribir `ejecutar_modulo`**

Reemplazar el método `ejecutar_modulo` actual por:
```python
    def ejecutar_modulo(self, modulo_id: str):
        fn = PRESENTADOR.get(modulo_id)
        if fn is None:
            return
        try:
            if modulo_id == "reporte":
                os.makedirs(self.carpeta_reportes, exist_ok=True)
                resultado = fn(self.sesion, carpeta_salida=self.carpeta_reportes)
            else:
                resultado = fn(self.sesion)
            self.sesion.registrar(modulo_id, resultado, resultado.get("alertas", []))
        except Exception as e:
            traceback.print_exc()
            self.barra.set_info(self.sesion.proyecto, self.sesion.perfil,
                                 estado=f"error en {modulo_id}: {e}", es_error=True)
            return
        adaptador = RENDER.get(modulo_id)
        for panel in self.paneles_actuales:
            if panel.modulo.id == modulo_id and adaptador is not None:
                panel.limpiar_resultados()
                adaptador(panel, resultado)
            panel.refrescar_estado()
        self.riel.refrescar()
```

- [ ] **Step 6: Correr → PASS/skip**

Run: `python -m pytest tests/test_gui_app.py -q`
Expected: los 5 no tabulares dejan panel no vacío; el tabular (`dv`) sigue con contenido; `test_app_importable_sin_display` PASS.

- [ ] **Step 7: Verificar import sin display + pyflakes**

Run: `python -c "import gui.app; print('ok')"` → `ok`
Run: `python -m pyflakes gui/app.py gui/componentes.py` → sin salida

- [ ] **Step 8: Commit**

```bash
git add gui/app.py tests/test_gui_app.py
git commit -m "feat(gui): RENDER reemplaza _COLUMNAS; render de icc_trafo/balance/demanda/flujo_nodal/reporte

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Verificación end-to-end + regresión

**Files:**
- Test: sin archivos nuevos; corrida de verificación

- [ ] **Step 1: Drive end-to-end con el Excel real (todos los módulos renderizan)**

Crear script temporal en el scratchpad de la sesión (NO commitear), con este contenido, y ejecutarlo:
```python
import os, sys, tempfile
ROOT = r"C:\Users\user007\Documents\motor-calculo-bt"
sys.path.insert(0, ROOT); os.chdir(ROOT)
from gui.app import AppBT, RENDER
from gui.cargador import cargar_excel_a_sesion
from gui_core.fases import FASES, modulos_de_fase, PRESENTADOR

app = AppBT(); app.withdraw()
app.carpeta_reportes = tempfile.mkdtemp(prefix="rep_")  # no ensuciar el repo
cargar_excel_a_sesion(os.path.join(ROOT, "circuitos.xlsx"), app.sesion)
fallos, vacios = [], []
try:
    for fase in FASES:
        app.mostrar_fase(fase)
        for m in modulos_de_fase(fase):
            if m.id not in PRESENTADOR:
                continue
            if not m.prereq(app.sesion):
                continue
            try:
                app.ejecutar_modulo(m.id)
                panel = next(p for p in app.paneles_actuales if p.modulo.id == m.id)
                n = len(panel.contenedor_resultados.winfo_children())
                print(f"  [{'OK' if n else 'VACIO'}] {m.id:16} hijos={n} render={'sí' if m.id in RENDER else 'no'}")
                if n == 0:
                    vacios.append(m.id)
            except Exception as e:
                fallos.append((m.id, repr(e)))
                print(f"  [XX] {m.id}: {e}")
finally:
    app.destroy()
print("RESULTADO:", "OK" if not fallos and not vacios else f"fallos={fallos} vacios={vacios}")
sys.exit(1 if (fallos or vacios) else 0)
```

Expected: cada módulo con presentador y prereq cumplido imprime `[OK] ... hijos>=1`; `RESULTADO: OK`; exit 0.

- [ ] **Step 2: Suite completa**

Run: `python -m pytest tests/ -q -p no:cacheprovider`
Expected: verde. Con los 5 tests nuevos (3 de Task 1 + 2 de Task 2), ≈763 passed + 8 skipped con display disponible; sin fallos nuevos. Correr una sola vez, sin runs de pytest solapados (los tests de reportería generan imágenes en rutas compartidas y dos corridas concurrentes se pisan).

- [ ] **Step 3: pyflakes global GUI**

Run: `python -m pyflakes gui.py gui/*.py gui_core/*.py`
Expected: sin salida.

- [ ] **Step 4: Commit (si hubo ajustes) / no-op**

Si algún ajuste fue necesario en Task 1/2 durante la verificación, commitearlo con mensaje descriptivo. Si todo pasó sin cambios, no hay commit en esta tarea.

---

## Notas para el ejecutor

- `gui_core/` NO se toca en este plan. Solo `gui/componentes.py`, `gui/app.py` y sus tests.
- Colores SIEMPRE desde `COLORES`. No hardcodear hex.
- `mostrar_tabla` deja de auto-limpiar: la limpieza ocurre una sola vez en `ejecutar_modulo` vía `limpiar_resultados()`, para que fichas + tabla coexistan.
- Los adaptadores deben ser tolerantes a claves faltantes (`.get` + `_fmt`); nunca lanzar por clave ausente.
- El botón "Abrir carpeta" deriva la carpeta de `os.path.dirname(ruta_docx)`; si no hubo generación (sin circuitos), no se añade el botón.
- Verificación headless: los tests Tk usan `@requiere_display`; en CI sin display se saltan (esperado).
