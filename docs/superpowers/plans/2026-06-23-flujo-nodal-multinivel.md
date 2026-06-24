# Flujo de carga nodal multinivel — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el grafo `Red` desde la hoja `cadena`, correr el flujo de carga nodal y volcar un perfil por barra (tensiones, caídas, pérdidas) a la memoria SEC.

**Architecture:** Un módulo nuevo `red_desde_cadena.py` traduce la cadena de coordinación (árbol `upstream`/`nivel` + `Icc_kA` por nodo) a un `Red` de `flujo_nodal.py`: topología por upstream, impedancia de rama desde la escalera de Icc (repartida R/X con X/R típico), cargas agregadas en hojas por peso de `In_A`. `reporteria_sec` solo renderiza. `flujo_nodal.py` no se modifica.

**Tech Stack:** Python 3.13, pytest, python-docx, numpy. Sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-06-23-flujo-nodal-multinivel-design.md`

---

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `red_desde_cadena.py` | mapeo cadena → `Red` (topología, Z desde Icc, cargas en hojas) | Crear |
| `reporteria_sec.py` | + `_agregar_seccion_flujo_nodal()` + cableado; bloque `flujo_nodal` en `exportar_json_epc` | Modificar |
| `gui.py` | enhebrar `cadena`, `trafo_z_ohm`, `tension_sistema_v` en `datos_run` | Modificar |
| `tests/test_red_desde_cadena.py` | mapeo (árbol, Z, cargas, casos límite) | Crear |
| `tests/test_reporteria_flujo_nodal.py` | sección memoria + JSON EPC | Crear |
| `tests/test_integracion_flujo_nodal_real.py` | cadena real de `circuitos.xlsx` | Crear |

Interfaces de `flujo_nodal.py` (NO modificar, solo usar):
- `Bus(id: str, tipo: str, P_kW=0.0, Q_kVAR=0.0, V_pu=1.0)` — tipo ∈ {"slack","PQ"} (PV no soportado).
- `Rama(from_bus: str, to_bus: str, R_ohm: float, X_ohm: float)`.
- `Red(buses: list[Bus], ramas: list[Rama], S_base_kVA=1000.0, V_base_kV=0.38)` — exige exactamente 1 slack; valida que cada rama referencie buses existentes.
- `calcular_flujo_nodal(red, max_iter=50, tol=1e-6) -> dict` con claves: `convergido`, `iteraciones`, `buses` ({id: {V_pu, delta_deg, V_kV, P_kW, Q_kVAR}}), `perdidas_totales_kW`, `norma`.

---

## Task 1: `red_desde_cadena.py` — topología (árbol + slack)

**Files:**
- Create: `red_desde_cadena.py`
- Test: `tests/test_red_desde_cadena.py`

- [ ] **Step 1: Escribir el test (falla)**

Crear `tests/test_red_desde_cadena.py`:
```python
"""Mapeo cadena de coordinación → Red (flujo_nodal)."""
import pytest
from red_desde_cadena import construir_red


def _cadena_min():
    # G0 (nivel 0) -> G1 (nivel 1) -> C2 (nivel 2, hoja)
    return [
        {"nombre": "G0", "upstream": "", "nivel": 0, "In_A": 1600, "curva": "ETU600", "Icc_kA": 30.0},
        {"nombre": "G1", "upstream": "G0", "nivel": 1, "In_A": 630, "curva": "ETU320", "Icc_kA": 10.0},
        {"nombre": "C2", "upstream": "G1", "nivel": 2, "In_A": 160, "curva": "C", "Icc_kA": 6.0},
    ]


def _circuitos_min():
    return [
        {"nombre": "L1", "sistema": "3F", "I_diseno": 100.0, "cos_phi": 0.9},
        {"nombre": "L2", "sistema": "3F", "I_diseno": 80.0, "cos_phi": 0.9},
    ]


def test_construye_red_con_slack_trafo():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    ids = [b.id for b in red.buses]
    assert "TRAFO" in ids
    slacks = [b for b in red.buses if b.tipo == "slack"]
    assert len(slacks) == 1 and slacks[0].id == "TRAFO"

