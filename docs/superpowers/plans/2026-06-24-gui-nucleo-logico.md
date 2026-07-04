# GUI — Núcleo lógico (`gui_core/`) — Plan de implementación (Plan 1 de 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el núcleo lógico de la GUI rediseñada —estado de sesión, paleta, registro de fases/módulos, derivación de estado y presentadores— 100% testeable sin abrir ventanas Tkinter.

**Architecture:** Paquete nuevo `gui_core/` sin dependencias de Tkinter. `SesionProyecto` guarda datos cargados + resultados; un registro declarativo de 7 fases y ~18 módulos define prerrequisitos y norma; funciones puras derivan el estado (sin datos/listo/calculado/alerta); los presentadores orquestan los motores existentes y devuelven resultados estructurados + alertas. La capa visual (Plan 2) consumirá este núcleo.

**Tech Stack:** Python 3.13, dataclasses, enum, pytest. Sin Tkinter, sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-06-24-gui-rediseno-fases-tokyo-night-design.md`

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `gui_core/__init__.py` | marca de paquete |
| `gui_core/estado.py` | paleta Tokyo Night `COLORES` + enum `Estado` + `color_de_estado` |
| `gui_core/sesion.py` | `SesionProyecto` (datos + resultados + flags derivados) |
| `gui_core/fases.py` | `Modulo`, registro `MODULOS`, `FASES`, `estado_modulo`, `estado_fase` |
| `gui_core/presentadores.py` | presentadores por módulo (orquestan motores → resultado+alertas) |
| `tests/test_gui_core_estado.py` | paleta + enum |
| `tests/test_gui_core_sesion.py` | flags de sesión |
| `tests/test_gui_core_fases.py` | registro + derivación de estado |
| `tests/test_gui_core_presentadores.py` | presentadores contra motores reales |

Regla: `gui_core/` **no importa `tkinter`**. Solo importa los módulos de motor (`calculos`, `transformador`, `icc_punto`, `protecciones`, `balance`, `demanda`, `arc_flash`, `coordinacion`, `red_desde_cadena`, `flujo_nodal`, `generador`, `ats`, `ups`, `sts`, `trafo_iso`, `motores`).

---

## Task 1: Paleta Tokyo Night + enum Estado

**Files:**
- Create: `gui_core/__init__.py` (vacío)
- Create: `gui_core/estado.py`
- Test: `tests/test_gui_core_estado.py`

- [ ] **Step 1: Test que falla**

```python
from gui_core.estado import COLORES, Estado, color_de_estado


def test_paleta_tokyo_night_hexes():
    assert COLORES["fondo"] == "#1a1b26"
    assert COLORES["acento"] == "#7aa2f7"
    assert COLORES["ok"] == "#9ece6a"
    assert COLORES["alerta"] == "#f7768e"
    assert COLORES["precaucion"] == "#ff9e64"

def test_estados_existen():
    assert {e.value for e in Estado} == {"sin_datos", "listo", "calculado", "alerta"}

def test_color_de_estado():
    assert color_de_estado(Estado.CALCULADO) == COLORES["ok"]
    assert color_de_estado(Estado.ALERTA) == COLORES["alerta"]
    assert color_de_estado(Estado.LISTO) == COLORES["acento"]
    assert color_de_estado(Estado.SIN_DATOS) == COLORES["texto_tenue"]
```

- [ ] **Step 2: Correr → FAIL** (`ModuleNotFoundError: gui_core`)

Run: `python -m pytest tests/test_gui_core_estado.py -q`

- [ ] **Step 3: Implementar**

`gui_core/__init__.py`: archivo vacío.

`gui_core/estado.py`:
```python
"""Paleta Tokyo Night y estados de módulo para la GUI."""
from __future__ import annotations

from enum import Enum

COLORES = {
    "fondo":        "#1a1b26",
    "panel":        "#16161e",
    "seleccion":    "#292e42",
    "borde":        "#3b4261",
    "texto":        "#c0caf5",
    "texto_tenue":  "#565f89",
    "acento":       "#7aa2f7",
    "ok":           "#9ece6a",
    "alerta":       "#f7768e",
    "precaucion":   "#ff9e64",
    "amarillo":     "#e0af68",
    "violeta":      "#bb9af7",
}


