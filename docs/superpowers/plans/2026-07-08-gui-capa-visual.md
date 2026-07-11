# GUI — Capa visual Tkinter (`gui/`) — Plan de implementación (Plan 2 de 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir la capa visual Tkinter (shell por fases + componentes + paneles de módulo) sobre el núcleo `gui_core`, reemplazando el `MotorCalculoBT` de tabs por la navegación de 7 fases con paleta Tokyo Night.

**Architecture:** Componentes reutilizables en `gui/componentes.py` (widgets Tk estilizados con `gui_core.estado.COLORES`). La ventana principal `gui/app.py` mantiene una `SesionProyecto`, dibuja el `RielFases` y renderiza, por fase, un `PanelModulo` por módulo del registro `gui_core.fases.MODULOS`; el botón Calcular llama al presentador de `PRESENTADOR`, registra el resultado y refresca los badges. `gui.py` pasa a ser un lanzador delgado. La lógica ya vive en `gui_core` (Plan 1); esta capa solo renderiza y enruta eventos.

**Tech Stack:** Python 3.13, tkinter/ttk, pytest. Sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-06-24-gui-rediseno-fases-tokyo-night-design.md` (secciones A–E)

**Contexto del núcleo (Plan 1, ya en main):**
- `gui_core.estado`: `COLORES` (dict Tokyo Night), `Estado` (enum), `color_de_estado(Estado)->hex`.
- `gui_core.sesion.SesionProyecto`: `cargar(dict)`, `registrar(id, resultado, alertas)`, flags `tiene_*`, `.resultados`, `.proyecto`, `.perfil`.
- `gui_core.fases`: `FASES` (dict 0..6), `MODULOS` (list[Modulo] con `.id/.nombre/.norma/.fase/.requiere/.prereq`), `modulos_de_fase(n)`, `estado_modulo(m, s)->Estado`, `estado_fase(n, s)->Estado`, `buscar_modulo(id)`, `PRESENTADOR` (dict id→fn(sesion)->{"filas"/"buses"/..., "alertas":[...]}).

---

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `gui/headless.py` | helper `hay_display()` + skip para tests Tk | Crear |
| `gui/componentes.py` | `BarraSuperior`, `RielFases`, `BadgeEstado`, `PanelModulo`, `BotonAccion`, `TablaResultados` | Crear |
| `gui/app.py` | `AppBT(tk.Tk)` — shell: sesión + riel + área de paneles + wiring | Crear |
| `gui/cargador.py` | `cargar_excel_a_sesion(ruta, sesion)` — lee hojas (excel.py) → `SesionProyecto.cargar` | Crear |
| `gui_core/presentadores.py` | + presentadores fase 5-6 (emergencia/reporte) | Modificar |
| `gui_core/fases.py` | ampliar `PRESENTADOR` con fase 5-6 | Modificar |
| `gui.py` | lanzador delgado → `gui.app.AppBT` | Reescribir |
| `tests/test_gui_componentes.py` | smokes headless-skip de componentes | Crear |
| `tests/test_gui_app.py` | smoke headless-skip del shell + wiring | Crear |
| `tests/test_gui_cargador.py` | cargador Excel → sesión (sin display) | Crear |
| `tests/test_gui_core_presentadores_emergencia.py` | presentadores fase 5-6 (sin display) | Crear |

Reglas:
- Los componentes leen color SOLO de `gui_core.estado.COLORES` (una fuente de verdad).
- Las sub-ventanas actuales (`gui/arranque_window.py`, `emergencia_window.py`, `guiada_window.py`, `reporte_window.py`) se **retiran** al final (Task 8), su función queda cubierta por paneles de fase 5-6.
- `gui_core/` sigue sin importar tkinter; `gui/` importa `gui_core` (nunca al revés).

---

## Task 1: Helper headless para tests Tk

**Files:**
- Create: `gui/headless.py`
- Test: `tests/test_gui_componentes.py` (se crea aquí con el primer uso)

- [ ] **Step 1: Escribir helper**

`gui/headless.py`:
```python
"""Utilidad para tests de Tkinter: detecta si hay display disponible."""
from __future__ import annotations


def hay_display() -> bool:
    """True si se puede crear una raíz Tk (hay display). En CI headless → False."""
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.destroy()
        return True
    except Exception:
        return False
```

- [ ] **Step 2: Test del helper (no requiere display)**

`tests/test_gui_componentes.py` (inicio del archivo):
```python
import pytest
from gui.headless import hay_display

requiere_display = pytest.mark.skipif(not hay_display(), reason="sin display (headless)")


def test_hay_display_es_bool():
    assert isinstance(hay_display(), bool)
