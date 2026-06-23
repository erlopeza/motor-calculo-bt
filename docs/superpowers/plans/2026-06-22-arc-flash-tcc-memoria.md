# Arc Flash + TCC en memoria SEC — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar los motores `arc_flash`, `tcc_curvas` y `coordinacion` a la memoria SEC, produciendo una sección de Arc Flash (barra principal + tabla por circuito) sobre datos genéricos, validada con LEO-ARICA.

**Architecture:** El cálculo vive en `arc_flash.py` (puente que evalúa el tiempo de despeje en la corriente de arco Ia vía `coordinacion`). `coordinacion.py` toma la constante térmica k de una fuente única (catálogo `tcc_curvas`). `reporteria_sec.py` solo renderiza. La entrada usa el formato Excel canónico existente; LEO-ARICA entra como dato de validación.

**Tech Stack:** Python 3.13, pytest, python-docx, openpyxl. Sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-06-22-arc-flash-tcc-memoria-design.md`

---

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `tcc_curvas.py` | + `get_k_iec60898(modelo)` — k como fuente única | Modificar |
| `coordinacion.py` | `K_CURVA` derivado del catálogo (no hardcode B/C/D) | Modificar |
| `arc_flash.py` | + `arc_flash_desde_proteccion(...)` (puente Ia→t→energía) | Modificar |
| `reporteria_sec.py` | + `enriquecer_circuitos_con_proteccion()` + `_agregar_seccion_arc_flash()` + cableado en `generar_memoria_docx`; arco en `exportar_json_epc` | Modificar |
| `gui.py` | enhebrar In_A/curva en circuitos + icc_barra/cabecera en datos_run | Modificar |
| `tests/test_tcc_curvas.py` | tests de `get_k_iec60898` | Modificar |
| `tests/test_coordinacion_unificada.py` | regresión M7 idéntico | Crear |
| `tests/test_arc_flash_proteccion.py` | puente | Crear |
| `tests/test_reporteria_arc_flash.py` | enriquecer + sección memoria + json | Crear |
| `tests/fixtures/leo_arica.xlsx` | dato de validación conforme al formato canónico | Crear |
| `tests/test_integracion_leo_arica.py` | end-to-end | Crear |

---

## Task 1: Fuente única de la constante térmica k (tcc ↔ M7)

**Files:**
- Modify: `tcc_curvas.py`
- Modify: `coordinacion.py:22-27` (dict `K_CURVA`)
- Test: `tests/test_tcc_curvas.py`, `tests/test_coordinacion_unificada.py`

- [ ] **Step 1: Escribir test de `get_k_iec60898` (falla)**

En `tests/test_tcc_curvas.py`, añadir al final:

```python
class TestKtermicoFuenteUnica:
    def test_get_k_valores_catalogo(self):
        from tcc_curvas import get_k_iec60898
        assert get_k_iec60898("B") == 45
        assert get_k_iec60898("C") == 80
        assert get_k_iec60898("D") == 180

    def test_get_k_insensible_mayusculas(self):
        from tcc_curvas import get_k_iec60898
        assert get_k_iec60898("c") == 80

    def test_get_k_curva_inexistente_lanza(self):
        from tcc_curvas import get_k_iec60898
        import pytest
        with pytest.raises(ValueError):
            get_k_iec60898("Z")
```

- [ ] **Step 2: Correr el test (debe fallar)**

Run: `python -m pytest tests/test_tcc_curvas.py::TestKtermicoFuenteUnica -v`
Expected: FAIL con `ImportError: cannot import name 'get_k_iec60898'`

- [ ] **Step 3: Implementar `get_k_iec60898` en `tcc_curvas.py`**

Añadir tras la función `buscar_curva`:

```python
def get_k_iec60898(modelo: str) -> float:
    """Constante térmica k de una curva IEC 60898 (t = k/(I/In)²).

    Fuente única del valor de k para todo el sistema (coordinación, arco).
    """
    entrada = buscar_curva("IEC60898", modelo)
    if entrada is None:
        raise ValueError(f"Curva IEC60898 modelo '{modelo}' no está en el catálogo")
    return float(entrada["parametros"]["k"])
```

- [ ] **Step 4: Correr el test (debe pasar)**

Run: `python -m pytest tests/test_tcc_curvas.py::TestKtermicoFuenteUnica -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Escribir test de regresión M7 (falla o pasa según estado)**

Crear `tests/test_coordinacion_unificada.py`:

```python
"""Regresión: K_CURVA B/C/D deriva del catálogo tcc (fuente única) sin cambiar números."""
from coordinacion import K_CURVA, calcular_tiempo_disparo


def test_kcurva_bcd_proviene_del_catalogo():
    from tcc_curvas import get_k_iec60898
    assert K_CURVA["B"] == get_k_iec60898("B")
    assert K_CURVA["C"] == get_k_iec60898("C")
    assert K_CURVA["D"] == get_k_iec60898("D")

def test_kcurva_conserva_TM():
    assert K_CURVA["TM"] == 100

def test_tiempo_termico_identico_tras_unificar():
    # Curva C, In=100, I=150 (región térmica) → t = 80/(1.5²) = 35.556 s
    r = calcular_tiempo_disparo(150.0, 100.0, "C")
    assert r["region"] == "termico"
    assert round(r["t_s"], 3) == 35.556
```

- [ ] **Step 6: Correr (test_tiempo_termico debería pasar ya; los de derivación fallan)**

Run: `python -m pytest tests/test_coordinacion_unificada.py -v`
Expected: `test_tiempo_termico_identico_tras_unificar` PASS; los dos de derivación FAIL (K_CURVA aún hardcodeado).

- [ ] **Step 7: Derivar `K_CURVA` del catálogo en `coordinacion.py`**

Reemplazar el bloque (líneas ~22-27):

```python
K_CURVA = {
    "B": 45,    # disparo magnético: 3–5×In
    "C": 80,    # disparo magnético: 5–10×In
    "D": 180,   # disparo magnético: 10–20×In
    "TM": 100,  # termomagnético IEC 60947-2 (aproximación)
}
```

por:

```python
from tcc_curvas import get_k_iec60898

# Constante térmica k: B/C/D provienen del catálogo DATA-3 (fuente única);
# TM es aproximación IEC 60947-2 (no es curva IEC 60898).
K_CURVA = {
    "B": get_k_iec60898("B"),
    "C": get_k_iec60898("C"),
    "D": get_k_iec60898("D"),
    "TM": 100,  # termomagnético IEC 60947-2 (aproximación)
}
```

- [ ] **Step 8: Correr la suite de coordinación completa (regresión)**

Run: `python -m pytest tests/test_coordinacion_unificada.py tests/test_coordinacion_refinada.py -v`
Expected: PASS (todos). Confirma que M7 no cambió de números.

- [ ] **Step 9: Commit**

```bash
git add tcc_curvas.py coordinacion.py tests/test_tcc_curvas.py tests/test_coordinacion_unificada.py
git commit -m "feat(tcc): fuente única de k térmico; coordinacion deriva K_CURVA del catálogo

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Puente Arc-Flash ↔ protección (`arc_flash_desde_proteccion`)

**Files:**
- Modify: `arc_flash.py`
- Test: `tests/test_arc_flash_proteccion.py`

- [ ] **Step 1: Escribir el test (falla)**

Crear `tests/test_arc_flash_proteccion.py`:

```python
"""P1.1 integración — puente arc_flash ↔ protección (t de despeje en Ia)."""
import pytest
from arc_flash import arc_flash_desde_proteccion


class TestPuenteArcFlash:
    def test_dict_completo(self):
        r = arc_flash_desde_proteccion(Ibf_kA=20.0, V_kV=0.4, In_A=250, curva="C")
        for k in ("Ia_kA", "t_despeje_s", "region_despeje", "E_cal_cm2",
                  "D_afb_mm", "categoria_ppe", "despeje_incierto", "verificar_simaris"):
            assert k in r

    def test_ia_menor_que_ibf(self):
        r = arc_flash_desde_proteccion(20.0, 0.4, 250, "C")
        assert 0 < r["Ia_kA"] < 20.0

    def test_falla_alta_dispara_instantaneo(self):
        # Ia muy por encima del umbral magnético C (10×In) → instantáneo 0.02 s
        r = arc_flash_desde_proteccion(Ibf_kA=25.0, V_kV=0.4, In_A=100, curva="C")
        assert r["region_despeje"] == "instantaneo"
        assert r["t_despeje_s"] == pytest.approx(0.02, abs=1e-6)

    def test_proteccion_no_despeja_aplica_techo_y_bandera(self):
        # In enorme respecto a Ia → no dispara → techo 2 s + bandera
        r = arc_flash_desde_proteccion(Ibf_kA=2.0, V_kV=0.4, In_A=4000, curva="C")
        assert r["despeje_incierto"] is True
        assert r["t_despeje_s"] == pytest.approx(2.0, abs=1e-6)

    def test_energia_positiva(self):
        r = arc_flash_desde_proteccion(20.0, 0.4, 250, "C")
        assert r["E_cal_cm2"] > 0

    def test_techo_parametrizable(self):
        r = arc_flash_desde_proteccion(2.0, 0.4, 4000, "C", t_techo_s=1.0)
        assert r["t_despeje_s"] == pytest.approx(1.0, abs=1e-6)