def test_un_bus_por_dispositivo():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    ids = {b.id for b in red.buses}
    assert {"G0", "G1", "C2"}.issubset(ids)

def test_ramas_siguen_upstream():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    pares = {(r.from_bus, r.to_bus) for r in red.ramas}
    assert ("TRAFO", "G0") in pares   # nivel 0 cuelga del trafo
    assert ("G0", "G1") in pares
    assert ("G1", "C2") in pares
```

- [ ] **Step 2: Correr (debe fallar)**

Run: `python -m pytest tests/test_red_desde_cadena.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'red_desde_cadena'`

- [ ] **Step 3: Implementar la topología en `red_desde_cadena.py`**

```python
# ============================================================
# red_desde_cadena.py
# Responsabilidad: traducir la cadena de coordinación (árbol
# upstream/nivel + Icc por nodo) a un grafo Red de flujo_nodal.
# Normativa: IEC 60909 (Z desde Icc) / IEEE 399 (flujo de carga)
# ============================================================

from __future__ import annotations

import math

from flujo_nodal import Bus, Rama, Red

SLACK_ID = "TRAFO"
C_MAX = 1.05            # IEC 60909
COS_PHI_DEFAULT = 0.9   # para Q de las cargas


def _z_acumulada(icc_kA: float, vn_v: float) -> float:
    """Z acumulada (magnitud, Ω) hasta una barra desde su Icc trifásica."""
    icc_a = float(icc_kA) * 1000.0
    return (C_MAX * vn_v) / (math.sqrt(3.0) * icc_a)


def construir_red(
    cadena: list,
    trafo_z_ohm: float,
    circuitos: list,
    *,
    xr: float = 0.1,
    vn_v: float = 380.0,
    s_base_kVA: float = 1000.0,
) -> Red:
    """Construye un Red de flujo_nodal desde la cadena de coordinación.

    Topología: un bus por dispositivo; rama de upstream→dispositivo;
    nivel 0 cuelga del slack TRAFO.
    Impedancia de rama: derivada de la escalera de Icc (ver _z_acumulada),
    repartida R+jX con relación X/R = xr.
    Cargas: agregadas en nodos hoja por peso de In_A (ver Task 3).
    """
    buses: list[Bus] = [Bus(id=SLACK_ID, tipo="slack")]
    ramas: list[Rama] = []

    for d in cadena:
        nombre = str(d.get("nombre") or "").strip()
        if not nombre:
            continue
        buses.append(Bus(id=nombre, tipo="PQ"))
        padre = str(d.get("upstream") or "").strip() or SLACK_ID
        # impedancia de rama: se completa en Task 2 (placeholder mínimo aquí)
        ramas.append(Rama(from_bus=padre, to_bus=nombre, R_ohm=1e-6, X_ohm=0.0))

    return Red(buses=buses, ramas=ramas, S_base_kVA=s_base_kVA, V_base_kV=vn_v / 1000.0)
```

- [ ] **Step 4: Correr (debe pasar)**

Run: `python -m pytest tests/test_red_desde_cadena.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add red_desde_cadena.py tests/test_red_desde_cadena.py
git commit -m "feat(red): topología Red desde cadena (árbol upstream + slack trafo)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Impedancia de rama desde la escalera de Icc

**Files:**
- Modify: `red_desde_cadena.py`
- Test: `tests/test_red_desde_cadena.py`

- [ ] **Step 1: Escribir el test (falla)**

