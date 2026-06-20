# Auditoría Integral — Motor de Cálculo BT

**Fecha:** 2026-06-19
**Rama auditada:** `main` (sincronizada con `origin/main`, working tree limpio al iniciar)
**Commit base:** `7c6e2a5` (Ciclo 1 A-5 Icc fase-neutro IEC 60364-4-41)
**Alcance:** repositorio completo — git, estructura, módulos, funciones, tests, calidad/normativa, dependencias, documentación, artefactos.
**Tipo:** auditoría no destructiva (solo lectura + ejecución de tests) **+ corrección de higiene autorizada** (`.gitignore` y desindexado de artefactos) **+ informe técnico de funciones**.

---

## Veredicto global

El **núcleo de cálculo es sólido**: 53 módulos productivos (~14.200 LOC), una suite de **480 tests que pasa al 100 % en 23,9 s**, arquitectura modular por dominio (transformador, Icc, protecciones, coordinación, demanda, motores, generador, STS, UPS, ATS, trafo de aislamiento) y un estilo de commits trazable por ciclos/módulos.

Los problemas son **periféricos pero numerosos y de fácil corrección**: el repositorio está **contaminado con artefactos generados** (reportes, memorias DOCX/PDF, imágenes, bases de datos temporales, `__pycache__`), el **`.gitignore` está corrupto a nivel de bytes** (mezcla UTF-8/UTF-16) y el **README está obsoleto y no renderiza**. Hay además **duplicación de cálculo conocida** entre `src/` y módulos raíz, y **ausencia total de packaging/CI/conftest**.

| Dimensión | Estado | Severidad máx. |
|---|---|---|
| Núcleo de cálculo y tests | 🟢 Sólido | — |
| Git / commits / ramas | 🟢 Correcto | Bajo |
| Higiene del repo / artefactos | 🔴 Deficiente | **Alto** |
| Módulos y funciones | 🟡 Bueno con duplicación | Medio |
| Tests (suite) | 🟢 Verde 480/480 | Bajo |
| Calidad / normativa | 🟡 Aceptable con deuda | Medio |
| Dependencias / empaquetado | 🟡 Riesgo de entorno | Medio |
| Documentación | 🔴 Obsoleta | **Alto** |

---

## Hallazgos priorizados

| ID | Severidad | Hallazgo | Evidencia | Acción |
|---|---|---|---|---|
| H-01 | 🔴 Alto | `.gitignore` corrupto: las 4 últimas reglas (`motor_bt.db`, `07_CONTROL/`, `*.docx`, `*.pdf`) están en UTF-16LE dentro de un archivo UTF-8 → patrones inertes | `03_higiene_artefactos.md` | **Corregido** en esta auditoría (reescrito UTF-8) |
| H-02 | 🔴 Alto | 60+ artefactos generados versionados (REPORTE_*, MEMORIA_*.docx, *.pdf, *.jpeg, .tmp_*, `__pycache__`, `motor_bt.db`, logs) | `auditoria/_artefactos_a_desindexar.txt` | **Desindexados** (git rm --cached, conservados en disco) |
| H-03 | 🔴 Alto | README describe v1.0 obsoleta (4 módulos; "no calcula cortocircuito"/"no verifica coordinación") y su Markdown está escapado (`\#`, `\*`) → no renderiza | `08_documentacion.md` | Reescritura recomendada (no ejecutada) |
| H-04 | 🟠 Medio | Duplicación de cálculo `src/arranque_motores.py` ↔ `motores.py` y solapamiento `src/sistemas_emergencia.py` ↔ `generador.py` | `AUDITORIA_SRC_M8_M9.md`, `04_modulos_funciones.md` | Consolidar; `src/` debe delegar |
| H-05 | 🟠 Medio | Doble layout de tests: 12 `test_*.py` en raíz + 26 en `tests/`, sin `conftest.py`/`pytest.ini` | `05_tests.md` | Unificar bajo `tests/` |
| H-06 | 🟠 Medio | Sin packaging (`pyproject.toml`), sin CI, sin pin de `numpy/matplotlib`, deps ML pesadas (`torch`/`chromadb`) declaradas pero no instaladas | `07_dependencias_empaquetado.md` | Añadir pyproject + CI; separar extras RAG |
| H-07 | 🟡 Bajo | Datos de fabricante (alternador Stamford HCI544D) hardcodeados en `generador.py` | `AUDITORIA_CICLO_0.md`, `06_calidad_normativa.md` | Mover a `presets/` (ya existe `presets/alternadores/`) |
| H-08 | 🟡 Bajo | Defaults típicos sin cita normativa (derrateo altitud, autonomía 6 h, límites ΔV) | `06_calidad_normativa.md` | Documentar fuente o exigir entrada |
| H-09 | 🟡 Bajo | `*.spec` versionados pese a estar en `.gitignore`; 2 identidades git con el mismo email | `02_git_commits_ramas.md`, `03_higiene_artefactos.md` | Decisión del propietario (no se tocó) |
| H-10 | 🟡 Bajo | 5 marcadores TODO/FIXME/BORRADOR en código productivo | `06_calidad_normativa.md` | Triar y resolver |

---

## Acciones ejecutadas en esta auditoría
1. ✅ `.gitignore` reescrito en UTF-8 limpio, con reglas funcionales (H-01).
2. ✅ Artefactos generados desindexados con `git rm --cached` (conservados en disco) (H-02).
3. ✅ Suite ejecutada: **480 passed in 23.94s** — ver `05_tests.md` y `_pytest_output.txt`.

> **Sin commit.** Todos los cambios quedan en el working tree para tu revisión, según lo acordado.

## Acciones recomendadas (no ejecutadas — requieren decisión)
- Reescribir README (H-03) y actualizar "Limitaciones" + estructura real.
- Consolidar duplicación `src/` ↔ raíz (H-04) y unificar layout de tests (H-05).
- Añadir `pyproject.toml`, `conftest.py` y un workflow de CI (H-06).
- Mover datos de fabricante a `presets/` y citar fuentes normativas (H-07, H-08).

---

## Índice de reportes
| Archivo | Contenido |
|---|---|
| [01_inventario.md](01_inventario.md) | Estructura, paquetes, métricas del repo |
| [02_git_commits_ramas.md](02_git_commits_ramas.md) | Historial, convención de commits, ramas, remoto |
| [03_higiene_artefactos.md](03_higiene_artefactos.md) | `.gitignore`, artefactos versionados, binarios |
| [04_modulos_funciones.md](04_modulos_funciones.md) | Mapa de módulos, duplicación, acoplamiento |
| [05_tests.md](05_tests.md) | Ejecución real, layout, cobertura |
| [06_calidad_normativa.md](06_calidad_normativa.md) | Hardcodes, defaults, citas normativas, TODOs |
| [07_dependencias_empaquetado.md](07_dependencias_empaquetado.md) | requirements, PyInstaller, CI, riesgos |
| [08_documentacion.md](08_documentacion.md) | README, docs, notas |
| [09_informe_tecnico_funciones.md](09_informe_tecnico_funciones.md) | **Informe técnico de funciones del proyecto** |
| [10_comparativa_ETAP.md](10_comparativa_ETAP.md) | Comparativa funciones/usabilidad vs. ETAP 22 + factibilidad |
| [11_ROADMAP_CONSOLIDADO.md](11_ROADMAP_CONSOLIDADO.md) | **Roadmap consolidado** (hallazgos + ETAP + plan por fases) |