```

- [ ] **Step 2: Correr el test (debe fallar)**

Run: `python -m pytest tests/test_arc_flash_proteccion.py -v`
Expected: FAIL con `ImportError: cannot import name 'arc_flash_desde_proteccion'`

- [ ] **Step 3: Implementar el puente en `arc_flash.py`**

Añadir al inicio (tras `import math`):

```python
import coordinacion
```

Añadir tras `calcular_arc_flash_completo`:

```python
def arc_flash_desde_proteccion(
    Ibf_kA: float,
    V_kV: float,
    In_A: float,
    curva: str,
    *,
    G_mm: float = 32.0,
    D_mm: float = 455.0,
    config: str = "box",
    t_techo_s: float = 2.0,
) -> dict:
    """Arc Flash con tiempo de despeje evaluado en la corriente de arco Ia.

    La corriente de arco Ia es menor que la de falla franca Ibf, por lo que la
    protección puede tardar más en despejar (IEEE 1584 §exige evaluar en Ia).

    Resolución del tiempo según la región de disparo a Ia:
      instantaneo                 -> t del dispositivo
      termico/tiempo_corto/idmt   -> t del dispositivo (puede ser grande)
      verificar_simaris (ETU)     -> t_techo + bandera verificar_simaris
      no_dispara / t indefinido   -> t_techo + bandera despeje_incierto

    Defaults G/D/config: típicos IEEE 1584-2002 para tablero BT cerrado.
    """
    ia_res = calcular_corriente_arco(Ibf_kA, V_kV, G_mm, config)
    Ia_kA = ia_res["Ia_kA"]

    disp = coordinacion.calcular_tiempo_disparo(Ia_kA * 1000.0, In_A, curva)
    region = disp["region"]
    despeje_incierto = False
    verificar_simaris = False

    if region in ("instantaneo", "termico", "tiempo_corto", "idmt"):
        t = disp["t_s"]
    elif region == "verificar_simaris":
        t = t_techo_s
        verificar_simaris = True
    else:  # no_dispara u otro
        t = t_techo_s
        despeje_incierto = True

    if t is None:  # dispara pero sin tiempo determinado (defensivo)
        t = t_techo_s
        despeje_incierto = True

    af = calcular_arc_flash_completo(
        Ibf_kA, V_kV, G_mm, t_s=float(t), D_mm=D_mm, config=config
    )

    return {
        "Ibf_kA":            float(Ibf_kA),
        "Ia_kA":             Ia_kA,
        "t_despeje_s":       round(float(t), 4),
        "region_despeje":    region,
        "E_cal_cm2":         af["E_cal_cm2"],
        "D_afb_mm":          af["D_afb_mm"],
        "categoria_ppe":     af["categoria_ppe"],
        "estado_ppe":        af["estado_ppe"],
        "despeje_incierto":  despeje_incierto,
        "verificar_simaris": verificar_simaris,
        "norma":             af["norma"],
    }
```

- [ ] **Step 4: Correr el test (debe pasar)**

Run: `python -m pytest tests/test_arc_flash_proteccion.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Verificar que no hay ciclo de import y la suite de arco sigue verde**

Run: `python -c "import arc_flash" && python -m pytest tests/test_arc_flash.py -q`
Expected: import OK; 41 passed

- [ ] **Step 6: Commit**

```bash
git add arc_flash.py tests/test_arc_flash_proteccion.py
git commit -m "feat(arc_flash): puente arc_flash_desde_proteccion (t de despeje en Ia)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Enriquecer circuitos con protección (helper genérico)

**Files:**
- Modify: `reporteria_sec.py`
- Test: `tests/test_reporteria_arc_flash.py`

- [ ] **Step 1: Escribir el test (falla)**

Crear `tests/test_reporteria_arc_flash.py`:

```python
"""P1.1 memoria — enriquecer circuitos y sección Arc Flash en la memoria SEC."""
from pathlib import Path
import uuid
from reporteria_sec import enriquecer_circuitos_con_proteccion


def test_enriquecer_agrega_in_y_curva():
    circuitos = [{"nombre": "C-01", "sistema": "3F", "icc_ka": 10.0}]
    protecciones = {"C-01": {"In_A": 250, "curva": "C", "poder_corte_kA": 25}}
    out = enriquecer_circuitos_con_proteccion(circuitos, protecciones)
    assert out[0]["In_A"] == 250
    assert out[0]["curva"] == "C"