Añadir a `tests/test_red_desde_cadena.py`:
```python
def _rama(red, frm, to):
    return next(r for r in red.ramas if r.from_bus == frm and r.to_bus == to)

def test_z_rama_positiva_y_creciente_en_profundidad():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    z_g1 = _rama(red, "G0", "G1")
    z_c2 = _rama(red, "G1", "C2")
    # cada rama tiene impedancia positiva
    assert z_g1.R_ohm > 0 and z_c2.R_ohm > 0
    # la rama más profunda (Icc menor aguas abajo) aporta más impedancia
    assert abs(complex(z_c2.R_ohm, z_c2.X_ohm)) > abs(complex(z_g1.R_ohm, z_g1.X_ohm))

def test_z_rama_coincide_con_escalera_icc():
    import math
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min(), xr=0.1, vn_v=380.0)
    # Z_acum(G1) = 1.05*380/(√3*10000); Z_acum(G0)=1.05*380/(√3*30000)
    z_g1_acum = 1.05 * 380.0 / (math.sqrt(3) * 10000.0)
    z_g0_acum = 1.05 * 380.0 / (math.sqrt(3) * 30000.0)
    z_rama_esperada = z_g1_acum - z_g0_acum
    r = _rama(red, "G0", "G1")
    assert abs(complex(r.R_ohm, r.X_ohm)) == pytest.approx(z_rama_esperada, rel=1e-3)

def test_nodo_sin_icc_se_excluye():
    cadena = _cadena_min() + [
        {"nombre": "X9", "upstream": "C2", "nivel": 3, "In_A": 32, "curva": "C", "Icc_kA": None},
    ]
    red = construir_red(cadena, trafo_z_ohm=0.005, circuitos=_circuitos_min())
    ids = {b.id for b in red.buses}
    assert "X9" not in ids  # sin Icc → excluido
```

- [ ] **Step 2: Correr (debe fallar)**

Run: `python -m pytest tests/test_red_desde_cadena.py -v`
Expected: FAIL — `test_z_rama_coincide_con_escalera_icc` (R=1e-6 placeholder) y `test_nodo_sin_icc_se_excluye`.

- [ ] **Step 3: Implementar Z de rama y exclusión por Icc**

Reemplazar el cuerpo del bucle `for d in cadena:` en `construir_red` por:
```python
    # 1) Z acumulada por nodo (desde Icc); índice por nombre.
    z_acum: dict[str, float] = {SLACK_ID: float(trafo_z_ohm)}
    nodos_validos: list[dict] = []
    excluidos: list[str] = []
    for d in cadena:
        nombre = str(d.get("nombre") or "").strip()
        if not nombre:
            continue
        icc = d.get("Icc_kA")
        if icc is None or float(icc) <= 0:
            excluidos.append(nombre)
            continue
        z_acum[nombre] = _z_acumulada(float(icc), vn_v)
        nodos_validos.append(d)

    # 2) Buses + ramas (rama = Z_acum(nodo) − Z_acum(padre), repartida R/X).
    for d in nodos_validos:
        nombre = str(d["nombre"]).strip()
        padre = str(d.get("upstream") or "").strip() or SLACK_ID
        if padre not in z_acum:
            # padre excluido/ausente → cuelga del slack como aproximación
            padre = SLACK_ID
        buses.append(Bus(id=nombre, tipo="PQ"))
        z_mag = z_acum[nombre] - z_acum.get(padre, 0.0)
        if z_mag <= 0:
            z_mag = 1e-6  # dato sospechoso (Icc hijo ≥ padre)
        r = z_mag / math.sqrt(1.0 + xr * xr)
        x = r * xr
        ramas.append(Rama(from_bus=padre, to_bus=nombre, R_ohm=r, X_ohm=x))
```
y eliminar el bucle placeholder anterior. Mantener la creación inicial de `buses = [Bus(SLACK_ID, "slack")]` y `ramas = []` antes de este bloque, y el `return Red(...)` después.

Exponer los excluidos: cambiar la firma para devolverlos no es necesario (YAGNI); en su lugar, adjuntarlos como atributo del Red para que el reporte los lea:
```python
    red = Red(buses=buses, ramas=ramas, S_base_kVA=s_base_kVA, V_base_kV=vn_v / 1000.0)
    red.nodos_excluidos = excluidos  # type: ignore[attr-defined]
    return red
```

- [ ] **Step 4: Correr (debe pasar)**

Run: `python -m pytest tests/test_red_desde_cadena.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add red_desde_cadena.py tests/test_red_desde_cadena.py
git commit -m "feat(red): impedancia de rama desde escalera de Icc + exclusión sin Icc

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Cargas agregadas en nodos hoja por peso de In

**Files:**
- Modify: `red_desde_cadena.py`
- Test: `tests/test_red_desde_cadena.py`

- [ ] **Step 1: Escribir el test (falla)**

Añadir a `tests/test_red_desde_cadena.py`:
```python
def _carga_total_circuitos(circuitos):
    import math
    tot = 0.0
    for c in circuitos:
        v = 380.0 if c["sistema"] == "3F" else 220.0
        f = math.sqrt(3) if c["sistema"] == "3F" else 1.0
        tot += f * v * float(c["I_diseno"]) * float(c["cos_phi"]) / 1000.0
    return tot