class Estado(Enum):
    SIN_DATOS = "sin_datos"
    LISTO = "listo"
    CALCULADO = "calculado"
    ALERTA = "alerta"


_COLOR = {
    Estado.SIN_DATOS: COLORES["texto_tenue"],
    Estado.LISTO:     COLORES["acento"],
    Estado.CALCULADO: COLORES["ok"],
    Estado.ALERTA:    COLORES["alerta"],
}


def color_de_estado(estado: Estado) -> str:
    return _COLOR[estado]
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_gui_core_estado.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui_core/__init__.py gui_core/estado.py tests/test_gui_core_estado.py
git commit -m "feat(gui_core): paleta Tokyo Night + enum Estado

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: `SesionProyecto` — contenedor de datos y flags

**Files:**
- Create: `gui_core/sesion.py`
- Test: `tests/test_gui_core_sesion.py`

- [ ] **Step 1: Test que falla**

```python
from gui_core.sesion import SesionProyecto


def test_sesion_vacia_flags_false():
    s = SesionProyecto()
    assert s.tiene_circuitos is False
    assert s.tiene_trafo is False
    assert s.tiene_cadena is False
    assert s.tiene_protecciones is False

def test_cargar_setea_flags():
    s = SesionProyecto()
    s.cargar({
        "circuitos": [{"nombre": "C1"}],
        "trafo": {"modo": "A", "kVA": 1000},
        "protecciones": {"C1": {"In_A": 100, "curva": "C"}},
        "cadena": [{"nombre": "G0"}],
        "proyecto": "P", "perfil": "industrial",
    })
    assert s.tiene_circuitos and s.tiene_trafo
    assert s.tiene_protecciones and s.tiene_cadena
    assert s.proyecto == "P" and s.perfil == "industrial"

def test_cargar_ignora_claves_desconocidas():
    s = SesionProyecto()
    s.cargar({"basura": 123, "circuitos": [{"nombre": "C1"}]})
    assert s.tiene_circuitos
    assert not hasattr(s, "basura")

def test_registrar_resultado():
    s = SesionProyecto()
    s.registrar("dv", {"filas": [1, 2]}, alertas=["C1"])
    assert s.resultados["dv"]["alertas"] == ["C1"]
    assert s.resultados["dv"]["resultado"] == {"filas": [1, 2]}
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_core_sesion.py -q`

- [ ] **Step 3: Implementar `gui_core/sesion.py`**

```python
"""Estado de sesión del proyecto: única fuente de verdad de la GUI."""
from __future__ import annotations

from dataclasses import dataclass, field

# Claves de datos que la sesión acepta desde el cargador Excel.
_CLAVES_DATOS = (
    "circuitos", "trafo", "protecciones", "cadena", "balance_datos",
    "tableros", "params_demanda", "generador", "ups", "sts", "ats",
    "trafo_iso", "proyecto", "perfil", "trafo_z_ohm", "tension_sistema_v",
)


@dataclass
class SesionProyecto:
    circuitos: list = field(default_factory=list)
    trafo: dict | None = None
    protecciones: dict = field(default_factory=dict)
    cadena: list = field(default_factory=list)
    balance_datos: dict = field(default_factory=dict)
    tableros: dict = field(default_factory=dict)
    params_demanda: dict = field(default_factory=dict)
    generador: dict | None = None
    ups: dict | None = None
    sts: dict | None = None
    ats: dict | None = None
    trafo_iso: dict | None = None
    proyecto: str = ""
    perfil: str = ""
    trafo_z_ohm: float = 0.0
    tension_sistema_v: float = 380.0
    resultados: dict = field(default_factory=dict)

    def cargar(self, datos: dict) -> None:
        """Fusiona datos cargados (Excel). Ignora claves desconocidas."""
        for clave in _CLAVES_DATOS:
            if clave in datos and datos[clave] is not None:
                setattr(self, clave, datos[clave])

    def registrar(self, modulo_id: str, resultado, alertas: list | None = None) -> None:
        """Guarda el resultado de un módulo y sus alertas (para derivar estado)."""
        self.resultados[modulo_id] = {"resultado": resultado, "alertas": list(alertas or [])}

    @property
    def tiene_circuitos(self) -> bool:
        return bool(self.circuitos)

    @property
    def tiene_trafo(self) -> bool:
        return self.trafo is not None

    @property
    def tiene_protecciones(self) -> bool:
        return bool(self.protecciones)

    @property
    def tiene_cadena(self) -> bool:
        return bool(self.cadena)

    @property
    def tiene_icc(self) -> bool:
        return "icc_punto" in self.resultados
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_gui_core_sesion.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui_core/sesion.py tests/test_gui_core_sesion.py
git commit -m "feat(gui_core): SesionProyecto con datos, resultados y flags derivados

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Registro de fases/módulos + derivación de estado

**Files:**
- Create: `gui_core/fases.py`
- Test: `tests/test_gui_core_fases.py`

- [ ] **Step 1: Test que falla**

```python
from gui_core.sesion import SesionProyecto
from gui_core.estado import Estado
from gui_core.fases import FASES, MODULOS, modulos_de_fase, estado_modulo, estado_fase, buscar_modulo