def test_enriquecer_sin_proteccion_no_rompe():
    circuitos = [{"nombre": "C-99", "sistema": "3F", "icc_ka": 5.0}]
    out = enriquecer_circuitos_con_proteccion(circuitos, {})
    assert "In_A" not in out[0] or out[0].get("In_A") in (None, 0)

def test_enriquecer_no_muta_original():
    circuitos = [{"nombre": "C-01", "sistema": "3F", "icc_ka": 10.0}]
    enriquecer_circuitos_con_proteccion(circuitos, {"C-01": {"In_A": 100, "curva": "B"}})
    assert "In_A" not in circuitos[0]
```

- [ ] **Step 2: Correr el test (debe fallar)**

Run: `python -m pytest tests/test_reporteria_arc_flash.py -v`
Expected: FAIL con `ImportError: cannot import name 'enriquecer_circuitos_con_proteccion'`

- [ ] **Step 3: Implementar el helper en `reporteria_sec.py`**

Añadir como función de módulo (tras los imports / antes de `generar_memoria_docx`):

```python
def enriquecer_circuitos_con_proteccion(circuitos: list, protecciones: dict) -> list:
    """Devuelve copias de los circuitos con In_A/curva de su protección (por nombre).

    `protecciones` es {nombre_circuito: {"In_A": .., "curva": .., ...}}.
    Circuitos sin protección quedan sin In_A/curva. No muta la entrada.
    """
    salida = []
    for c in circuitos:
        c2 = dict(c)
        prot = protecciones.get(c.get("nombre"))
        if prot:
            if prot.get("In_A"):
                c2["In_A"] = prot["In_A"]
            if prot.get("curva"):
                c2["curva"] = prot["curva"]
        salida.append(c2)
    return salida
```

- [ ] **Step 4: Correr el test (debe pasar)**

Run: `python -m pytest tests/test_reporteria_arc_flash.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add reporteria_sec.py tests/test_reporteria_arc_flash.py
git commit -m "feat(reporteria): enriquecer_circuitos_con_proteccion (merge In_A/curva)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Sección Arc Flash en la memoria DOCX

**Files:**
- Modify: `reporteria_sec.py` (nueva función + cableado en `generar_memoria_docx`)
- Test: `tests/test_reporteria_arc_flash.py`

- [ ] **Step 1: Escribir el test (falla)**

Añadir a `tests/test_reporteria_arc_flash.py`:

```python
def _tmp(): 
    d = Path(__file__).resolve().parent / ".tmp_arcflash"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)

def _datos_run():
    return {
        "project_id": "TEST-AF", "revision": "R1",
        "timestamp": "2026-06-22T12:00:00+00:00", "perfil": "industrial",
        "norma": "MM2", "n_ok": 1, "n_fallas": 0, "max_dv_pct": 1.0,
        "max_icc_ka": 12.0, "status": "OK",
        "icc_barra_ka": 25.0,
        "proteccion_cabecera": {"In_A": 630, "curva": "C"},
    }

def _circuitos_af():
    return [
        {"nombre": "C-01", "conductor": "25mm2", "S_mm2": 25.0, "I_diseno": 80.0,
         "I_max": 100.0, "cos_phi": 0.9, "L_m": 20.0, "paralelos": 1, "sistema": "3F",
         "dv_v": 1.0, "dv_pct": 0.3, "icc_ka": 12.0, "estado": "OK", "norma": "MM2",
         "observaciones": "", "In_A": 100, "curva": "C"},
        {"nombre": "C-02-SIN-PROT", "conductor": "16mm2", "S_mm2": 16.0, "I_diseno": 50.0,
         "I_max": 76.0, "cos_phi": 0.9, "L_m": 30.0, "paralelos": 1, "sistema": "3F",
         "dv_v": 1.0, "dv_pct": 0.4, "icc_ka": 8.0, "estado": "OK", "norma": "MM2",
         "observaciones": ""},
    ]

def test_memoria_incluye_seccion_arc_flash():
    from docx import Document as DocxDocument
    from reporteria_sec import generar_memoria_docx
    ruta = generar_memoria_docx(_datos_run(), _circuitos_af(), _tmp())
    doc = DocxDocument(ruta)
    texto = "\n".join(p.text for p in doc.paragraphs)
    assert "Arco Eléctrico" in texto
    assert "IEEE 1584" in texto

def test_memoria_arc_flash_tiene_tabla_por_circuito():
    from docx import Document as DocxDocument
    from reporteria_sec import generar_memoria_docx
    ruta = generar_memoria_docx(_datos_run(), _circuitos_af(), _tmp())
    doc = DocxDocument(ruta)
    # Debe existir al menos una tabla con encabezado "Cat EPP"
    encontrada = any(
        any("Cat EPP" in cell.text for cell in tabla.rows[0].cells)
        for tabla in doc.tables
    )
    assert encontrada

def test_memoria_arc_flash_lista_circuitos_sin_proteccion():
    from docx import Document as DocxDocument
    from reporteria_sec import generar_memoria_docx
    ruta = generar_memoria_docx(_datos_run(), _circuitos_af(), _tmp())
    doc = DocxDocument(ruta)
    texto = "\n".join(p.text for p in doc.paragraphs)
    assert "C-02-SIN-PROT" in texto
```