def test_carga_solo_en_hojas():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    # G0 y G1 son intermedios (sin carga); C2 es hoja (con carga)
    g0 = next(b for b in red.buses if b.id == "G0")
    c2 = next(b for b in red.buses if b.id == "C2")
    assert g0.P_kW == 0.0
    assert c2.P_kW < 0.0  # inyección de carga negativa

def test_carga_total_conservada():
    red = construir_red(_cadena_min(), trafo_z_ohm=0.005, circuitos=_circuitos_min())
    p_cargas = -sum(b.P_kW for b in red.buses if b.tipo == "PQ")
    esperado = _carga_total_circuitos(_circuitos_min())
    assert p_cargas == pytest.approx(esperado, rel=1e-6)

def test_reparto_por_peso_de_In():
    # dos hojas con In distinto → la de mayor In recibe más carga
    cadena = [
        {"nombre": "G0", "upstream": "", "nivel": 0, "In_A": 1000, "curva": "TM", "Icc_kA": 20.0},
        {"nombre": "HojaA", "upstream": "G0", "nivel": 1, "In_A": 200, "curva": "C", "Icc_kA": 8.0},
        {"nombre": "HojaB", "upstream": "G0", "nivel": 1, "In_A": 100, "curva": "C", "Icc_kA": 8.0},
    ]
    red = construir_red(cadena, trafo_z_ohm=0.005, circuitos=_circuitos_min())
    a = next(b for b in red.buses if b.id == "HojaA")
    b = next(b for b in red.buses if b.id == "HojaB")
    assert abs(a.P_kW) == pytest.approx(2 * abs(b.P_kW), rel=1e-6)  # 200/100
```

- [ ] **Step 2: Correr (debe fallar)**

Run: `python -m pytest tests/test_red_desde_cadena.py -v`
Expected: FAIL — las cargas siguen en 0 (aún no se asignan).

- [ ] **Step 3: Implementar cálculo de carga total + reparto en hojas**

Añadir estas funciones auxiliares a `red_desde_cadena.py` (nivel módulo):
```python
def _potencia_circuito_kW(c: dict) -> float:
    """P del circuito en kW: usa p_kw si existe; si no, √3·V·I·cosφ (3F) o V·I·cosφ (1F)."""
    if c.get("p_kw") is not None:
        return float(c["p_kw"])
    sistema = str(c.get("sistema", "3F")).upper()
    v = 380.0 if sistema == "3F" else 220.0
    f = math.sqrt(3.0) if sistema == "3F" else 1.0
    i = float(c.get("I_diseno") or 0.0)
    cosphi = float(c.get("cos_phi") or COS_PHI_DEFAULT)
    return f * v * i * cosphi / 1000.0


def _carga_total_kW(circuitos: list) -> float:
    return sum(_potencia_circuito_kW(c) for c in (circuitos or []))
```

Luego, justo antes del `red = Red(...)` final, agregar el reparto de carga a hojas:
```python
    # 3) Cargas: agregadas en nodos hoja, repartidas por peso de In_A.
    hijos = {r.from_bus for r in ramas}
    hojas = [d for d in nodos_validos if str(d["nombre"]).strip() not in hijos]
    suma_in = sum(float(d.get("In_A") or 0.0) for d in hojas)
    p_total = _carga_total_kW(circuitos)
    tan_phi = math.tan(math.acos(COS_PHI_DEFAULT))
    bus_por_id = {b.id: b for b in buses}
    if suma_in > 0 and p_total > 0:
        for d in hojas:
            nombre = str(d["nombre"]).strip()
            peso = float(d.get("In_A") or 0.0) / suma_in
            p_hoja = p_total * peso
            bus = bus_por_id[nombre]
            bus.P_kW = -p_hoja
            bus.Q_kVAR = -p_hoja * tan_phi