def test_siete_fases():
    assert set(FASES.keys()) == {0, 1, 2, 3, 4, 5, 6}

def test_cada_modulo_tiene_fase_valida():
    for m in MODULOS:
        assert m.fase in FASES
        assert m.nombre and m.norma is not None

def test_modulo_arc_flash_en_fase_3():
    af = buscar_modulo("arc_flash")
    assert af is not None and af.fase == 3

def test_estado_sin_datos_cuando_faltan_prereqs():
    s = SesionProyecto()  # vacía
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.SIN_DATOS

def test_estado_listo_cuando_prereqs_ok_sin_resultado():
    s = SesionProyecto(circuitos=[{"nombre": "C1"}])
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.LISTO

def test_estado_calculado_y_alerta():
    s = SesionProyecto(circuitos=[{"nombre": "C1"}])
    s.registrar("dv", {"filas": []}, alertas=[])
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.CALCULADO
    s.registrar("dv", {"filas": []}, alertas=["C1"])
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.ALERTA

def test_estado_fase_es_el_peor_de_sus_modulos():
    s = SesionProyecto(circuitos=[{"nombre": "C1"}])
    s.registrar("dv", {}, alertas=["C1"])   # alerta
    # fase 1 debe reportar ALERTA aunque otros módulos estén en LISTO
    assert estado_fase(1, s) == Estado.ALERTA