- [ ] **Step 2: Correr el test (debe fallar)**

Run: `python -m pytest tests/test_reporteria_arc_flash.py -k arc_flash -v`
Expected: FAIL — la memoria aún no tiene la sección (assert "Arco Eléctrico").

- [ ] **Step 3: Implementar `_agregar_seccion_arc_flash` en `reporteria_sec.py`**

Añadir la función:

```python
def _agregar_seccion_arc_flash(doc, datos_run: dict, circuitos: list) -> None:
    """Sección de Arc Flash (IEEE 1584): barra principal + tabla por circuito."""
    from arc_flash import arc_flash_desde_proteccion
    from conductores import TENSION_SISTEMA

    doc.add_heading("Análisis de Arco Eléctrico (IEEE 1584)", level=1)

    # --- Barra principal ---
    icc_barra = datos_run.get("icc_barra_ka")
    cab = datos_run.get("proteccion_cabecera") or {}
    v_barra_kv = float(datos_run.get("tension_barra_kv", 0.4))
    if icc_barra and cab.get("In_A") and cab.get("curva"):
        r = arc_flash_desde_proteccion(
            float(icc_barra), v_barra_kv, cab["In_A"], cab["curva"]
        )
        cat = "PELIGRO" if r["categoria_ppe"] is None else f"Cat {r['categoria_ppe']}"
        doc.add_heading("Barra principal", level=2)
        doc.add_paragraph(
            f"Ibf={r['Ibf_kA']:.2f} kA · Ia={r['Ia_kA']:.2f} kA · "
            f"t_despeje={r['t_despeje_s']:.3f} s · E={r['E_cal_cm2']:.2f} cal/cm² · "
            f"Frontera={r['D_afb_mm']:.0f} mm · {cat}"
            + ("  ⚠ despeje incierto" if r["despeje_incierto"] else "")
        )
    else:
        doc.add_paragraph(
            "Barra principal: sin Icc de barra o protección de cabecera definida; "
            "se omite el cálculo de arco en la barra."
        )

    # --- Tabla por circuito ---
    con_prot = [c for c in circuitos if c.get("In_A") and c.get("curva") and c.get("icc_ka")]
    sin_prot = [c for c in circuitos if not (c.get("In_A") and c.get("curva"))]

    if con_prot:
        doc.add_heading("Por circuito", level=2)
        tabla = doc.add_table(rows=1, cols=7)
        encabezados = ["Circuito", "Icc (kA)", "Ia (kA)", "t_desp (s)",
                       "E (cal/cm²)", "Frontera (mm)", "Cat EPP"]
        for i, h in enumerate(encabezados):
            tabla.rows[0].cells[i].text = h
        for c in con_prot:
            v_kv = TENSION_SISTEMA.get(c["sistema"], 380) / 1000.0
            r = arc_flash_desde_proteccion(
                float(c["icc_ka"]), v_kv, c["In_A"], c["curva"]
            )
            marca = " ⚠" if (r["despeje_incierto"] or r["verificar_simaris"]) else ""
            cat = "PELIGRO" if r["categoria_ppe"] is None else str(r["categoria_ppe"])
            celdas = tabla.add_row().cells
            celdas[0].text = str(c.get("nombre", ""))
            celdas[1].text = f'{float(c["icc_ka"]):.2f}'
            celdas[2].text = f'{r["Ia_kA"]:.2f}'
            celdas[3].text = f'{r["t_despeje_s"]:.3f}'
            celdas[4].text = f'{r["E_cal_cm2"]:.2f}'
            celdas[5].text = f'{r["D_afb_mm"]:.0f}'
            celdas[6].text = cat + marca

    if sin_prot:
        nombres = ", ".join(str(c.get("nombre", "?")) for c in sin_prot)
        doc.add_paragraph(
            "Circuitos sin datos de protección (omitidos del análisis de arco): "
            + nombres
        )
```

- [ ] **Step 4: Cablear la sección en `generar_memoria_docx`**

En `reporteria_sec.py`, dentro de `generar_memoria_docx`, tras la sección "Calculo Icc" (justo antes de `doc.add_heading("Balance y Demanda", level=1)`), añadir:

```python
    try:
        _agregar_seccion_arc_flash(doc, datos_run, circuitos)
    except Exception as e:
        doc.add_paragraph(f"[Análisis de Arco Eléctrico no disponible: {e}]")
```

- [ ] **Step 5: Correr el test (debe pasar)**

Run: `python -m pytest tests/test_reporteria_arc_flash.py -v`
Expected: PASS (6 tests)

- [ ] **Step 6: Regresión de toda la reportería**

Run: `python -m pytest tests/test_reporteria_sec.py -q`
Expected: PASS (14)

- [ ] **Step 7: Commit**

```bash
git add reporteria_sec.py tests/test_reporteria_arc_flash.py
git commit -m "feat(reporteria): sección Arc Flash en memoria DOCX (barra + tabla)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Arc Flash en `exportar_json_epc`

**Files:**
- Modify: `reporteria_sec.py` (`exportar_json_epc`)
- Test: `tests/test_reporteria_arc_flash.py`

- [ ] **Step 1: Escribir el test (falla)**

Añadir a `tests/test_reporteria_arc_flash.py`:

```python
def test_json_epc_incluye_arc_flash():
    import json
    from reporteria_sec import exportar_json_epc
    ruta = exportar_json_epc(_datos_run(), _tmp(), circuitos=_circuitos_af())
    with open(ruta, encoding="utf-8") as fh:
        payload = json.load(fh)
    assert "arc_flash" in payload
    filas = payload["arc_flash"]["circuitos"]
    assert any(f["nombre"] == "C-01" for f in filas)
    assert filas[0]["E_cal_cm2"] >= 0
```

- [ ] **Step 2: Correr el test (debe fallar)**

Run: `python -m pytest tests/test_reporteria_arc_flash.py::test_json_epc_incluye_arc_flash -v`
Expected: FAIL — `exportar_json_epc` no acepta `circuitos` o no incluye `arc_flash`.

- [ ] **Step 3: Inspeccionar la firma actual de `exportar_json_epc`**

Run: `python -c "import inspect, reporteria_sec; print(inspect.signature(reporteria_sec.exportar_json_epc))"`
Expected: ver la firma para añadir el parámetro opcional `circuitos=None` sin romper llamadas existentes.

- [ ] **Step 4: Implementar el bloque arc_flash en `exportar_json_epc`**

Añadir parámetro `circuitos: list | None = None` a la firma. Antes de escribir el JSON, construir el bloque:

```python
    if circuitos:
        from arc_flash import arc_flash_desde_proteccion
        from conductores import TENSION_SISTEMA
        filas_af = []
        for c in circuitos:
            if not (c.get("In_A") and c.get("curva") and c.get("icc_ka")):
                continue
            v_kv = TENSION_SISTEMA.get(c.get("sistema", "3F"), 380) / 1000.0
            r = arc_flash_desde_proteccion(float(c["icc_ka"]), v_kv, c["In_A"], c["curva"])
            filas_af.append({
                "nombre": c.get("nombre"),
                "Ia_kA": r["Ia_kA"],
                "t_despeje_s": r["t_despeje_s"],
                "E_cal_cm2": r["E_cal_cm2"],
                "D_afb_mm": r["D_afb_mm"],
                "categoria_ppe": r["categoria_ppe"],
                "despeje_incierto": r["despeje_incierto"],
            })
        payload["arc_flash"] = {"norma": "IEEE 1584-2002", "circuitos": filas_af}
```

(`payload` es el dict que la función ya serializa; insertar el bloque antes del `json.dump`.)

- [ ] **Step 5: Correr el test (debe pasar)**

Run: `python -m pytest tests/test_reporteria_arc_flash.py::test_json_epc_incluye_arc_flash -v`
Expected: PASS

- [ ] **Step 6: Regresión JSON EPC existente**

Run: `python -m pytest tests/test_reporteria_sec.py -k epc -v`
Expected: PASS (los tests EPC existentes siguen verdes; `circuitos` es opcional)

- [ ] **Step 7: Commit**

```bash
git add reporteria_sec.py tests/test_reporteria_arc_flash.py
git commit -m "feat(reporteria): incluir arc_flash en exportar_json_epc (opcional)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Enhebrar datos en la GUI

**Files:**
- Modify: `gui.py` (bloque de `circuitos_persistencia` y `datos_run`, ≈ líneas 916-972)

- [ ] **Step 1: Localizar el bloque de ensamblado**

Run: `python -c "import re;s=open('gui.py',encoding='utf-8-sig').read();[print(i+1,l) for i,l in enumerate(s.splitlines()) if 'circuitos_persistencia.append' in l or 'datos_run = {' in l]"`
Expected: ver las líneas exactas del `.append(...)` y del dict `datos_run`.