```

- [ ] **Step 3: Correr → PASS**

Run: `python -m pytest tests/test_gui_componentes.py -q`
Expected: 1 passed (o el skip marker disponible).

- [ ] **Step 4: Commit**

```bash
git add gui/headless.py tests/test_gui_componentes.py
git commit -m "feat(gui): helper headless para tests Tk

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Componentes básicos — BadgeEstado, BotonAccion, TablaResultados

**Files:**
- Create: `gui/componentes.py`
- Test: `tests/test_gui_componentes.py`

- [ ] **Step 1: Escribir smokes (headless-skip)**

Añadir a `tests/test_gui_componentes.py`:
```python
@requiere_display
def test_badge_estado_muestra_color_por_estado():
    import tkinter as tk
    from gui_core.estado import Estado, color_de_estado
    from gui.componentes import BadgeEstado
    root = tk.Tk(); root.withdraw()
    try:
        b = BadgeEstado(root, Estado.CALCULADO)
        assert b.cget("foreground") == color_de_estado(Estado.CALCULADO) or b.color == color_de_estado(Estado.CALCULADO)
        b.set_estado(Estado.ALERTA)
        assert b.color == color_de_estado(Estado.ALERTA)
    finally:
        root.destroy()


@requiere_display
def test_boton_accion_deshabilitado():
    import tkinter as tk
    from gui.componentes import BotonAccion
    root = tk.Tk(); root.withdraw()
    try:
        llamado = []
        btn = BotonAccion(root, "Calcular", lambda: llamado.append(1))
        btn.set_habilitado(False)
        assert str(btn["state"]) == "disabled"
        btn.set_habilitado(True)
        assert str(btn["state"]) == "normal"
    finally:
        root.destroy()


@requiere_display
def test_tabla_resultados_llena_filas():
    import tkinter as tk
    from gui.componentes import TablaResultados
    root = tk.Tk(); root.withdraw()
    try:
        t = TablaResultados(root, ["Circuito", "Icc (kA)"])
        t.set_filas([["C-01", "10.8"], ["C-02", "9.1"]])
        assert t.num_filas() == 2
    finally:
        root.destroy()
```

- [ ] **Step 2: Correr → FAIL** (`ImportError: gui.componentes`)

Run: `python -m pytest tests/test_gui_componentes.py -q`

- [ ] **Step 3: Implementar `gui/componentes.py` (parte 1)**

```python
"""Componentes Tkinter reutilizables, estilizados con la paleta Tokyo Night."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui_core.estado import COLORES, Estado, color_de_estado

_ETIQUETA = {
    Estado.SIN_DATOS: "sin datos",
    Estado.LISTO: "listo",
    Estado.CALCULADO: "calculado",
    Estado.ALERTA: "alerta",
}


class BadgeEstado(tk.Label):
    """Punto + etiqueta de estado, coloreado."""

    def __init__(self, master, estado: Estado):
        super().__init__(master, bg=COLORES["panel"])
        self.set_estado(estado)

    def set_estado(self, estado: Estado) -> None:
        self.color = color_de_estado(estado)
        self.configure(text=f"● {_ETIQUETA[estado]}", fg=self.color,
                       bg=COLORES["panel"], font=("Segoe UI", 9))


class BotonAccion(tk.Button):
    """Botón azul relleno; gris cuando se deshabilita."""

    def __init__(self, master, texto: str, comando):
        super().__init__(
            master, text=texto, command=comando,
            bg=COLORES["acento"], fg=COLORES["fondo"], relief="flat",
            activebackground=COLORES["acento"], font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2", bd=0,
        )

    def set_habilitado(self, habilitado: bool) -> None:
        if habilitado:
            self.configure(state="normal", bg=COLORES["acento"], fg=COLORES["fondo"])
        else:
            self.configure(state="disabled", bg=COLORES["borde"], fg=COLORES["texto_tenue"])


class TablaResultados(tk.Frame):
    """Tabla ttk.Treeview con encabezado Tokyo Night."""

    def __init__(self, master, columnas: list[str]):
        super().__init__(master, bg=COLORES["fondo"])
        self.columnas = columnas
        self.tree = ttk.Treeview(self, columns=columnas, show="headings", height=8)
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=110)
        self.tree.pack(fill="both", expand=True)

    def set_filas(self, filas: list[list]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fila in filas:
            self.tree.insert("", "end", values=fila)

    def num_filas(self) -> int:
        return len(self.tree.get_children())
```

- [ ] **Step 4: Correr → PASS (o skip si headless)**

Run: `python -m pytest tests/test_gui_componentes.py -q`
Expected: passed o skipped (headless) — nunca error de import.

- [ ] **Step 5: Verificar import sin display**

