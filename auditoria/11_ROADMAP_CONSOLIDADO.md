# 11 — Roadmap consolidado

**Fecha:** 2026-06-19 · **Rama:** `main` · **Commit base:** `7c6e2a5`

Este documento **consolida** en un solo plan: (a) los hallazgos de la auditoría integral (reportes [00](00_RESUMEN_EJECUTIVO.md)–[09](09_informe_tecnico_funciones.md)) y (b) el análisis comparativo contra **ETAP 22 Demo** con su tabla de factibilidad ([10](10_comparativa_ETAP.md)). Define un backlog unificado, su secuenciación por fases y los criterios de "hecho".

---

## 1. Tesis del plan

`motor-calculo-bt` es un **automatizador de cálculo y memoria SEC (Chile) para BT**, sólido en su núcleo (480 tests verdes) pero con **deuda periférica** (higiene, docs, duplicación) y **brechas de exactitud** frente a un análisis eléctrico defendible. ETAP marca el techo de amplitud, pero **no es el objetivo**: el plan prioriza **cerrar exactitud y consolidar base** antes que perseguir amplitud, y reserva el "salto a análisis de red" (flujo nodal) como hito estratégico posterior.

**Regla de oro de secuenciación:** los *habilitadores* (CI, consolidación, docs) van **antes o en paralelo** a cualquier nueva capacidad de cálculo, para no propagar deuda al crecer.

---

## 2. Backlog unificado

IDs: `H-*` = hallazgo de auditoría · `P*` = capacidad funcional (ETAP gap). Estado: ✅ hecho (sesión) · 🟡 pendiente · ⏸️ diferido.
Esfuerzo S/M/L/XL · Valor ★–★★★.

| ID | Ítem | Origen | Tipo | Esfuerzo | Valor | Depende de | Estado | Fase |
|---|---|---|---|---|---|---|---|---|
| H-01 | `.gitignore` reescrito (UTF-8) | Auditoría | Higiene | S | ★★ | — | ✅ (sin commit) | F0 |
| H-02 | Desindexar 64 artefactos generados | Auditoría | Higiene | S | ★★ | H-01 | ✅ (sin commit) | F0 |
| H-03 | Reescribir README (real + sin escape) | Auditoría | Docs | M | ★★ | — | ✅ sesión | F0 |
| H-05 | Unificar layout de tests bajo `tests/` + `conftest.py` | Auditoría | Calidad | M | ★★ | — | ✅ sesión | F0 |
| H-06 | `pyproject.toml` + CI (pytest en cada push/PR) | Auditoría | Infra | M | ★★★ | — | ✅ sesión | F0 |
| H-04 | Consolidar duplicación `src/`↔raíz (delegar en `motores.py`) | Auditoría | Refactor | M | ★★ | H-06 | ✅ sesión | F0 |
| H-07 | Mover datos Stamford HCI544D a `presets/` | Auditoría | Calidad | S | ★ | — | ✅ sesión | F0 |
| H-08 | Citar/parametrizar defaults sin fuente (altitud, autonomía) | Auditoría | Normativa | S | ★★ | — | ✅ sesión | F0 |
| H-09 | Resolver `*.spec` duplicado e identidad git | Auditoría | Higiene | S | ★ | — | ✅ sesión | F0 |
| P0.1 | **Impedancia compleja de cable (R+jX)** en Icc/ΔV | ETAP | Exactitud | S | ★★★ | DATA-1 | ✅ sesión | F1 |
| P0.2 | **Aporte de motores al cortocircuito** | ETAP | Exactitud | M | ★★★ | DATA-2 | ✅ sesión | F1 |
| P0.3 | Declarar **rango de validez** en la memoria SEC | ETAP | Exactitud | S | ★★ | — | ✅ sesión | F1 |
| P1.1 | **Arc Flash IEEE 1584-2002** (modelo BT) | ETAP | Diferenciador | M | ★★★ | P0.1, coordinacion.py | ✅ sesión | F2 |
| P1.2 | **Librería de curvas TCC** (IEC 60898 + IEC 60255 IDMT) | ETAP | Diferenciador | M | ★★★ | DATA-3 | ✅ sesión | F2 |
| P1.3 | Refuerzo de coordinación (márgenes, back-up) | ETAP | Diferenciador | S–M | ★★ | P1.2 | ✅ sesión | F2 |
| P2.1 | **Flujo de carga nodal** (bus/rama + Newton-Raphson) | ETAP | Arquitectura | L–XL | ★★★ | F0 completa | ✅ sesión | F3 |
| P3.x | Ground Grid (IEEE 80) · DC · ANSI SC · Armónicos | ETAP | Expansión | M–L | ★–★★ | mercado | ⏸️ | F4 |
| — | Transitorios · OPF · RA · VFD/PV | ETAP | — | XL | ★ | — | ❌ descartado | — |
| DATA-1 | Tabla de reactancia X por conductor (IEC 60909-2 / NEC Ch.9) | Insumo | Datos | S | — | — | ✅ sesión | F1 |
| DATA-2 | Reactancias subtransitorias típicas de motores | Insumo | Datos | S | — | — | ✅ sesión | F1 |
| DATA-3 | Catálogo de curvas de protección (JSON/Excel) | Insumo | Datos | M | — | — | ✅ sesión | F2 |