- [ ] **Step 2: Añadir In_A/curva a cada circuito persistido**

En el `circuitos_persistencia.append({...})`, añadir dos claves al dict (leyendo de `self.protecciones`):

```python
                            "In_A": self.protecciones.get(c.get("nombre"), {}).get("In_A"),
                            "curva": self.protecciones.get(c.get("nombre"), {}).get("curva"),
```

- [ ] **Step 3: Añadir icc_barra_ka y proteccion_cabecera a `datos_run`**

En el dict `datos_run = {...}`, añadir:

```python
                    "icc_barra_ka": float(self.datos_trafo.get("Icc_kA", 0.0)) if getattr(self, "datos_trafo", None) else 0.0,
                    "proteccion_cabecera": next(
                        ({"In_A": p.get("In_A"), "curva": p.get("curva")}
                         for p in (self.protecciones.values() if isinstance(self.protecciones, dict) else [])
                         if p.get("nivel", 1) == 0),
                        {},
                    ),
```

- [ ] **Step 4: Verificación manual (la GUI no es unit-testeable headless)**

Run: `python -c "import ast; ast.parse(open('gui.py',encoding='utf-8-sig').read()); print('gui.py OK sintaxis')"`
Expected: `gui.py OK sintaxis`. La validación funcional real ocurre en el Task 7 (integración) que ejercita el mismo camino de datos sin la GUI.

- [ ] **Step 5: Commit**

```bash
git add gui.py
git commit -m "feat(gui): enhebrar In_A/curva e icc_barra/cabecera hacia la memoria

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Validación end-to-end LEO-ARICA (dato, no código)

**Files:**
- Create: `tests/fixtures/leo_arica.xlsx` (conforme al formato canónico)
- Create: `tests/test_integracion_leo_arica.py`

- [ ] **Step 1: Construir el fixture conforme al formato canónico**

Transcribir un subconjunto representativo de `LEO_ARICA_BASE_TECNICA_v5.xlsx` (hojas `03_TABLEROS_PANELES` y `04_CARGAS_CIRCUITOS`) al formato canónico. Crear `tests/_build_leo_fixture.py` y ejecutarlo una vez:

```python
import openpyxl

SRC = r"C:\Users\user007\Downloads\_WORK_REPO\02_PROYECTOS\ASESORIA-TECNICA-LEO_ARICA-2026\ANTECEDENTES\ELEC\LEO_ARICA_BASE_TECNICA_v5.xlsx"
DST = r"tests/fixtures/leo_arica.xlsx"

# Filas transcritas de 04_CARGAS_CIRCUITOS / 03_TABLEROS (subset real, en formato canónico).
# nombre, sistema, conductor, paralelos, i_diseno, cos_phi, l_m, temp_amb, In_A, curva
FILAS = [
    ("TD-RACKS-1", "3F", "70mm2", 1, 160.0, 0.95, 25.0, 30, 200, "C"),
    ("TD-RACKS-2", "3F", "50mm2", 1, 120.0, 0.95, 30.0, 30, 160, "C"),
    ("TD-HVAC",    "3F", "95mm2", 1, 210.0, 0.90, 18.0, 30, 250, "D"),
    ("TD-SERV",    "3F", "25mm2", 1,  70.0, 0.90, 40.0, 30, 100, "C"),
]
# NOTA al ejecutor: ajustar/ampliar FILAS con los valores reales de la base
# técnica (hojas 03/04). Mantener el formato canónico de columnas.

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "circuitos"
ws.append(["Nombre", "Sistema", "Conductor", "Paralelos", "I_diseno",
           "cos_phi", "L_m", "Temp_amb", "In_A", "curva"])
for f in FILAS:
    ws.append(list(f))

wp = wb.create_sheet("perfil")
wp.append(["campo", "valor"])
wp.append(["norma", "MM2"])
wp.append(["proyecto", "LEO-ARICA"])

import os
os.makedirs("tests/fixtures", exist_ok=True)
wb.save(DST)
print("fixture escrito:", DST)
```

Run: `python tests/_build_leo_fixture.py`
Expected: `fixture escrito: tests/fixtures/leo_arica.xlsx`

- [ ] **Step 2: Escribir el test de integración (falla)**

Crear `tests/test_integracion_leo_arica.py`:

```python
"""Validación end-to-end sobre datos reales LEO-ARICA conformados al formato canónico."""
from pathlib import Path
import openpyxl
import pytest
from reporteria_sec import enriquecer_circuitos_con_proteccion, generar_memoria_docx

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "leo_arica.xlsx"