```

- [ ] **Step 4: Correr (debe pasar)**

Run: `python -m pytest tests/test_red_desde_cadena.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add red_desde_cadena.py tests/test_red_desde_cadena.py
git commit -m "feat(red): cargas agregadas en hojas por peso de In (conserva total)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Sección "Flujo de Carga Nodal" en la memoria DOCX

**Files:**
- Modify: `reporteria_sec.py`
- Test: `tests/test_reporteria_flujo_nodal.py`

- [ ] **Step 1: Escribir el test (falla)**

Crear `tests/test_reporteria_flujo_nodal.py`:
```python
"""Sección de flujo de carga nodal en la memoria SEC."""
from pathlib import Path


def _tmp():
    d = Path(__file__).resolve().parent / ".tmp_flujo_nodal"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)

def _datos_run():
    return {
        "project_id": "TEST-FN", "revision": "R1",
        "timestamp": "2026-06-23T12:00:00+00:00", "perfil": "industrial",
        "norma": "MM2", "n_ok": 1, "n_fallas": 0, "max_dv_pct": 1.0,
        "max_icc_ka": 30.0, "status": "OK",
        "trafo_z_ohm": 0.005, "tension_sistema_v": 380.0,
        "cadena": [
            {"nombre": "G0", "upstream": "", "nivel": 0, "In_A": 1600, "curva": "ETU600", "Icc_kA": 30.0},
            {"nombre": "G1", "upstream": "G0", "nivel": 1, "In_A": 630, "curva": "ETU320", "Icc_kA": 10.0},
            {"nombre": "C2", "upstream": "G1", "nivel": 2, "In_A": 160, "curva": "C", "Icc_kA": 6.0},
        ],
    }

def _circuitos():
    return [
        {"nombre": "L1", "S_mm2": 25.0, "sistema": "3F", "I_diseno": 100.0, "cos_phi": 0.9,
         "L_m": 20.0, "paralelos": 1, "dv_pct": 0.3, "icc_ka": 6.0, "estado": "OK", "norma": "MM2"},
    ]

def test_memoria_incluye_seccion_flujo_nodal():
    from docx import Document
    from reporteria_sec import generar_memoria_docx
    ruta = generar_memoria_docx(_datos_run(), _circuitos(), _tmp())
    doc = Document(ruta)
    texto = "\n".join(p.text for p in doc.paragraphs)
    assert "Flujo de Carga Nodal" in texto

def test_memoria_flujo_nodal_tabla_por_barra():
    from docx import Document
    from reporteria_sec import generar_memoria_docx
    ruta = generar_memoria_docx(_datos_run(), _circuitos(), _tmp())
    doc = Document(ruta)
    encontrada = any(
        any("V (pu)" in cell.text for cell in tabla.rows[0].cells)
        for tabla in doc.tables
    )
    assert encontrada

def test_memoria_flujo_nodal_sin_cadena_omite():
    from docx import Document
    from reporteria_sec import generar_memoria_docx
    datos = _datos_run()
    datos["cadena"] = []
    ruta = generar_memoria_docx(datos, _circuitos(), _tmp())
    doc = Document(ruta)
    texto = "\n".join(p.text for p in doc.paragraphs)
    assert "sin cadena" in texto.lower()
```

- [ ] **Step 2: Correr (debe fallar)**

Run: `python -m pytest tests/test_reporteria_flujo_nodal.py -v`
Expected: FAIL — la sección no existe.

- [ ] **Step 3: Implementar `_agregar_seccion_flujo_nodal` en `reporteria_sec.py`**