---

## 3. Plan por fases

### Fase 0 — Saneamiento y base (habilitadores) · *en curso*
**Objetivo:** dejar el repo limpio, documentado y con red de seguridad (CI) antes de crecer.
- Commitear lo ya hecho (H-01, H-02) + ejecutar H-03, H-05, H-06, H-04, H-07, H-08, H-09.
- **Hito 0 "listo cuando":** README refleja el alcance real; tests unificados y verdes en CI; sin duplicación de cálculo `src/`↔raíz; `pyproject.toml` instalable.

### Fase 1 — Exactitud (P0) · *máximo retorno por esfuerzo*
**Objetivo:** que lo que ya se calcula sea más preciso y defendible.
- P0.1 reactancia de cable (+DATA-1), P0.2 aporte de motores (+DATA-2), P0.3 rango de validez.
- **Hito 1 "listo cuando":** Icc y ΔV usan impedancia compleja con contribución de motores; cada memoria declara supuestos y límites de validez; tests de regresión cubren los nuevos cálculos.

### Fase 2 — Diferenciador técnico (P1) · ✅ completada e integrada
**Objetivo:** capacidades de alto valor que reutilizan datos ya disponibles.
- P1.1 Arc Flash IEEE 1584 (usa Icc + tiempo de despeje existentes), P1.2 librería de curvas TCC (+DATA-3), P1.3 refuerzo de coordinación.
- **Hito 2 "listo cuando":** ✅ la memoria SEC incluye una sección de Arco Eléctrico (energía incidente, frontera, categoría EPP) — barra principal + tabla por circuito — con el tiempo de despeje evaluado en la corriente de arco Ia (puente `arc_flash_desde_proteccion`). La región térmica de coordinación usa fuente única de `k` (catálogo TCC). Ya no son motores aislados: están **integrados a `reporteria_sec` y a la GUI**.
- **Validación:** ejecutado end-to-end sobre datos reales **LEO-ARICA** conformados al formato canónico (`tests/fixtures/leo_arica.xlsx`, `tests/test_integracion_leo_arica.py`). El código es genérico (multi-proyecto); LEO-ARICA entra solo como dato.
- **Insumo descartado:** importador DWG/DXF — el spike mostró que los schedules viven como objetos OLE opacos; la vía correcta es el Excel fuente (ver spec `docs/superpowers/specs/2026-06-22-arc-flash-tcc-memoria-design.md`).

### Fase 3 — Análisis de red (P2) · *salto estratégico* · ✅ completada
**Objetivo:** pasar de determinista por circuito a red acoplada.
- P2.1 ✅ `flujo_nodal.py`: modelo bus/rama + Y-bus + solver Newton-Raphson polar sobre `numpy` denso (suficiente para redes BT < 100 buses; `scipy.sparse` queda como mejora futura para redes grandes).
- **Hito 3 "listo cuando":** ✅ flujo de carga nodal con balance de potencia y pérdidas por rama verificados (33 tests); convive con el modo simplificado actual sin tocarlo.
- **Integración (2026-06-23):** ✅ `red_desde_cadena.py` traduce la hoja `cadena` (árbol `upstream` + Icc por nodo) a un `Red`: topología multinivel, impedancia de rama desde la escalera de Icc, cargas agregadas en hojas por peso de `In`. El flujo nodal ya **no es un motor aislado**: tiene sección en la memoria SEC (perfil de tensiones por barra + pérdidas) y bloque en `exportar_json_epc`, validado sobre la cadena real de `circuitos.xlsx`. Spec: `docs/superpowers/specs/2026-06-23-flujo-nodal-multinivel-design.md`.

### Fase 4 — Expansión opcional (P3) · *según mercado*
Ground Grid (IEEE 80), sistemas DC (datacenter), ANSI SC, armónicos — solo si la demanda lo justifica.

---

## 4. Secuencia recomendada (orden de ejecución)

```
F0 (saneamiento)  ──►  F1 (exactitud P0)  ──►  F2 (diferenciador P1)  ──►  F3 (flujo nodal P2)  ──►  F4 (expansión P3)
   │                       │                        │
   └─ commit H-01/H-02     └─ DATA-1, DATA-2         └─ DATA-3
      H-03 README             P0.1/P0.2/P0.3            P1.1/P1.2/P1.3
      H-06 CI + pyproject
      H-04 consolidar src/
```