Run: `python -c "import gui.componentes; print('ok')"`
Expected: `ok` (importar el módulo no crea ventanas).

- [ ] **Step 6: Commit**

```bash
git add gui/componentes.py tests/test_gui_componentes.py
git commit -m "feat(gui): componentes BadgeEstado, BotonAccion, TablaResultados

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Componentes de navegación — RielFases y BarraSuperior

**Files:**
- Modify: `gui/componentes.py`
- Test: `tests/test_gui_componentes.py`

- [ ] **Step 1: Escribir smokes**

Añadir a `tests/test_gui_componentes.py`:
```python
@requiere_display
def test_riel_fases_lista_las_7_fases():
    import tkinter as tk
    from gui.componentes import RielFases
    from gui_core.sesion import SesionProyecto
    root = tk.Tk(); root.withdraw()
    try:
        seleccion = []
        riel = RielFases(root, SesionProyecto(), on_seleccion=lambda n: seleccion.append(n))
        assert len(riel.items) == 7
        riel.seleccionar(3)
        assert seleccion == [3]
    finally:
        root.destroy()


@requiere_display
def test_barra_superior_muestra_proyecto():
    import tkinter as tk
    from gui.componentes import BarraSuperior
    root = tk.Tk(); root.withdraw()
    try:
        barra = BarraSuperior(root, on_cargar=lambda: None)
        barra.set_info(proyecto="LEO-ARICA", perfil="datacenter", estado="12 hojas")
        assert "LEO-ARICA" in barra.texto_proyecto()
    finally:
        root.destroy()
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_componentes.py -q`

- [ ] **Step 3: Implementar (añadir a `gui/componentes.py`)**

```python
from gui_core.fases import FASES, estado_fase


