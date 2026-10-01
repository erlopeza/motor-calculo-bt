# 06 — Calidad y normativa

## Trazabilidad normativa (fortaleza)

El código cita normas en comentarios y constantes de forma sistemática. Frecuencia de citas en código productivo:

| Norma | Citas | Norma | Citas |
|---|---:|---|---:|
| IEC 60364-4-41 | 23 | IEC 60947-2 | 12 |
| IEC 60909 | 21 | IEC 60364 | 12 |
| RIC-N08 | 15 | IEC 60898 | 8 |
| IEC 60076 | 14 | NCh 4-2003 | 7 |
| TIA-942 | 13 | IEC 60228 | 7 |

✅ **Destacable:** la base normativa (SEC RIC, IEC 60364/60909/60947/60076, NCh 4, TIA-942) está embebida y trazable. Es la mayor fortaleza de calidad del proyecto.

## H-10 (reclasificado a 🟢 Bajo) — Marcadores de trabajo pendiente

Los 5 hits de "BORRADOR" en `reporteria_sec.py` **no son TODOs**: son un **estado legítimo del gate de emisión documental** (`nivel: "BORRADOR"/"INCOMPLETO"/...`), que marca documentos no aptos para emisión cuando se usan parámetros por defecto. **No se encontraron TODO/FIXME/HACK/XXX reales** en el código productivo. → hallazgo cerrado favorablemente.

## H-07 (✅ Cerrado, 2026-06-19) — Datos de fabricante hardcodeados

Documentado en [`../AUDITORIA_CICLO_0.md`](../AUDITORIA_CICLO_0.md), cerrado en el commit `fb5159c`. Verificado de nuevo el 2026-10-01: `STAMFORD_HCI544D_W14` ya no existe en `generador.py` ni en `ats.py` (grep sin resultados); el preset vive solo en `presets/alternadores/stamford_hci544d.py` y `generador.py::get_parametros_alternador()` lo consume por `importlib`. Sin dato de fabricante en el core.

## H-08 (✅ Cerrado, 2026-06-19) — Defaults típicos sin cita normativa

Inventariado en `AUDITORIA_CICLO_0.md`, cerrado en el commit `fb5159c`. Verificado de nuevo el 2026-10-01:

| Módulo | Constante | Resolución |
|---|---|---|
| `generador.py` | curva de derrateo altitud | Citada: ISO 8528-1:2018 §13.4 / IEC 60034-1 §3.5 |
| `generador.py` | autonomía mínima combustible | Citada: RIC N°08 §5.3.1 (SEC Chile) |
| `generador.py` | reactancias default (Xd_pp, Xd_p, Xd, R1, X0) | Etiquetadas `# TIPO A - DEFAULT: verificar con ficha tecnica GE` — correcto: son parámetro de equipo, no citables a norma, y la etiqueta ya cumple la regla del brief Ciclo 0 ("debe llegar por input, trazado como default") |
| `generador.py` | `DV_ARRANQUE_LIMITE_CRITICO` | Etiquetada `# TIPO C - umbral interno para cargas criticas` |

**Riesgo residual (abierto):** el campo `usa_defaults` existe por función en `generador.py`/`ats.py`/`ups.py`/`motores.py` (cerrado en `ecca4f3`), pero el gate `BORRADOR`/`FINAL`/`INCOMPLETO` de `reporteria_sec.py::verificar_completitud_parametros` no lo consume — verificado el 2026-10-01, cero referencias a `usa_defaults` en `reporteria_sec.py`. Un cálculo con defaults de equipo aplicados puede emitirse como FINAL sin que el gate lo marque. **Sigue pendiente propagar `usa_defaults` al gate.**

## Otros aspectos de calidad

| Aspecto | Estado |
|---|---|
| Funciones privadas con prefijo `_` consistentes | ✅ |
| Guardas anti-división-por-cero (`1e-9`, `1e-12`) | ✅ (numéricas, no criterio eléctrico) |
| Conversiones de unidad explícitas (kVA→VA, A→kA, √3) | ✅ |
| Type hints | Parcial (presente en módulos recientes: `motores`, `ups`, `sugerencias`; ausente en antiguos) |
| Docstrings de módulo/función | Parcial e inconsistente |
| Linter/formatter (ruff/black) configurado | ❌ No (ver `07`) |

## Recomendaciones

| Acción | Prioridad | Estado |
|---|---|---|
| Mover datos Stamford HCI544D a `presets/alternadores/` y referenciar | Media | ✅ Cerrado (`fb5159c`) |
| Citar fuente de los defaults de altitud/autonomía o exigir entrada del usuario | Media | ✅ Cerrado (`fb5159c`) |
| Propagar `usa_defaults` (ya existe por función desde `ecca4f3`) al gate `BORRADOR` de `reporteria_sec.py` | Media | 🟡 Abierto |
| Añadir `ruff` + `black` y un pre-commit | Baja | 🟡 Abierto |
| Completar type hints y docstrings en módulos antiguos | Baja | 🟡 Abierto |
