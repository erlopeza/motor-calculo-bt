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
| P2.1 | **Flujo de carga nodal** (bus/rama + Newton-Raphson) | ETAP | Arquitectura | L–XL | ★★★ | F0 completa | 🟡 | F3 |
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

### Fase 2 — Diferenciador técnico (P1)
**Objetivo:** capacidades de alto valor que reutilizan datos ya disponibles.
- P1.1 Arc Flash IEEE 1584 (usa Icc + tiempo de despeje existentes), P1.2 librería de curvas TCC (+DATA-3), P1.3 refuerzo de coordinación.
- **Hito 2 "listo cuando":** la memoria incluye energía incidente/frontera de arco y coordinación con curvas reales de fabricante.

### Fase 3 — Análisis de red (P2) · *salto estratégico*
**Objetivo:** pasar de determinista por circuito a red acoplada.
- P2.1 refactor del modelo de datos (lista de circuitos → grafo bus/rama) + solucionador Newton-Raphson sobre `numpy`/`scipy.sparse`.
- **Hito 3 "listo cuando":** flujo de carga nodal validado contra casos de referencia; convive con el modo simplificado actual.

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