Añadir cerca de `_agregar_seccion_arc_flash`:
```python
def _agregar_seccion_flujo_nodal(doc: Document, datos_run: dict, circuitos: list) -> None:
    """Sección de Flujo de Carga Nodal: perfil de tensiones por barra (Newton-Raphson)."""
    doc.add_heading("Flujo de Carga Nodal", level=1)

    cadena = datos_run.get("cadena") or []
    if not cadena:
        doc.add_paragraph(
            "Flujo nodal: sin cadena de coordinación cargada; se omite el análisis nodal."
        )
        return

    from red_desde_cadena import construir_red
    from flujo_nodal import calcular_flujo_nodal

    trafo_z = float(datos_run.get("trafo_z_ohm") or 0.0)
    vn = float(datos_run.get("tension_sistema_v") or 380.0)
    if trafo_z <= 0:
        doc.add_paragraph("Flujo nodal: impedancia del transformador no disponible; se omite.")
        return

    red = construir_red(cadena, trafo_z, circuitos, vn_v=vn)
    res = calcular_flujo_nodal(red)

    estado = "convergió" if res["convergido"] else "NO convergió"
    doc.add_paragraph(
        f"Newton-Raphson: {estado} en {res['iteraciones']} iteraciones. "
        f"Pérdidas totales: {res['perdidas_totales_kW']:.3f} kW."
    )

    tabla = doc.add_table(rows=1, cols=5)
    for i, h in enumerate(["Bus", "V (pu)", "V (kV)", "Caída %", "P (kW)"]):
        tabla.rows[0].cells[i].text = h
    for bus_id, r in res["buses"].items():
        caida = (1.0 - r["V_pu"]) * 100.0
        celdas = tabla.add_row().cells
        celdas[0].text = str(bus_id)
        celdas[1].text = f'{r["V_pu"]:.4f}'
        celdas[2].text = f'{r["V_kV"]:.4f}'
        celdas[3].text = f'{caida:.2f}'
        celdas[4].text = f'{r["P_kW"]:.2f}'

    excluidos = getattr(red, "nodos_excluidos", [])
    if excluidos:
        doc.add_paragraph(
            "Nodos excluidos por Icc faltante/inconsistente: " + ", ".join(excluidos)
        )
```

- [ ] **Step 4: Cablear en `generar_memoria_docx`**

En `reporteria_sec.py`, justo después del bloque `try/except` que llama `_agregar_seccion_arc_flash(...)`, añadir:
```python
    try:
        _agregar_seccion_flujo_nodal(doc, datos_run, circuitos)
    except Exception as e:
        print(f"[reporteria_sec] Flujo nodal no disponible: {e}")
        doc.add_paragraph(f"[Flujo de Carga Nodal no disponible: {e}]")
```

- [ ] **Step 5: Correr (debe pasar)**

Run: `python -m pytest tests/test_reporteria_flujo_nodal.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Regresión de reportería**

Run: `python -m pytest tests/test_reporteria_sec.py tests/test_reporteria_arc_flash.py -q`
Expected: PASS (sin regresiones).

- [ ] **Step 7: Commit**

```bash
git add reporteria_sec.py tests/test_reporteria_flujo_nodal.py
git commit -m "feat(reporteria): sección Flujo de Carga Nodal en memoria DOCX

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Bloque `flujo_nodal` en `exportar_json_epc`

**Files:**
- Modify: `reporteria_sec.py` (`exportar_json_epc`)
- Test: `tests/test_reporteria_flujo_nodal.py`

- [ ] **Step 1: Escribir el test (falla)**

Añadir a `tests/test_reporteria_flujo_nodal.py`:
```python
def test_json_epc_incluye_flujo_nodal():
    import json
    from reporteria_sec import exportar_json_epc
    ruta = exportar_json_epc(_datos_run(), _tmp(), circuitos=_circuitos())
    with open(ruta, encoding="utf-8") as fh:
        payload = json.load(fh)
    assert "flujo_nodal" in payload
    fn = payload["flujo_nodal"]
    assert "buses" in fn and "perdidas_totales_kW" in fn
    assert any(b["id"] == "TRAFO" for b in fn["buses"])
```

- [ ] **Step 2: Correr (debe fallar)**

Run: `python -m pytest tests/test_reporteria_flujo_nodal.py::test_json_epc_incluye_flujo_nodal -v`
Expected: FAIL — no existe el bloque `flujo_nodal`.

- [ ] **Step 3: Implementar el bloque en `exportar_json_epc`**