def test_modulos_de_fase_no_vacio():
    for n in FASES:
        assert isinstance(modulos_de_fase(n), list)
    assert len(modulos_de_fase(3)) >= 3  # protecciones, coordinación, arc flash...
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_core_fases.py -q`

- [ ] **Step 3: Implementar `gui_core/fases.py`**

```python
"""Registro declarativo de fases y módulos + derivación de estado."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from gui_core.estado import Estado
from gui_core.sesion import SesionProyecto

FASES = {
    0: "Datos",
    1: "Cálculo base",
    2: "Cortocircuito",
    3: "Protección",
    4: "Carga y red",
    5: "Emergencia",
    6: "Reporte",
}


@dataclass(frozen=True)
class Modulo:
    id: str
    nombre: str
    norma: str
    fase: int
    requiere: str                      # etiqueta humana del prerrequisito
    prereq: Callable[[SesionProyecto], bool]


MODULOS: list[Modulo] = [
    # Fase 1 — cálculo base
    Modulo("dv", "Caída de tensión ΔV", "NCh Elec 4/2003 · IEC 60364", 1,
           "circuitos", lambda s: s.tiene_circuitos),
    Modulo("capacidad", "Capacidad de conductor", "IEC 60364-5-52", 1,
           "circuitos", lambda s: s.tiene_circuitos),
    Modulo("sugerencia", "Sugerencia de sección", "SEC RIC N°04", 1,
           "circuitos", lambda s: s.tiene_circuitos),
    # Fase 2 — cortocircuito
    Modulo("icc_trafo", "Icc bornes transformador", "IEC 60909 · IEC 60076", 2,
           "transformador", lambda s: s.tiene_trafo),
    Modulo("icc_punto", "Icc por punto + fase-neutro", "IEC 60909-2 · IEC 60364-4-41", 2,
           "trafo + circuitos", lambda s: s.tiene_trafo and s.tiene_circuitos),
    Modulo("aporte_motores", "Aporte de motores al Icc", "IEC 60909-4:2021", 2,
           "Icc + circuitos", lambda s: s.tiene_icc and s.tiene_circuitos),
    # Fase 3 — protección
    Modulo("protecciones", "Verificación de protecciones", "IEC 60947-2 · IEC 60364-4-41", 3,
           "Icc + protecciones", lambda s: s.tiene_icc and s.tiene_protecciones),
    Modulo("coordinacion", "Coordinación TCC / selectividad", "IEC 60947-2 (M7)", 3,
           "cadena", lambda s: s.tiene_cadena),
    Modulo("arc_flash", "Arc Flash", "IEEE 1584-2002 · NFPA 70E", 3,
           "Icc + protección", lambda s: s.tiene_icc and s.tiene_protecciones),
    # Fase 4 — carga y red
    Modulo("balance", "Balance por tablero", "NCh Elec 4/2003", 4,
           "circuitos + tableros", lambda s: s.tiene_circuitos and bool(s.tableros)),
    Modulo("demanda", "Demanda máxima (M6)", "RIC N°03 SEC · IEC 60076", 4,
           "circuitos", lambda s: s.tiene_circuitos),
    Modulo("flujo_nodal", "Flujo de carga nodal", "IEEE 399 · IEC 60909", 4,
           "cadena + trafo", lambda s: s.tiene_cadena and s.trafo_z_ohm > 0),
    # Fase 5 — emergencia
    Modulo("generador", "Grupo electrógeno + ATS + autonomía", "RIC N°08 SEC · ISO 8528", 5,
           "demanda/cargas", lambda s: s.generador is not None or s.tiene_circuitos),
    Modulo("trafo_iso", "Transformador de aislamiento", "IEC 61558 · IEEE C57.110", 5,
           "cargas", lambda s: s.trafo_iso is not None),
    Modulo("ups", "UPS", "IEC 62040", 5,
           "cargas críticas", lambda s: s.ups is not None),
    Modulo("sts", "STS", "IEC 62310", 5,
           "cargas", lambda s: s.sts is not None),
    Modulo("arranque", "Arranque de motores", "IEC 60947-4-1", 5,
           "motores", lambda s: s.tiene_circuitos),
    # Fase 6 — reporte
    Modulo("reporte", "Memoria SEC (DOCX/PDF/JSON EPC)", "SEC RIC", 6,
           "cálculos hechos", lambda s: bool(s.resultados)),
]

_INDICE = {m.id: m for m in MODULOS}
_PRIORIDAD = {Estado.ALERTA: 3, Estado.CALCULADO: 2, Estado.LISTO: 1, Estado.SIN_DATOS: 0}


def buscar_modulo(modulo_id: str) -> Modulo | None:
    return _INDICE.get(modulo_id)


def modulos_de_fase(fase: int) -> list[Modulo]:
    return [m for m in MODULOS if m.fase == fase]


def estado_modulo(modulo: Modulo, sesion: SesionProyecto) -> Estado:
    if not modulo.prereq(sesion):
        return Estado.SIN_DATOS
    res = sesion.resultados.get(modulo.id)
    if res is None:
        return Estado.LISTO
    return Estado.ALERTA if res.get("alertas") else Estado.CALCULADO


def estado_fase(fase: int, sesion: SesionProyecto) -> Estado:
    """Peor estado entre los módulos de la fase (alerta > calculado > listo > sin datos)."""
    estados = [estado_modulo(m, sesion) for m in modulos_de_fase(fase)]
    if not estados:
        return Estado.SIN_DATOS
    return max(estados, key=lambda e: _PRIORIDAD[e])
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_gui_core_fases.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui_core/fases.py tests/test_gui_core_fases.py
git commit -m "feat(gui_core): registro de 7 fases + ~18 módulos con prereqs y derivación de estado

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Presentadores fase 1-2 (cálculo base + cortocircuito)

**Files:**
- Create: `gui_core/presentadores.py`
- Test: `tests/test_gui_core_presentadores.py`

- [ ] **Step 1: Test que falla**

```python
from gui_core.sesion import SesionProyecto
from gui_core.presentadores import presentar_dv, presentar_icc_trafo, presentar_icc_punto


def _sesion_basica():
    s = SesionProyecto()
    s.cargar({
        "circuitos": [{
            "nombre": "C-01", "sistema": "3F", "conductor": "6AWG", "S_mm2": 13.3,
            "I_max": 65.0, "paralelos": 1, "I_diseno": 40.0, "cos_phi": 0.9,
            "L_m": 15.0, "temp_amb": 30,
        }],
        "trafo": {"modo": "A", "kVA": 1000.0, "Vn_BT": 380.0, "Ucc_pct": 5.0},
    })
    return s


def test_presentar_dv_devuelve_filas_y_estado():
    r = presentar_dv(_sesion_basica())
    assert r["filas"] and "dv_pct" in r["filas"][0]
    assert isinstance(r["alertas"], list)

def test_presentar_dv_marca_alerta_en_falla():
    s = SesionProyecto()
    s.cargar({"circuitos": [{
        "nombre": "LARGO", "sistema": "3F", "conductor": "14AWG", "S_mm2": 2.08,
        "I_max": 25.0, "paralelos": 1, "I_diseno": 24.0, "cos_phi": 0.9,
        "L_m": 300.0, "temp_amb": 30,
    }]})
    r = presentar_dv(s)
    assert r["alertas"]  # caída excesiva → alerta

def test_presentar_icc_trafo():
    r = presentar_icc_trafo(_sesion_basica())
    assert r["Icc_kA"] > 0 and r["Zt_ohm"] > 0

def test_presentar_icc_punto_por_circuito():
    r = presentar_icc_punto(_sesion_basica())
    assert r["filas"] and r["filas"][0]["Icc_kA"] > 0
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_core_presentadores.py -q`

- [ ] **Step 3: Implementar (parte fase 1-2) en `gui_core/presentadores.py`**

```python
"""Presentadores: orquestan los motores existentes desde una SesionProyecto.