- **No empezar F1 sin CI (H-06):** cada cambio de cálculo necesita garantía automática de no-regresión.
- **DATA-1/2/3** son insumos compartidos: curarlos temprano desbloquea varias tareas.
- **F3 (flujo nodal)** solo tras F0 completa (refactor seguro requiere base consolidada).

---

## 5. Decisión inmediata sugerida

El siguiente paso concreto y de mayor retorno es **cerrar Fase 0 y arrancar P0.1 (reactancia de cable)**:
1. Commitear higiene ya hecha (H-01, H-02) + comparativa/roadmap.
2. Añadir `pyproject.toml` + workflow CI (H-06).
3. Implementar P0.1 con TDD (tabla DATA-1 + migración a `complex` en `icc_punto.py`/`calculos.py`).

> Documento de planificación, solo lectura sobre el código. No se modificó código fuente; las acciones ✅ corresponden a la corrección de higiene de la auditoría base (en working tree, sin commit).

---

## 6. Adenda — estado post-F3 (2026-07-11)

Este documento quedó congelado al cierre de F3. Trabajo posterior, fuera del backlog original pero en la misma línea de "consolidar antes de crecer":

- **Endurecimiento del motor** (rama `hardening/motor-aristas`, mergeada): lectores de Excel y calculadores protegidos contra datos malformados/faltantes (antes crasheaban con `ZeroDivisionError`/`KeyError`/`ValueError`); suite de tests basados en propiedades (`hypothesis`) añadida como capa complementaria de fuzz sobre los invariantes físicos.
- **Limpieza de módulos** (rama `cleanup/modulos`, mergeada): eliminado el monolito legado `calculo_bt.py` (muerto, cero importadores); imports sin uso y f-strings sin placeholder corregidos; `pyflakes` en cero para todos los módulos no-GUI.
- **Rediseño de GUI en dos planes** (ambos mergeados a `main`):
  - Plan 1 — `gui_core/`: núcleo lógico sin tkinter (`SesionProyecto`, registro de 18 módulos en 7 fases, presentadores que orquestan el motor existente), 100 % testeable sin display.
  - Plan 2 — `gui/`: capa visual Tkinter sobre `gui_core` (paleta Tokyo Night, navegación por fase, `AppBT`); `gui.py` pasó a ser un lanzador delgado; se retiraron las sub-ventanas `Toplevel` viejas (arranque/emergencia/guiada/reporte).
  - Plan 3-A — `gui/app.py` + `gui/componentes.py`: render de resultados no tabulares (Icc trafo, balance, demanda, flujo nodal, reporte); antes solo cambiaban el badge, ahora muestran fichas clave-valor/tabla y, en el caso del reporte, rutas de archivo + botón "Abrir carpeta". Registro `RENDER` reemplaza `_COLUMNAS`; `PanelModulo` gana `mostrar_fichas`/`agregar_accion`/`limpiar_resultados`.
  - Pendiente documentado (no bloqueante): paneles de parámetros de entrada para fase 5 (Emergencia) — candidato a un Plan 3-B futuro.
- **Mejoras al dashboard técnico** (rama `feat/dashboard-mejoras`, mergeada): `dashboard.py` (Streamlit) nunca se había probado en todo el ciclo de rediseño de GUI — al hacerlo se encontró y corrigió un bug real de mojibake (doble-encoding UTF-8/cp1252) que dejaba ilegible toda la interfaz, y comparando el diseño contra herramientas técnicas equivalentes (MLflow/W&B, CI/CD, ETAP, Grafana) surgieron 6 huecos: rutas DOCX/PDF ocultas, `commit_hash` sin link, timestamp crudo, validación de ruta de DB incompleta (corregidos como P0); sin filtro de fecha, sin alineación visual con el resto del proyecto (agregados como P1, con paleta Tokyo Night vía `.streamlit/config.toml`). `pandas`/`streamlit` pasaron a ser dependencias declaradas (extra `dashboard`). Coordinar los gráficos nativos con la paleta de estado queda diferido a P2 (requeriría migrar a Altair).

**F4 (Ground Grid, DC, ANSI SC, armónicos) sigue diferido**, sin cambios respecto a la decisión original: solo se retoma si el mercado lo justifica.

**Estado actual (2026-08-02):** 795 tests (784 passed + 11 skipped), `pyflakes` limpio en todo el repo, sin `TODO`/`FIXME` pendientes. GUI y dashboard verificados en runtime real (drive end-to-end con Excel real, `.exe` PyInstaller empaquetado arranca sin errores, dashboard corrido con Streamlit real y las 4 mejoras confirmadas en el navegador).