En `exportar_json_epc`, justo después del bloque `if circuitos:` que añade `payload["arc_flash"]`, añadir:
```python
    cadena = datos_run.get("cadena") or []
    trafo_z = float(datos_run.get("trafo_z_ohm") or 0.0)
    if cadena and trafo_z > 0:
        from red_desde_cadena import construir_red
        from flujo_nodal import calcular_flujo_nodal
        vn = float(datos_run.get("tension_sistema_v") or 380.0)
        red = construir_red(cadena, trafo_z, circuitos or [], vn_v=vn)
        res = calcular_flujo_nodal(red)
        payload["flujo_nodal"] = {
            "convergido": res["convergido"],
            "iteraciones": res["iteraciones"],
            "perdidas_totales_kW": res["perdidas_totales_kW"],
            "buses": [
                {"id": bid, "V_pu": r["V_pu"], "V_kV": r["V_kV"], "P_kW": r["P_kW"]}
                for bid, r in res["buses"].items()
            ],
        }
```

- [ ] **Step 4: Correr (debe pasar)**

Run: `python -m pytest tests/test_reporteria_flujo_nodal.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Regresión EPC**

Run: `python -m pytest tests/test_reporteria_sec.py -k epc -q`
Expected: PASS (los EPC existentes intactos).

- [ ] **Step 6: Commit**

```bash
git add reporteria_sec.py tests/test_reporteria_flujo_nodal.py
git commit -m "feat(reporteria): incluir flujo_nodal en exportar_json_epc

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Enhebrar datos en la GUI

**Files:**
- Modify: `gui.py`

- [ ] **Step 1: Localizar el bloque y los nombres reales**

Run: `python -c "import re;s=open('gui.py',encoding='utf-8-sig').read();[print(i+1, l) for i,l in enumerate(s.splitlines()) if 'datos_run = {' in l or 'icc_barra_ka' in l or 'calcular_icc_transformador' in l or 'self.cadena_datos' in l]"`
Read the region around `datos_run = {` (where Arc Flash keys `icc_barra_ka`/`proteccion_cabecera` were added) and confirm how the transformer impedance is obtained (the function `calcular_icc_transformador` returns `(Icc_kA, Zt_ohm, datos)`; the existing code may already compute it for `icc_barra_ka`).

- [ ] **Step 2: Añadir las tres claves a `datos_run`**

In the `datos_run = {...}` dict literal, add (adapt the `Zt` expression to the actual variable holding the transformer impedance found in Step 1; if only Icc is captured, capture the second return value `Zt_ohm` from the same `calcular_icc_transformador`/`icc_desde_tabla` call):
```python
                    "cadena": self.cadena_datos or [],
                    "trafo_z_ohm": float(_zt_ohm) if _zt_ohm else 0.0,
                    "tension_sistema_v": float(TENSION_SISTEMA.get("3F", 380)),
```
where `_zt_ohm` is the transformer impedance magnitude (Ω). If the existing Arc Flash threading already computed an `_icc_barra_ka` from `calcular_icc_transformador(...)`, extend that same call to also keep `Zt_ohm` as `_zt_ohm`. `TENSION_SISTEMA` is already imported in gui.py (used elsewhere).

- [ ] **Step 3: Verificar sintaxis**

Run: `python -c "import ast; ast.parse(open('gui.py',encoding='utf-8-sig').read()); print('gui.py OK sintaxis')"`
Expected: `gui.py OK sintaxis`

- [ ] **Step 4: Regresión GUI**

Run: `python -m pytest tests/test_gui_reporte.py tests/test_gui_guiada.py tests/test_gui_guiada_v2.py -q`
Expected: PASS / collect sin errores.

- [ ] **Step 5: Commit**

```bash
git add gui.py
git commit -m "feat(gui): enhebrar cadena + Z trafo + tensión hacia el flujo nodal

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Validación end-to-end con la cadena real

**Files:**
- Create: `tests/test_integracion_flujo_nodal_real.py`

- [ ] **Step 1: Escribir el test (falla si algo no encaja)**

Crear `tests/test_integracion_flujo_nodal_real.py`:
```python
"""Validación: flujo nodal sobre la cadena real de circuitos.xlsx (G0A→G1A→C1A→C2A)."""
from pathlib import Path
import openpyxl
import pytest
from excel import leer_cadena_excel
from red_desde_cadena import construir_red
from flujo_nodal import calcular_flujo_nodal

