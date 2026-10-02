# 12 — Hallazgo y fix: factor c_max IEC 60909 ausente/incorrecto en Icc

**Fecha:** 2026-10-02 · **Origen:** construcción de matriz de gobernanza técnica para `calculos.py`/`icc_punto.py` (ver [11_ROADMAP_CONSOLIDADO.md](11_ROADMAP_CONSOLIDADO.md)).

## Hallazgo

Dos problemas relacionados, encontrados al documentar la fórmula real de cada función de `icc_punto.py` y compararla con su docstring:

1. **`icc_punto.py::calcular_icc_punto()`** — la Icc de cada circuito (usada en TODA la memoria SEC, CLI y GUI) no aplicaba ningún factor de tensión `c` pese a que su propio docstring decía `Icc = c_max × Vn / (√3 × |Z_total|)`. El código usaba `c=1.0` implícito.
2. **`transformador.py::C_MAX = 1.10`** — el factor usado para la Icc en bornes del transformador era el valor de **Media Tensión**, no el de Baja Tensión. El propio proyecto ya documentaba el valor correcto en `rag_normativa/referencias_iec.py:12` (`c_max = 1.05 (BT, Vn <= 1kV) / 1.10 (MT)`) y en el propio texto de la memoria SEC (`reporteria_sec.py:303`: *"c_max = 1.05"*) — es decir, la memoria generada **le decía al lector un valor mientras calculaba con otro**.

## Impacto real (no hipotético)

Camino de producción verificado: `main.py`/GUI → `calcular_icc_todos_circuitos()` → `calcular_icc_punto()` por circuito → ese valor se compara directo contra `poder_corte_kA` del breaker en `protecciones.py::verificar_circuito_completo()`. Esa verificación requiere la Icc **máxima** (c_max). Con c=1.0 en vez de 1.05, la Icc usada para validar poder de corte quedaba subestimada.

## Fix

- `icc_punto.py`: nueva constante `C_MAX_IEC60909 = 1.05` (par de la ya existente `C_MIN_IEC60909 = 0.95`). `calcular_icc_punto()` gana parámetro `c_max: float = C_MAX_IEC60909` (retrocompatible, no cambia la firma posicional ni el tupla de retorno) y lo aplica en la fórmula, para 3F y 1F/2F.
- `transformador.py`: `C_MAX` corregido de `1.10` a `1.05`.

## Números antes/después (caso LEO-ARICA: 1000 kVA, 380V, Ucc=5%)

| Valor | Antes | Después |
|---|---:|---:|
| `Icc_nom_kA` (bornes, sin c) | 30.39 | 30.39 (sin cambio) |
| `Icc_max_kA` (bornes, c_max) | 36.14 (con c=1.10, incorrecto) | 34.49 (con c=1.05) |
| `Icc_min_kA` (bornes, c_min) | 26.85 | 26.85 (sin cambio, c_min ya era correcto) |
| Icc por circuito (`calcular_icc_punto`) | sin factor c (c=1.0 implícito) | ×1.05 por defecto |

## Verificación

- Tests nuevos: `test_c_max_iec60909_es_1_05_bt`, `test_icc_punto_aplica_c_max_por_defecto`, `test_icc_punto_c_max_parametrizable` (`tests/test_impedancia_compleja.py`).
- Tests corregidos (aserción numérica dependía del valor incorrecto): `test_icc_max_leo_arica` (`tests/test_calculos.py`), `test_icc_transformador_respeta_cmax_cmin_y_tolerancia` (`tests/test_validacion_ingenieril_rapida.py`).
- Verificado exhaustivamente que ningún otro test dependía del valor antiguo: todos los usos de `calcular_icc_punto`/`calcular_icc_transformador` en tests restantes son relacionales (`<`, `>`) o usan datos independientes — invariantes ante un factor escalar uniforme.
- Suite completa: 819 tests (808 passed + 11 skipped), sin regresiones. `pyflakes` sin advertencias nuevas (las 3 preexistentes en `test_calculos.py`/`test_impedancia_compleja.py` no fueron introducidas por este fix).

## No tocado (fuera de alcance de este fix)

- `generador.py::C_MAX_BT = 1.05` ya era correcto — no se modificó.
- `commissioning/p4_icc.py`'s `* 1.10` es un margen de aceptación de comisionamiento, concepto distinto al factor `c` de IEC 60909 — no relacionado, no tocado.
- El texto fijo de `reporteria_sec.py:303` ("c_max = 1.05") ya era correcto; ahora también lo es el cálculo que describe.

## Adenda — tercer lugar con el mismo bug, encontrado en verificación end-to-end

Correr el CLI real (`python main.py --proyecto ... --excel circuitos.xlsx`) tras el fix mostró que la memoria SEC **seguía imprimiendo "maxima=36.14 kA"**, pese a que `transformador.py::C_MAX` ya estaba en 1.05. Causa: `main.py` (líneas ~1106-1109, dentro del bloque que arma `datos_transformador` para la memoria CLI) tiene su **propia reimplementación duplicada** del cálculo de Icc_max/Icc_min — recalcula `z_min`/`z_max` a mano y multiplica por `1.1`/`0.95` **literales hardcodeados**, sin llamar a `calcular_icc_transformador()` para esos campos (solo usa esa función para `Icc_nom_kA`, descartando el resto del dict con `_, _`). El mismo patrón de duplicación que ya cerramos para ATS/generador en Ciclo 0 (`f4329fb`), esta vez entre `main.py` y `transformador.py`.

**Fix:** `main.py` ahora importa `C_MAX`/`C_MIN` de `transformador.py` y los usa en vez de los literales `1.1`/`0.95`. No se tocó la estructura del bloque (sigue cubriendo tanto modo "A" como modo catálogo `icc_desde_tabla`) — cambio mínimo, mismo origen de verdad.

**Verificado con CLI real** (no solo tests, porque este bloque de `main.py` no tenía cobertura de test dedicada — otro hallazgo: es lógica inline en una función grande, sin test unitario propio): memoria regenerada sobre `circuitos.xlsx` ahora muestra `Icc bornes BT: nominal=30.39 kA, maxima=34.49 kA, minima=26.85 kA` — coherente con el texto de la propia memoria. 819 tests (808 passed + 11 skipped), `pyflakes` limpio.

**Nota:** la GUI (`gui_core/presentadores.py`) no tiene esta duplicación porque no calcula `Icc_max_kA`/`Icc_min_kA` en absoluto todavía — mismo vacío de fase 5 documentado en `06_calidad_normativa.md` y `11_ROADMAP_CONSOLIDADO.md`.