class RielFases(tk.Frame):
    """Lista vertical de las 7 fases con badge de estado; notifica selección."""

    def __init__(self, master, sesion, on_seleccion):
        super().__init__(master, bg=COLORES["panel"], width=200)
        self.sesion = sesion
        self.on_seleccion = on_seleccion
        self.items: dict[int, tk.Frame] = {}
        self._puntos: dict[int, tk.Label] = {}
        for n, nombre in FASES.items():
            fila = tk.Frame(self, bg=COLORES["panel"], cursor="hand2")
            fila.pack(fill="x")
            punto = tk.Label(fila, text="●", bg=COLORES["panel"], fg=COLORES["texto_tenue"])
            punto.pack(side="left", padx=(12, 8), pady=6)
            lbl = tk.Label(fila, text=f"{n} · {nombre}", bg=COLORES["panel"],
                           fg=COLORES["texto"], font=("Segoe UI", 10), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            for w in (fila, punto, lbl):
                w.bind("<Button-1>", lambda e, k=n: self.seleccionar(k))
            self.items[n] = fila
            self._puntos[n] = punto
        self.refrescar()

    def seleccionar(self, fase: int) -> None:
        for n, fila in self.items.items():
            bg = COLORES["seleccion"] if n == fase else COLORES["panel"]
            fila.configure(bg=bg)
            for hijo in fila.winfo_children():
                hijo.configure(bg=bg)
        self.on_seleccion(fase)

    def refrescar(self) -> None:
        for n, punto in self._puntos.items():
            punto.configure(fg=color_de_estado(estado_fase(n, self.sesion)))


class BarraSuperior(tk.Frame):
    """Barra superior: proyecto · perfil · [Cargar Excel] · estado."""

    def __init__(self, master, on_cargar):
        super().__init__(master, bg=COLORES["panel"], height=44)
        self._proyecto = tk.StringVar(value="Proyecto: —")
        self._perfil = tk.StringVar(value="perfil: —")
        self._estado = tk.StringVar(value="")
        tk.Label(self, textvariable=self._proyecto, bg=COLORES["panel"],
                 fg=COLORES["texto"], font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)
        tk.Label(self, textvariable=self._perfil, bg=COLORES["panel"],
                 fg=COLORES["texto_tenue"], font=("Segoe UI", 9)).pack(side="left")
        BotonAccion(self, "Cargar Excel", on_cargar).pack(side="right", padx=12, pady=6)
        tk.Label(self, textvariable=self._estado, bg=COLORES["panel"],
                 fg=COLORES["ok"], font=("Segoe UI", 9)).pack(side="right", padx=8)

    def set_info(self, proyecto: str, perfil: str, estado: str) -> None:
        self._proyecto.set(f"Proyecto: {proyecto}")
        self._perfil.set(f"perfil: {perfil}")
        self._estado.set(estado)

    def texto_proyecto(self) -> str:
        return self._proyecto.get()
```

- [ ] **Step 4: Correr → PASS/skip**

Run: `python -m pytest tests/test_gui_componentes.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui/componentes.py tests/test_gui_componentes.py
git commit -m "feat(gui): RielFases (7 fases con badges) + BarraSuperior

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: PanelModulo — anatomía uniforme

**Files:**
- Modify: `gui/componentes.py`
- Test: `tests/test_gui_componentes.py`

- [ ] **Step 1: Escribir smoke**

Añadir a `tests/test_gui_componentes.py`:
```python
@requiere_display
def test_panel_modulo_render_y_calcular():
    import tkinter as tk
    from gui.componentes import PanelModulo
    from gui_core.fases import buscar_modulo
    from gui_core.sesion import SesionProyecto
    root = tk.Tk(); root.withdraw()
    try:
        s = SesionProyecto(circuitos=[{"nombre": "C1", "sistema": "3F", "conductor": "6AWG",
            "S_mm2": 13.3, "I_max": 65, "paralelos": 1, "I_diseno": 40, "cos_phi": 0.9,
            "L_m": 15, "temp_amb": 30}])
        llamado = []
        panel = PanelModulo(root, buscar_modulo("dv"), s, on_calcular=lambda mid: llamado.append(mid))
        assert "Caída de tensión" in panel.titulo_texto()
        assert "NCh" in panel.norma_texto()
        panel.boton.invoke()   # dispara on_calcular
        assert llamado == ["dv"]
    finally:
        root.destroy()
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_componentes.py -q`

- [ ] **Step 3: Implementar (añadir a `gui/componentes.py`)**

```python
from gui_core.fases import estado_modulo


class PanelModulo(tk.Frame):
    """Anatomía uniforme: encabezado+norma+badge, aplicabilidad, acción, resultados."""

    def __init__(self, master, modulo, sesion, on_calcular):
        super().__init__(master, bg=COLORES["fondo"], padx=16, pady=12)
        self.modulo = modulo
        self.sesion = sesion

        cab = tk.Frame(self, bg=COLORES["fondo"]); cab.pack(fill="x")
        self._titulo = tk.Label(cab, text=modulo.nombre, bg=COLORES["fondo"],
                                fg=COLORES["texto"], font=("Segoe UI", 13, "bold"))
        self._titulo.pack(side="left")
        self._norma = tk.Label(cab, text=modulo.norma, bg=COLORES["fondo"],
                               fg=COLORES["texto_tenue"], font=("Segoe UI", 9))
        self._norma.pack(side="left", padx=10)
        self.badge = BadgeEstado(cab, estado_modulo(modulo, sesion))
        self.badge.configure(bg=COLORES["fondo"])
        self.badge.pack(side="right")

        tk.Label(self, text=f"Requiere: {modulo.requiere}", bg=COLORES["fondo"],
                 fg=COLORES["texto_tenue"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 8))

        self.boton = BotonAccion(self, "Calcular", lambda: on_calcular(modulo.id))
        self.boton.pack(anchor="w")
        prereq_ok = modulo.prereq(sesion)
        self.boton.set_habilitado(prereq_ok)

        self.contenedor_resultados = tk.Frame(self, bg=COLORES["fondo"])
        self.contenedor_resultados.pack(fill="both", expand=True, pady=(10, 0))

    def titulo_texto(self) -> str:
        return self._titulo.cget("text")

    def norma_texto(self) -> str:
        return self._norma.cget("text")

    def refrescar_estado(self) -> None:
        self.badge.set_estado(estado_modulo(self.modulo, self.sesion))
        self.badge.configure(bg=COLORES["fondo"])
        self.boton.set_habilitado(self.modulo.prereq(self.sesion))

    def mostrar_tabla(self, columnas: list[str], filas: list[list]) -> None:
        for w in self.contenedor_resultados.winfo_children():
            w.destroy()
        tabla = TablaResultados(self.contenedor_resultados, columnas)
        tabla.configure(bg=COLORES["fondo"])
        tabla.set_filas(filas)
        tabla.pack(fill="both", expand=True)
```

- [ ] **Step 4: Correr → PASS/skip**

Run: `python -m pytest tests/test_gui_componentes.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui/componentes.py tests/test_gui_componentes.py
git commit -m "feat(gui): PanelModulo con anatomía uniforme (encabezado/norma/badge/acción/resultados)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Cargador Excel → SesionProyecto

**Files:**
- Create: `gui/cargador.py`
- Test: `tests/test_gui_cargador.py`

- [ ] **Step 1: Escribir test (sin display)**

`tests/test_gui_cargador.py`:
```python
from pathlib import Path
from gui.cargador import cargar_excel_a_sesion
from gui_core.sesion import SesionProyecto

LIBRO = Path(__file__).resolve().parents[1] / "circuitos.xlsx"


def test_cargar_excel_puebla_sesion():
    assert LIBRO.exists()
    s = SesionProyecto()
    resumen = cargar_excel_a_sesion(str(LIBRO), s)
    assert s.tiene_circuitos
    assert isinstance(resumen, dict) and "hojas" in resumen
    assert resumen["hojas"] >= 1


def test_cargar_excel_inexistente_no_crashea():
    s = SesionProyecto()
    resumen = cargar_excel_a_sesion("no-existe.xlsx", s)
    assert resumen["error"]
    assert not s.tiene_circuitos
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_cargador.py -q`

- [ ] **Step 3: Implementar `gui/cargador.py`**

```python
"""Carga un libro Excel a una SesionProyecto usando los lectores de excel.py."""
from __future__ import annotations

import openpyxl

import excel
from conductores import TENSION_SISTEMA
from transformador import calcular_icc_transformador, icc_desde_tabla
from gui_core.sesion import SesionProyecto


def cargar_excel_a_sesion(ruta: str, sesion: SesionProyecto) -> dict:
    """Lee todas las hojas soportadas y las carga en la sesión.

    Retorna un resumen {"hojas": int, "error": str|None}. Nunca crashea.
    """
    try:
        circuitos = excel.leer_circuitos_excel(ruta)
    except Exception as e:
        return {"hojas": 0, "error": str(e)}

    try:
        libro = openpyxl.load_workbook(ruta, data_only=True)
    except Exception as e:
        return {"hojas": 0, "error": str(e)}

    trafo = excel.leer_transformador_excel(ruta)
    datos = {
        "circuitos": circuitos,
        "trafo": trafo,
        "protecciones": excel.leer_protecciones_excel(libro) or {},
        "cadena": excel.leer_cadena_excel(libro) or [],
        "balance_datos": excel.leer_balance_excel(libro) or {},
        "tableros": excel.leer_tableros_excel(libro) or {},
        "params_demanda": excel.leer_demanda_excel(libro) or {},
        "generador": excel.leer_generador_excel(libro),
        "ups": excel.leer_ups_excel(libro),
        "sts": excel.leer_sts_excel(libro),
        "ats": excel.leer_ats_excel(libro),
        "trafo_iso": excel.leer_trafo_iso_excel(libro),
    }
    perfil = excel.leer_perfil_excel(libro) or {}
    datos["proyecto"] = perfil.get("nombre_proyecto", "PROYECTO")
    datos["perfil"] = perfil.get("perfil", "industrial")

    # Impedancia y tensión de barra para el flujo nodal (derivadas del trafo).
    if trafo:
        vn = float(trafo.get("Vn_BT", 380))
        datos["tension_sistema_v"] = vn
        if str(trafo.get("modo", "B")).upper() == "A":
            _, zt, _ = calcular_icc_transformador(trafo["kVA"], vn, trafo["Ucc_pct"])
        else:
            icc, ucc, _ = icc_desde_tabla(trafo["kVA"])
            zt = (ucc / 100.0) * (vn ** 2 / (trafo["kVA"] * 1000.0))
        datos["trafo_z_ohm"] = float(zt)

    sesion.cargar({k: v for k, v in datos.items() if v is not None})
    hojas = sum(1 for k in ("circuitos", "trafo", "protecciones", "cadena", "tableros")
                if getattr(sesion, k, None))
    return {"hojas": hojas, "error": None}
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_gui_cargador.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add gui/cargador.py tests/test_gui_cargador.py
git commit -m "feat(gui): cargador Excel → SesionProyecto (todas las hojas, sin crash)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Presentadores fase 5-6 (emergencia + reporte)

**Files:**
- Modify: `gui_core/presentadores.py`, `gui_core/fases.py`
- Test: `tests/test_gui_core_presentadores_emergencia.py`

- [ ] **Step 1: Verificar firmas de motor**

Run: `python -c "import inspect, generador, ats, ups, sts, trafo_iso, reporteria_sec as r; print(inspect.signature(reporteria_sec.exportar_json_epc) if hasattr(reporteria_sec,'exportar_json_epc') else '')" 2>/dev/null; python -c "import inspect,reporteria_sec; print('epc', inspect.signature(reporteria_sec.exportar_json_epc)); print('docx', inspect.signature(reporteria_sec.generar_memoria_docx))"`
Expected: firmas de `exportar_json_epc(datos_run, ruta_salida, modo_emision='auto', circuitos=None)` y `generar_memoria_docx(datos_run, circuitos, ruta_salida)`.

- [ ] **Step 2: Escribir tests (sin display)**

`tests/test_gui_core_presentadores_emergencia.py`:
```python
from gui_core.sesion import SesionProyecto
from gui_core.presentadores import presentar_reporte


def test_presentar_reporte_sin_calculos_indica_gate():
    s = SesionProyecto()
    r = presentar_reporte(s)
    assert "apto_emision" in r
    assert isinstance(r["alertas"], list)


def test_presentar_reporte_con_datos_minimos(tmp_path):
    s = SesionProyecto()
    s.cargar({
        "proyecto": "T", "perfil": "industrial",
        "circuitos": [{"nombre": "C-01", "conductor": "6AWG", "S_mm2": 13.3,
                       "I_diseno": 40.0, "I_max": 65.0, "cos_phi": 0.9, "L_m": 15.0,
                       "paralelos": 1, "sistema": "3F", "dv_pct": 0.3, "icc_ka": 10.0,
                       "estado": "OK", "norma": "MM2"}],
    })
    r = presentar_reporte(s, carpeta_salida=str(tmp_path))
    assert r["ruta_docx"].endswith(".docx")
```

- [ ] **Step 3: Correr → FAIL**

Run: `python -m pytest tests/test_gui_core_presentadores_emergencia.py -q`

- [ ] **Step 4: Implementar (añadir a `gui_core/presentadores.py`)**

```python
import os
from reporteria_sec import (
    generar_memoria_docx, generar_reporte_pdf,
    exportar_json_epc, verificar_completitud_parametros,
)


def _datos_run(sesion: SesionProyecto) -> dict:
    return {
        "project_id": sesion.proyecto or "PROYECTO",
        "revision": "GUI",
        "perfil": sesion.perfil or "industrial",
        "norma": "MM2",
        "n_circuitos": len(sesion.circuitos),
        "status": "OK",
        "cadena": sesion.cadena,
        "trafo_z_ohm": sesion.trafo_z_ohm,
        "tension_sistema_v": sesion.tension_sistema_v,
    }


def presentar_reporte(sesion: SesionProyecto, carpeta_salida: str | None = None) -> dict:
    """Genera memoria DOCX/PDF/JSON EPC + gate de completitud."""
    carpeta = carpeta_salida or os.getcwd()
    datos = _datos_run(sesion)
    circuitos = sesion.circuitos
    gate = verificar_completitud_parametros(datos)
    alertas = [] if gate.get("apto_emision") else ["parámetros TIPO-A en default"]
    salida = {"apto_emision": gate.get("apto_emision", False),
              "nivel": gate.get("nivel", "INCOMPLETO"), "alertas": alertas,
              "ruta_docx": "", "ruta_pdf": "", "ruta_json": ""}
    if not circuitos:
        return salida
    try:
        salida["ruta_docx"] = generar_memoria_docx(datos, circuitos, carpeta)
        salida["ruta_pdf"] = generar_reporte_pdf(datos, circuitos, carpeta)
        salida["ruta_json"] = exportar_json_epc(datos, carpeta, circuitos=circuitos)
    except Exception as e:  # la generación no debe tumbar la GUI
        salida["alertas"].append(f"error de generación: {e}")
    return salida
```

Nota: los módulos de emergencia (generador/ats/ups/sts/trafo_iso/arranque) ya tienen estado en el registro; sus presentadores de detalle se implementan como panel-específicos en una iteración posterior. Para esta entrega, la fase 5 muestra estado y la fase 6 genera el reporte que consolida todo. Añadir a `PRESENTADOR` en `fases.py`:
```python
    "reporte": _p.presentar_reporte,
```

- [ ] **Step 5: Correr → PASS**

Run: `python -m pytest tests/test_gui_core_presentadores_emergencia.py -q`

- [ ] **Step 6: Commit**

```bash
git add gui_core/presentadores.py gui_core/fases.py tests/test_gui_core_presentadores_emergencia.py
git commit -m "feat(gui_core): presentador de reporte (fase 6) + gate de completitud

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Shell `AppBT` — ensamblado y wiring

**Files:**
- Create: `gui/app.py`
- Test: `tests/test_gui_app.py`

- [ ] **Step 1: Escribir smoke (headless-skip)**

`tests/test_gui_app.py`:
```python
import pytest
from gui.headless import hay_display

requiere_display = pytest.mark.skipif(not hay_display(), reason="sin display (headless)")


@requiere_display
def test_app_arranca_y_selecciona_fase():
    from gui.app import AppBT
    app = AppBT()
    app.withdraw()
    try:
        assert app.sesion is not None
        app.mostrar_fase(1)                     # cálculo base
        assert app.fase_actual == 1
        assert len(app.paneles_actuales) >= 1   # ΔV, capacidad, sugerencia
    finally:
        app.destroy()


@requiere_display
def test_app_calcular_registra_y_refresca():
    from gui.app import AppBT
    app = AppBT()
    app.withdraw()
    try:
        app.sesion.cargar({"circuitos": [{"nombre": "C1", "sistema": "3F",
            "conductor": "6AWG", "S_mm2": 13.3, "I_max": 65, "paralelos": 1,
            "I_diseno": 40, "cos_phi": 0.9, "L_m": 15, "temp_amb": 30}]})
        app.mostrar_fase(1)
        app.ejecutar_modulo("dv")               # llama presentador + registrar
        assert "dv" in app.sesion.resultados
    finally:
        app.destroy()


def test_app_importable_sin_display():
    import gui.app          # importar no debe crear ventanas
    assert hasattr(gui.app, "AppBT")
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_app.py -q`

- [ ] **Step 3: Implementar `gui/app.py`**

```python
"""Ventana principal de la GUI por fases (Tokyo Night) sobre gui_core."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog

from gui_core.estado import COLORES
from gui_core.fases import modulos_de_fase, PRESENTADOR
from gui_core.sesion import SesionProyecto
from gui.componentes import BarraSuperior, RielFases, PanelModulo
from gui.cargador import cargar_excel_a_sesion

# Columnas de la tabla de resultados por módulo (id → (columnas, extractor de fila)).
_COLUMNAS = {
    "dv": (["Circuito", "ΔV (V)", "ΔV (%)", "Estado"],
           lambda f: [f["nombre"], f["dv_v"], f["dv_pct"], f["estado"]]),
    "capacidad": (["Circuito", "I diseño", "Cap (A)", "OK"],
                  lambda f: [f["nombre"], f["I_diseno"], f["cap_A"], f["ok"]]),
    "icc_punto": (["Circuito", "Icc (kA)", "Zt total"],
                  lambda f: [f["nombre"], f["Icc_kA"], f["Zt_total"]]),
    "arc_flash": (["Circuito", "E (cal/cm²)", "Frontera (mm)", "Cat EPP"],
                  lambda f: [f["nombre"], f["E_cal_cm2"], f["D_afb_mm"], f["categoria_ppe"]]),
    "protecciones": (["Circuito", "Estado", "Icc (kA)"],
                     lambda f: [f["nombre"], f["estado"], f["Icc_kA"]]),
    "coordinacion": (["Dispositivo", "t (s)", "Región"],
                     lambda f: [f["nombre"], f["t_s"], f["region"]]),
    "sugerencia": (["Circuito", "Sugerido", "Cap (A)", "ΔV (%)"],
                   lambda f: [f["nombre"], f["sugerido"], f["cap_A"], f["dv_pct"]]),
    "aporte_motores": (["Motor", "P (kW)", "Aporte (A)"],
                       lambda f: [f["nombre"], f["P_kW"], f["I_aporte_A"]]),
}


class AppBT(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Motor de Cálculo BT")
        self.configure(bg=COLORES["fondo"])
        self.geometry("1000x640")
        self.sesion = SesionProyecto()
        self.fase_actual = 0
        self.paneles_actuales: list[PanelModulo] = []

        self.barra = BarraSuperior(self, on_cargar=self._cargar_excel)
        self.barra.pack(fill="x")
        cuerpo = tk.Frame(self, bg=COLORES["fondo"]); cuerpo.pack(fill="both", expand=True)
        self.riel = RielFases(cuerpo, self.sesion, on_seleccion=self.mostrar_fase)
        self.riel.pack(side="left", fill="y")
        self.area = tk.Frame(cuerpo, bg=COLORES["fondo"]); self.area.pack(side="right", fill="both", expand=True)
        self.mostrar_fase(0)

    def _cargar_excel(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not ruta:
            return
        resumen = cargar_excel_a_sesion(ruta, self.sesion)
        estado = f"{resumen['hojas']} hojas" if not resumen["error"] else "error de carga"
        self.barra.set_info(self.sesion.proyecto, self.sesion.perfil, estado)
        self.riel.refrescar()
        self.mostrar_fase(self.fase_actual)

    def mostrar_fase(self, fase: int):
        self.fase_actual = fase
        for w in self.area.winfo_children():
            w.destroy()
        self.paneles_actuales = []
        for m in modulos_de_fase(fase):
            panel = PanelModulo(self.area, m, self.sesion, on_calcular=self.ejecutar_modulo)
            panel.pack(fill="x", pady=6)
            self.paneles_actuales.append(panel)

    def ejecutar_modulo(self, modulo_id: str):
        fn = PRESENTADOR.get(modulo_id)
        if fn is None:
            return
        resultado = fn(self.sesion)
        self.sesion.registrar(modulo_id, resultado, resultado.get("alertas", []))
        # refrescar tabla del panel + badges
        cols = _COLUMNAS.get(modulo_id)
        for panel in self.paneles_actuales:
            if panel.modulo.id == modulo_id and cols and "filas" in resultado:
                columnas, extractor = cols
                panel.mostrar_tabla(columnas, [extractor(f) for f in resultado["filas"]])
            panel.refrescar_estado()
        self.riel.refrescar()


def main():
    AppBT().mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr → PASS/skip**

Run: `python -m pytest tests/test_gui_app.py -q`
Expected: `test_app_importable_sin_display` PASS; los `@requiere_display` PASS con display o skip en headless.

- [ ] **Step 5: Commit**

```bash
git add gui/app.py tests/test_gui_app.py
git commit -m "feat(gui): shell AppBT — riel de fases + paneles + wiring calcular/registrar/refrescar

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Lanzador `gui.py` + retiro de sub-ventanas + regresión

**Files:**
- Rewrite: `gui.py` (lanzador delgado)
- Delete: `gui/arranque_window.py`, `gui/emergencia_window.py`, `gui/guiada_window.py`, `gui/reporte_window.py` (y sus tests si existen)
- Test: regresión completa

- [ ] **Step 1: Localizar tests que dependen de las sub-ventanas**

Run: `grep -rln "arranque_window\|emergencia_window\|guiada_window\|reporte_window\|MotorCalculoBT" tests/ gui.py`
Expected: lista de archivos a actualizar/eliminar. Confirmar cuáles tests son de las viejas ventanas.

- [ ] **Step 2: Reescribir `gui.py` como lanzador delgado**

Reemplazar TODO el contenido de `gui.py` por:
```python
"""Lanzador de la GUI del Motor de Cálculo BT (rediseño por fases)."""
from gui.app import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Eliminar sub-ventanas obsoletas y sus tests**

```bash
git rm gui/arranque_window.py gui/emergencia_window.py gui/guiada_window.py gui/reporte_window.py
```
Eliminar también los tests que importan esas ventanas o `MotorCalculoBT` (identificados en Step 1) con `git rm`. Si `src/arranque_motores.py`, `src/sistemas_emergencia.py`, `src/generador_memoria.py` quedaban SOLO usados por esas ventanas, verificar con grep si algún otro módulo los usa; si no, dejarlos (no es alcance de este plan eliminarlos — solo la capa de ventanas).

- [ ] **Step 4: Verificar arranque e importable**

Run: `python -c "import ast; ast.parse(open('gui.py',encoding='utf-8-sig').read()); import gui.app; print('gui ok')"`
Expected: `gui ok`.

- [ ] **Step 5: Suite completa**

Run: `python -m pytest tests/ -q`
Expected: verde (con skips headless). Los tests de las viejas ventanas ya no existen; los nuevos de gui/ pasan o se saltan según display.

- [ ] **Step 6: Actualizar `motor_bt.spec` si referencia symbols viejos**

Run: `grep -n "MotorCalculoBT\|arranque_window\|emergencia_window\|guiada_window\|reporte_window" motor_bt.spec`
Si aparece algo, actualizarlo (el entry sigue siendo `gui.py`, que ahora lanza `gui.app`); si no aparece nada, no tocar el spec.

- [ ] **Step 7: Commit**

```bash
git add gui.py motor_bt.spec
git commit -m "feat(gui): gui.py como lanzador de AppBT; retirar sub-ventanas Toplevel

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas para el ejecutor

- **`gui_core/` no cambia su regla:** sin tkinter. `gui/` importa `gui_core`, nunca al revés.
- **Testabilidad:** los widgets se prueban con smokes marcados `@requiere_display` (se saltan en CI headless); la lógica ya está cubierta en `gui_core` (Plan 1). Cada módulo de `gui/` debe ser **importable sin display** (no crear `Tk()` a nivel de módulo).
- **Colores:** SIEMPRE desde `gui_core.estado.COLORES`. No hardcodear hex en `gui/`.
- **Alcance de fase 5 (emergencia):** en esta entrega la fase 5 muestra estado de sus módulos y el reporte (fase 6) consolida; los paneles de detalle de generador/ats/ups/sts/arranque con sus parámetros de entrada son una iteración posterior (el registro ya los declara).
- **Bug conocido:** el `gui.py` viejo tenía `undefined name 'e'` (línea ~1034); al reescribir `gui.py` como lanzador delgado, ese código desaparece — verificar con pyflakes que `gui.py` y `gui/` quedan limpios: `python -m pyflakes gui.py gui/*.py`.
- Suite completa verde tras cada tarea (con skips headless esperados).
```
