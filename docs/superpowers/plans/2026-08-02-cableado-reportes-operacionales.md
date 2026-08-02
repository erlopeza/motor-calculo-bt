# Cableado de Reportes Operacionales Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan task-by-task.

**Goal:** Ensure CLI and GUI report generation carry the production-calculated Arc Flash inputs, nodal-flow inputs, and motor short-circuit contribution into the SEC memory and PDF without duplicating calculation physics or inventing missing equipment data.

**Architecture:** Add small, pure composition helpers at the orchestration boundary. The CLI and GUI will call the existing report enrichment and calculation functions, while `reporteria_sec.py` remains the consumer of a stable `datos_run`/circuit contract. Header protection is included only when the input explicitly identifies a cabecera; otherwise the report keeps its existing omission warning.

**Tech Stack:** Python, pytest, existing `reporteria_sec.py`, `main.py`, `gui_core/presentadores.py`, `icc_punto.py`, `motores.py`, `red_desde_cadena.py`.

## Global Constraints

- Work only on branch `dev/oper-001-historical-cycle-validation-run`; do not modify or merge `main`.
- Preserve existing calculation formulas and public APIs.
- Use production composition paths in tests; do not recreate the final payload only by hand in tests.
- Do not fabricate `proteccion_cabecera` from an arbitrary circuit protection.
- Keep existing behavior when optional sheets or equipment data are absent.
- Run focused tests after each delivery, then the full suite; the known headless Tk failure is environmental and must be reported separately if it persists.
- Commit each delivery independently with a focused message.

---

## Delivery 1: Wire Arc Flash Inputs

**Files:** `main.py`, `gui_core/presentadores.py`, `tests/test_reporteria_operacional_arc_flash.py`

### Step 1: Add failing production-path tests

- Exercise a CLI composition helper with circuit protections and assert each persisted circuit receives `In_A` and `curva`.
- Assert the CLI report payload carries transformer bar short-circuit and explicit header protection when supplied.
- Exercise `_circuitos_enriquecidos()` with a `SesionProyecto` and assert GUI report circuits carry protection fields.
- Assert GUI report data carries bar short-circuit and only recognizes an explicitly marked header protection.

### Step 2: Run focused tests and confirm failure

```powershell
python -m pytest tests/test_reporteria_operacional_arc_flash.py -q
```

### Step 3: Implement minimal composition helpers

- Reuse `enriquecer_circuitos_con_proteccion()` in the CLI path.
- Add a shared local selection convention for explicitly named header protections (`CABECERA`, `PROTECCION_CABECERA`, `MAIN`, `GENERAL`) without changing the Excel reader contract.
- Add `icc_barra_ka`, `tension_barra_kv`, and `proteccion_cabecera` to report payloads where data is available.
- Add protection fields to GUI enriched circuits from `sesion.protecciones`.

### Step 4: Run focused and regression tests

```powershell
python -m pytest tests/test_reporteria_operacional_arc_flash.py tests/test_reporteria_arc_flash.py tests/test_integracion_leo_arica.py -q
```

### Step 5: Commit

```powershell
git add main.py gui_core/presentadores.py tests/test_reporteria_operacional_arc_flash.py
git commit -m "fix(reportes): cablear entradas Arc Flash CLI y GUI"
```

## Delivery 2: Wire CLI Nodal Flow

**Files:** `main.py`, `tests/test_reporteria_operacional_flujo.py`

### Step 1: Add failing production-path tests

- Build the CLI report payload through the new composition helper with a real chain-shaped input, transformer impedance, and voltage.
- Assert `cadena`, `trafo_z_ohm`, and `tension_sistema_v` are present and are sufficient for `construir_red()` to create branches.
- Assert the GUI path remains unchanged and continues to expose the same three fields.

### Step 2: Run focused tests and confirm failure

```powershell
python -m pytest tests/test_reporteria_operacional_flujo.py -q
```

### Step 3: Implement minimal CLI payload wiring

- Carry `cadena_datos` into `datos_run`.
- Carry the already calculated transformer impedance and system voltage into `datos_run`.
- Preserve empty/omitted behavior when no chain or transformer exists.

### Step 4: Run focused and regression tests

```powershell
python -m pytest tests/test_reporteria_operacional_flujo.py tests/test_flujo_nodal.py tests/test_integracion_flujo_nodal_real.py -q
```

### Step 5: Commit

```powershell
git add main.py tests/test_reporteria_operacional_flujo.py
git commit -m "fix(reportes): cablear flujo nodal en payload CLI"
```

## Delivery 3: Wire Motor Contribution to Reports

**Files:** `main.py`, `gui_core/presentadores.py`, `tests/test_reporteria_operacional_motores.py`

### Step 1: Add failing production-path tests

- Assert the CLI payload computes and exposes aggregate motor contribution when motor circuits exist.
- Assert GUI report data uses the existing motor contribution presenter and exposes the aggregate bar Icc plus a structured breakdown.
- Assert per-circuit Icc remains the per-point value; aggregate motor contribution is not incorrectly copied into every circuit.
- Assert installations without motors retain the existing zero/empty behavior.

### Step 2: Run focused tests and confirm failure

```powershell
python -m pytest tests/test_reporteria_operacional_motores.py -q
```

### Step 3: Implement minimal wiring

- Reuse `calcular_aporte_icc_motor()` and `calcular_icc_con_aporte_motores()` in the CLI composition path.
- Put aggregate values in explicit report metadata (`icc_barra_ka`, `aporte_motores`) while preserving per-circuit Icc.
- Reuse `presentar_aporte_motores()` in GUI report assembly and expose its result in `datos_run`.

### Step 4: Run focused and regression tests

```powershell
python -m pytest tests/test_reporteria_operacional_motores.py tests/test_aporte_motores.py tests/test_gui_core_presentadores_emergencia.py -q
```

## Final Verification and Delivery Reports

Run:

```powershell
python -m pytest -ra
git diff --check
git status --short --branch
```

After each delivery, report: commit hash, files changed, tests run/results, what was repaired, what remains, and whether the known Tk/Tcl environment failure persists. Do not claim the full suite is green unless the command actually passes.