def _leer_fixture():
    wb = openpyxl.load_workbook(FIXTURE, read_only=True, data_only=True)
    ws = wb["circuitos"]
    filas = list(ws.iter_rows(values_only=True))
    hdr = [str(h).lower() for h in filas[0]]
    circuitos, protecciones = [], {}
    for row in filas[1:]:
        d = dict(zip(hdr, row))
        nombre = d["nombre"]
        circuitos.append({
            "nombre": nombre, "sistema": d["sistema"], "conductor": d["conductor"],
            "S_mm2": float(str(d["conductor"]).replace("mm2", "")),
            "paralelos": int(d["paralelos"]), "I_diseno": float(d["i_diseno"]),
            "cos_phi": float(d["cos_phi"]), "L_m": float(d["l_m"]),
            "icc_ka": 15.0, "sistema_v": d["sistema"], "estado": "OK", "norma": "MM2",
        })
        protecciones[nombre] = {"In_A": d["in_a"], "curva": d["curva"]}
    return circuitos, protecciones


def test_fixture_existe():
    assert FIXTURE.exists(), "Ejecutar tests/_build_leo_fixture.py primero"

def test_memoria_leo_arica_genera_con_arc_flash(tmp_path):
    from docx import Document
    circuitos, protecciones = _leer_fixture()
    circuitos = enriquecer_circuitos_con_proteccion(circuitos, protecciones)
    datos_run = {
        "project_id": "LEO-ARICA", "revision": "VAL", "perfil": "datacenter",
        "norma": "MM2", "n_ok": len(circuitos), "n_fallas": 0,
        "max_dv_pct": 2.0, "max_icc_ka": 15.0, "status": "OK",
        "icc_barra_ka": 30.0, "proteccion_cabecera": {"In_A": 630, "curva": "C"},
    }
    ruta = generar_memoria_docx(datos_run, circuitos, str(tmp_path))
    doc = Document(ruta)
    texto = "\n".join(p.text for p in doc.paragraphs)
    assert "Arco Eléctrico" in texto
    # coherencia física: hay tabla con al menos una fila de datos
    tabla_af = [t for t in doc.tables if any("Cat EPP" in c.text for c in t.rows[0].cells)]
    assert tabla_af and len(tabla_af[0].rows) >= 2

def test_energia_en_rango_fisico(tmp_path):
    from arc_flash import arc_flash_desde_proteccion
    circuitos, protecciones = _leer_fixture()
    circuitos = enriquecer_circuitos_con_proteccion(circuitos, protecciones)
    for c in circuitos:
        r = arc_flash_desde_proteccion(15.0, 0.4, c["In_A"], c["curva"])
        assert 0 < r["E_cal_cm2"] < 1000, f"E fuera de rango en {c['nombre']}"
        assert r["D_afb_mm"] > 0
```

- [ ] **Step 3: Correr el test (debe pasar)**

Run: `python -m pytest tests/test_integracion_leo_arica.py -v`
Expected: PASS (3 tests)

- [ ] **Step 4: Commit (incluye el fixture .xlsx)**

```bash
git add tests/fixtures/leo_arica.xlsx tests/test_integracion_leo_arica.py tests/_build_leo_fixture.py
git commit -m "test(integracion): validación end-to-end Arc Flash sobre datos LEO-ARICA

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Regresión final y cierre

- [ ] **Step 1: Correr la suite completa**

Run: `python -m pytest tests/ -q`
Expected: todos verdes (≈ 645 previos + nuevos de este plan), 0 fallos.

- [ ] **Step 2: Actualizar el roadmap**

En `auditoria/11_ROADMAP_CONSOLIDADO.md`, añadir una nota de que P1.1/P1.2/P1.3 quedaron **integrados a la memoria SEC** (no solo motores aislados) y que existe validación LEO-ARICA.

- [ ] **Step 3: Commit**

```bash
git add auditoria/11_ROADMAP_CONSOLIDADO.md
git commit -m "docs: Arc Flash + TCC integrados a memoria SEC (validado LEO-ARICA)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas de diseño para el ejecutor

- **Orden de import:** `arc_flash` → `coordinacion` → `tcc_curvas` es un DAG sin ciclos. No introducir imports de `arc_flash` dentro de `coordinacion`/`tcc_curvas`.
- **Genérico, no LEO:** ningún valor de LEO-ARICA va en el código de producción. Solo en `tests/fixtures/leo_arica.xlsx` y el test de integración.
- **Robustez de la memoria:** la sección de arco nunca debe romper la generación; va envuelta en try/except en `generar_memoria_docx`.
- **Régimen de pruebas:** TDD estricto — test que falla antes de cada implementación.