Cada presentador devuelve un dict con datos estructurados + 'alertas' (lista).
No importan tkinter. La sesión guarda el resultado vía registrar().
"""
from __future__ import annotations

from calculos import calcular_caida_tension, clasificar_caida, capacidad_corregida
from transformador import calcular_icc_transformador, icc_desde_tabla
from icc_punto import calcular_icc_punto
from conductores import TENSION_SISTEMA
from gui_core.sesion import SesionProyecto


def _zt_trafo(sesion: SesionProyecto) -> float:
    t = sesion.trafo or {}
    if not t:
        return 0.0
    if str(t.get("modo", "B")).upper() == "A":
        _, zt, _ = calcular_icc_transformador(t["kVA"], t["Vn_BT"], t["Ucc_pct"])
    else:
        icc, ucc, _ = icc_desde_tabla(t["kVA"])
        vn = float(t.get("Vn_BT", 380))
        zt = (ucc / 100.0) * (vn ** 2 / (t["kVA"] * 1000.0))
    return float(zt)


def presentar_dv(sesion: SesionProyecto) -> dict:
    filas, alertas = [], []
    for c in sesion.circuitos:
        dv_v, dv_pct = calcular_caida_tension(
            c["L_m"], c["S_mm2"], c["I_diseno"], c["paralelos"], c["sistema"]
        )
        estado = clasificar_caida(dv_pct)
        if str(estado).upper() == "FALLA":
            alertas.append(c["nombre"])
        filas.append({"nombre": c["nombre"], "dv_v": dv_v, "dv_pct": dv_pct, "estado": estado})
    return {"filas": filas, "alertas": alertas}


def presentar_capacidad(sesion: SesionProyecto) -> dict:
    filas, alertas = [], []
    for c in sesion.circuitos:
        cap = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
        ok = c["I_diseno"] <= cap
        if not ok:
            alertas.append(c["nombre"])
        filas.append({"nombre": c["nombre"], "I_diseno": c["I_diseno"], "cap_A": cap, "ok": ok})
    return {"filas": filas, "alertas": alertas}


def presentar_icc_trafo(sesion: SesionProyecto) -> dict:
    t = sesion.trafo or {}
    if str(t.get("modo", "B")).upper() == "A":
        icc, zt, info = calcular_icc_transformador(t["kVA"], t["Vn_BT"], t["Ucc_pct"])
    else:
        icc, ucc, kva_ref = icc_desde_tabla(t["kVA"])
        zt = _zt_trafo(sesion)
    return {"Icc_kA": round(float(icc), 2), "Zt_ohm": round(float(zt), 6), "alertas": []}


def presentar_icc_punto(sesion: SesionProyecto) -> dict:
    zt = _zt_trafo(sesion)
    filas, alertas = [], []
    for c in sesion.circuitos:
        icc, zt_total, zt_cable = calcular_icc_punto(
            zt, c["L_m"], c["S_mm2"], c["paralelos"], c["sistema"]
        )
        filas.append({"nombre": c["nombre"], "Icc_kA": icc, "Zt_total": zt_total})
    return {"filas": filas, "alertas": alertas}
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_gui_core_presentadores.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui_core/presentadores.py tests/test_gui_core_presentadores.py
git commit -m "feat(gui_core): presentadores fase 1-2 (ΔV, capacidad, Icc trafo/punto)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Presentadores fase 3 (protección, coordinación, arc flash)

**Files:**
- Modify: `gui_core/presentadores.py`
- Test: `tests/test_gui_core_presentadores.py`

- [ ] **Step 1: Test que falla** (añadir al archivo de tests)

```python
def test_presentar_arc_flash_por_circuito():
    from gui_core.presentadores import presentar_arc_flash
    s = _sesion_basica()
    s.cargar({"protecciones": {"C-01": {"In_A": 100, "curva": "C"}}})
    # Icc por circuito ya disponible en la sesión (se registra en el flujo real);
    # el presentador recomputa Icc si no está.
    r = presentar_arc_flash(s)
    assert r["filas"] and r["filas"][0]["E_cal_cm2"] > 0
    assert isinstance(r["alertas"], list)

def test_presentar_coordinacion_sin_cadena_vacio():
    from gui_core.presentadores import presentar_coordinacion
    r = presentar_coordinacion(SesionProyecto())
    assert r["filas"] == [] and r["alertas"] == []
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_core_presentadores.py -k "arc_flash or coordinacion" -q`

- [ ] **Step 3: Implementar (añadir a `presentadores.py`)**

```python
from arc_flash import arc_flash_desde_proteccion
from protecciones import verificar_circuito_completo
from coordinacion import verificar_cadena, calcular_tiempo_disparo


def presentar_protecciones(sesion: SesionProyecto) -> dict:
    zt = _zt_trafo(sesion)
    filas, alertas = [], []
    for c in sesion.circuitos:
        prot = sesion.protecciones.get(c["nombre"])
        if not prot:
            continue
        icc, _, _ = calcular_icc_punto(zt, c["L_m"], c["S_mm2"], c["paralelos"], c["sistema"])
        vn = TENSION_SISTEMA.get(c["sistema"], 380)
        r = verificar_circuito_completo(
            c["nombre"], prot["In_A"], prot["curva"],
            prot.get("poder_corte_kA", 0), icc, vn,
        )
        if str(r.get("estado", "")).upper() != "OK":
            alertas.append(c["nombre"])
        filas.append({"nombre": c["nombre"], "estado": r.get("estado"), "Icc_kA": icc})
    return {"filas": filas, "alertas": alertas}


def presentar_coordinacion(sesion: SesionProyecto) -> dict:
    if not sesion.tiene_cadena:
        return {"filas": [], "alertas": []}
    filas, alertas = [], []
    for d in sesion.cadena:
        r = calcular_tiempo_disparo(
            (d.get("Icc_kA", 0) or 0) * 1000.0, d.get("In_A", 0), d.get("curva", "C"),
        )
        if r["region"] == "verificar_simaris":
            alertas.append(d.get("nombre", "?"))
        filas.append({"nombre": d.get("nombre"), "t_s": r["t_s"], "region": r["region"]})
    return {"filas": filas, "alertas": alertas}


def presentar_arc_flash(sesion: SesionProyecto) -> dict:
    zt = _zt_trafo(sesion)
    filas, alertas = [], []
    for c in sesion.circuitos:
        prot = sesion.protecciones.get(c["nombre"])
        if not prot:
            continue
        icc, _, _ = calcular_icc_punto(zt, c["L_m"], c["S_mm2"], c["paralelos"], c["sistema"])
        vn_kv = TENSION_SISTEMA.get(c["sistema"], 380) / 1000.0
        r = arc_flash_desde_proteccion(icc, vn_kv, prot["In_A"], prot["curva"])
        if r["despeje_incierto"] or (r["categoria_ppe"] is None):
            alertas.append(c["nombre"])
        filas.append({
            "nombre": c["nombre"], "E_cal_cm2": r["E_cal_cm2"],
            "D_afb_mm": r["D_afb_mm"], "categoria_ppe": r["categoria_ppe"],
        })
    return {"filas": filas, "alertas": alertas}
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_gui_core_presentadores.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui_core/presentadores.py tests/test_gui_core_presentadores.py
git commit -m "feat(gui_core): presentadores fase 3 (protecciones, coordinación, arc flash)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Presentadores fase 4 (balance, demanda, flujo nodal)

**Files:**
- Modify: `gui_core/presentadores.py`
- Test: `tests/test_gui_core_presentadores.py`

- [ ] **Step 1: Test que falla**

```python
def test_presentar_flujo_nodal_sin_cadena_vacio():
    from gui_core.presentadores import presentar_flujo_nodal
    r = presentar_flujo_nodal(SesionProyecto())
    assert r["buses"] == [] and r["alertas"] == []

def test_presentar_flujo_nodal_con_cadena():
    from gui_core.presentadores import presentar_flujo_nodal
    s = SesionProyecto()
    s.cargar({
        "cadena": [
            {"nombre": "G0", "upstream": "", "nivel": 0, "In_A": 1600, "curva": "C", "Icc_kA": 30.0},
            {"nombre": "C2", "upstream": "G0", "nivel": 1, "In_A": 160, "curva": "C", "Icc_kA": 6.0},
        ],
        "circuitos": [{"nombre": "L1", "sistema": "3F", "I_diseno": 100.0, "cos_phi": 0.9}],
        "trafo_z_ohm": 0.007,
    })
    r = presentar_flujo_nodal(s)
    assert any(b["id"] == "TRAFO" for b in r["buses"])
    assert r["convergido"] is True
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_core_presentadores.py -k flujo_nodal -q`

- [ ] **Step 3: Implementar (añadir a `presentadores.py`)**

```python
from balance import calcular_balance_tableros
from demanda import calcular_demanda
from red_desde_cadena import construir_red
from flujo_nodal import calcular_flujo_nodal


def presentar_balance(sesion: SesionProyecto) -> dict:
    if not (sesion.tiene_circuitos and sesion.tableros):
        return {"tableros": {}, "alertas": []}
    kva = float((sesion.trafo or {}).get("kVA", 0) or 0)
    r = calcular_balance_tableros(sesion.circuitos, sesion.balance_datos, sesion.tableros, kva)
    return {"resultado": r, "tableros": r.get("tableros", {}), "alertas": []}


def presentar_demanda(sesion: SesionProyecto) -> dict:
    if not sesion.tiene_circuitos:
        return {"resultado": None, "alertas": []}
    r = calcular_demanda(sesion.circuitos, sesion.balance_datos, sesion.params_demanda)
    return {"resultado": r, "alertas": []}


def presentar_flujo_nodal(sesion: SesionProyecto) -> dict:
    if not (sesion.tiene_cadena and sesion.trafo_z_ohm > 0):
        return {"buses": [], "convergido": False, "perdidas_kW": 0.0, "alertas": []}
    red = construir_red(sesion.cadena, sesion.trafo_z_ohm, sesion.circuitos,
                        vn_v=sesion.tension_sistema_v)
    if not red.ramas:
        return {"buses": [], "convergido": False, "perdidas_kW": 0.0,
                "alertas": ["sin nodos con Icc válida"]}
    res = calcular_flujo_nodal(red)
    alertas = [] if res["convergido"] else ["no convergió"]
    buses = [{"id": b, "V_pu": r["V_pu"], "V_kV": r["V_kV"], "P_kW": r["P_kW"]}
             for b, r in res["buses"].items()]
    return {"buses": buses, "convergido": res["convergido"],
            "perdidas_kW": res["perdidas_totales_kW"], "alertas": alertas}
```

- [ ] **Step 4: Correr → PASS**

Run: `python -m pytest tests/test_gui_core_presentadores.py -q`

- [ ] **Step 5: Commit**

```bash
git add gui_core/presentadores.py tests/test_gui_core_presentadores.py
git commit -m "feat(gui_core): presentadores fase 4 (balance, demanda, flujo nodal)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Registro→presentador y regresión final del núcleo

**Files:**
- Modify: `gui_core/fases.py` (mapa id→presentador)
- Test: `tests/test_gui_core_fases.py`

- [ ] **Step 1: Test que falla**

```python
def test_cada_modulo_calculable_tiene_presentador():
    from gui_core.fases import PRESENTADOR
    # todos menos los de fase 0 (datos) y 6 (reporte, se maneja aparte)
    ids_calculo = {m.id for m in MODULOS if m.fase in (1, 2, 3, 4)}
    faltan = ids_calculo - set(PRESENTADOR)
    assert not faltan, f"módulos sin presentador: {faltan}"
```

- [ ] **Step 2: Correr → FAIL**

Run: `python -m pytest tests/test_gui_core_fases.py::test_cada_modulo_calculable_tiene_presentador -q`

- [ ] **Step 3: Añadir el mapa `PRESENTADOR` al final de `fases.py`**

```python
from gui_core import presentadores as _p

PRESENTADOR = {
    "dv": _p.presentar_dv,
    "capacidad": _p.presentar_capacidad,
    "icc_trafo": _p.presentar_icc_trafo,
    "icc_punto": _p.presentar_icc_punto,
    "protecciones": _p.presentar_protecciones,
    "coordinacion": _p.presentar_coordinacion,
    "arc_flash": _p.presentar_arc_flash,
    "balance": _p.presentar_balance,
    "demanda": _p.presentar_demanda,
    "flujo_nodal": _p.presentar_flujo_nodal,
}
```
(Import al pie para evitar ciclo: `presentadores` importa de `sesion`, no de `fases`.)

- [ ] **Step 4: Correr → PASS + suite completa**

Run: `python -m pytest tests/test_gui_core_fases.py -q && python -m pytest tests/ -q`
Expected: verde (incluye ~40 tests nuevos de gui_core).

- [ ] **Step 5: Commit**

```bash
git add gui_core/fases.py tests/test_gui_core_fases.py
git commit -m "feat(gui_core): mapa módulo→presentador + cobertura de módulos calculables

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas para el ejecutor

- **`gui_core/` no importa `tkinter`** — es el cerebro testeable de la GUI. La capa visual (Plan 2) lo consume.
- **La GUI orquesta, no recalcula:** los presentadores llaman a los motores existentes tal cual; ninguna fórmula se reimplementa.
- **DAG de imports:** `estado` ← `sesion` ← `presentadores`; `fases` importa `estado`+`sesion` y (al pie) `presentadores`. Ningún motor importa `gui_core`.
- **Aporte de motores, arranque, generador/ats/ups/sts/trafo_iso, reporte:** sus presentadores se añaden en el Plan 2 junto a sus paneles (requieren decisiones de UI sobre parámetros de entrada); el registro ya los declara con prereqs para mostrar su estado.
- Suite completa se mantiene verde tras cada tarea.