LIBRO = Path(__file__).resolve().parents[1] / "circuitos.xlsx"


def _circuitos_simple():
    return [
        {"nombre": "L1", "sistema": "3F", "I_diseno": 100.0, "cos_phi": 0.9},
        {"nombre": "L2", "sistema": "3F", "I_diseno": 63.0, "cos_phi": 0.85},
    ]

def test_cadena_real_converge_y_tensiones_decrecen():
    assert LIBRO.exists(), "circuitos.xlsx debe existir en la raíz del repo"
    wb = openpyxl.load_workbook(LIBRO, read_only=True, data_only=True)
    cadena = leer_cadena_excel(wb)
    assert cadena, "la hoja cadena debe tener dispositivos"

    red = construir_red(cadena, trafo_z_ohm=0.005, circuitos=_circuitos_simple(), vn_v=380.0)
    res = calcular_flujo_nodal(red)
    assert res["convergido"] is True

    # El slack está a 1.0 pu; las barras aguas abajo deben tener V_pu <= 1.0
    v_trafo = res["buses"]["TRAFO"]["V_pu"]
    assert v_trafo == pytest.approx(1.0, abs=1e-6)
    for bid, r in res["buses"].items():
        if bid != "TRAFO":
            assert r["V_pu"] <= 1.0 + 1e-9

def test_cadena_real_perdidas_positivas():
    wb = openpyxl.load_workbook(LIBRO, read_only=True, data_only=True)
    cadena = leer_cadena_excel(wb)
    red = construir_red(cadena, trafo_z_ohm=0.005, circuitos=_circuitos_simple(), vn_v=380.0)
    res = calcular_flujo_nodal(red)
    assert res["perdidas_totales_kW"] >= 0.0
```

- [ ] **Step 2: Correr el test**

Run: `python -m pytest tests/test_integracion_flujo_nodal_real.py -v`
Expected: PASS (2 tests). Si no converge por impedancias muy pequeñas/grandes derivadas de la Icc real, NO ocultar el fallo: reportarlo como concern y revisar el reparto R/X o el `trafo_z_ohm` de prueba (subir a un valor físico como 0.007 Ω para 1000 kVA). Documentar cualquier ajuste.

- [ ] **Step 3: Commit**

```bash
git add tests/test_integracion_flujo_nodal_real.py
git commit -m "test(integracion): flujo nodal sobre cadena real de circuitos.xlsx

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Regresión final + roadmap

- [ ] **Step 1: Suite completa**

Run: `python -m pytest tests/ -q`
Expected: todos verdes (≈ 675 previos + nuevos), 0 fallos.

- [ ] **Step 2: Actualizar el roadmap**

En `auditoria/11_ROADMAP_CONSOLIDADO.md`, en la sección Fase 3, añadir una nota: el flujo nodal P2.1 quedó **integrado a la memoria SEC** vía la cadena de coordinación (módulo `red_desde_cadena.py`), no solo como motor aislado.

- [ ] **Step 3: Commit**

```bash
git add auditoria/11_ROADMAP_CONSOLIDADO.md
git commit -m "docs: flujo nodal integrado a memoria SEC vía cadena de coordinación

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas para el ejecutor

- **No modificar `flujo_nodal.py`** — solo se consume. Sus invariantes: exactamente 1 slack, ramas referencian buses existentes, PV no soportado.
- **Genérico, no LEO/proyecto-específico:** ningún valor de proyecto en código de producción. `circuitos.xlsx` (raíz del repo) es un fixture ya existente del proyecto, válido para el test de integración.
- **Orden de import (DAG):** `red_desde_cadena` → `flujo_nodal`; `reporteria_sec` → `red_desde_cadena`/`flujo_nodal`. Nunca al revés.
- **Robustez:** la sección de memoria va envuelta en try/except y nunca rompe la generación.
- **Atributo `nodos_excluidos`:** se adjunta dinámicamente al objeto `Red` (no es un campo del dataclass de `flujo_nodal`); leerlo con `getattr(red, "nodos_excluidos", [])`.
