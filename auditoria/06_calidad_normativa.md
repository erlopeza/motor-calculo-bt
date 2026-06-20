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

## H-07 (🟡 Bajo) — Datos de fabricante hardcodeados

Documentado en [`../AUDITORIA_CICLO_0.md`](../AUDITORIA_CICLO_0.md): la tabla del alternador **Stamford HCI544D W14** (Xd_pp, Xd_p, Xd, X2, X0, Rs, Sn=625) está hardcodeada en `generador.py` (líneas ~32-35), pese a que existe `presets/alternadores/stamford_hci544d.py`. → **Mover a preset/catálogo** para evitar dos fuentes de verdad del mismo equipo.

## H-08 (🟡 Bajo) — Defaults típicos sin cita normativa

Inventariado en `AUDITORIA_CICLO_0.md`. Ejemplos con efecto de cálculo y **sin fuente citada**:

| Módulo | Constante | Valor | Observación |
|---|---|---|---|
| `generador.py` | curva de derrateo altitud | 4000/1500/0.04/300 | falta cita normativa/fabricante |
| `generador.py` | autonomía mínima combustible | 6.0 h | umbral operativo interno sin cita |
| `generador.py` | `DV_ARRANQUE_LIMITE_CRITICO` | 10.0 | umbral interno (vs. 15.0 NCh 4-2003 12.28.8 que sí está citado) |
| `generador.py` | reactancias default (Xd_pp=20, Xd_p=28, Xd=120, R1=2, X0=5) | — | el comentario indica "verificar con ficha técnica" — **defaults de máquina, no universales** |

**Riesgo:** un cálculo con defaults aplicados puede emitirse como definitivo sin que el usuario advierta que usó valores genéricos. ✅ Mitigado parcialmente por el gate `BORRADOR` de `reporteria_sec.py`, pero conviene **propagar ese gate a todos los módulos** que aplican defaults de equipo.

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

| Acción | Prioridad |
|---|---|
| Mover datos Stamford HCI544D a `presets/alternadores/` y referenciar | Media |
| Citar fuente de los defaults de altitud/autonomía o exigir entrada del usuario | Media |
| Extender el gate `BORRADOR` a todo cálculo que aplique defaults de equipo | Media |
| Añadir `ruff` + `black` y un pre-commit | Baja |
| Completar type hints y docstrings en módulos antiguos | Baja |
