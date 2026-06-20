# 03 — Higiene del repositorio y artefactos

## H-01 (🔴 Alto) — `.gitignore` corrupto a nivel de bytes

El archivo `.gitignore` es UTF-8 en su mayor parte, pero **las 4 últimas reglas están codificadas en UTF-16LE** (incrustadas como bytes nulos `\0` y saltos `\r\0\n\0`). Volcado real del final del archivo:

```
m \0 o \0 t \0 o \0 r \0 _ \0 b \0 t \0 . \0 d \0 b \0 \r \0 \n \0
0 \0 7 \0 _ \0 C \0 O \0 N \0 T \0 R \0 O \0 L \0 / \0 ...
* \0 . \0 d \0 o \0 c \0 x \0 ...
* \0 . \0 p \0 d \0 f \0 ...
```

**Consecuencia:** git interpreta esas líneas como un único patrón con bytes nulos, por lo que **las reglas para `motor_bt.db`, `07_CONTROL/`, `*.docx` y `*.pdf` NO funcionan**. Esta es la **causa raíz** de que decenas de binarios generados (H-02) hayan quedado versionados pese a la intención del commit `b9929a2` ("excluir outputs runtime — db, docx, pdf, 07_CONTROL").

✅ **Corregido:** `.gitignore` reescrito íntegramente en UTF-8 limpio, conservando todas las reglas previas como patrones funcionales y añadiendo `__pycache__/`, `*.pyc`, exclusiones de `.tmp_*`, logs y reportes generados.

## H-02 (🔴 Alto) — Artefactos generados versionados

El repo versiona **69 archivos** que son salidas/temporales y no deberían estar en control de versiones. Lista completa: [`_artefactos_a_desindexar.txt`](_artefactos_a_desindexar.txt).

| Categoría | Cantidad | Ejemplos |
|---|---|---|
| Reportes generados (`REPORTE_*.txt/.xlsx/.pdf`) | 20 | `REPORTE_LEO-ARICA-FINAL_20260321_1950.xlsx` |
| Memorias DOCX (`MEMORIA_*.docx`) | 13 | `MEMORIA_LEO-ARICA-M12_CLI_20260422_2248.docx` |
| Imágenes WhatsApp (`.jpeg`) | 5 | `WhatsApp Image 2026-04-19 at 11.53.22 PM.jpeg` |
| Bases temporales de test (`.tmp_*/`) | 11 | `.tmp_persistencia_tests/*.db` |
| Curvas PNG generadas (`07_CONTROL/`) | 4 | `07_CONTROL/curvas/.../*_tcc_*.png` |
| `__pycache__/*.pyc` | 4 | `__pycache__/calculos.cpython-313.pyc` |
| Exportes de eventos (`eventos_2026*`) | 2 | `eventos_20260418_1939.json` |
| Base de datos local | 1 | `motor_bt.db` |
| Logs de streamlit | 2 | `streamlit_out.log`, `streamlit_err.log` |

### Peso muerto
Binarios pesados versionados (Top): `Referencias/Output_sel (1).pdf` **7,8 MB**, `Referencias/Output_doc.pdf` 884 KB, `HCI5D-14-TD-EN_Rev_A.pdf` 268 KB, varias `.jpeg` 100–264 KB, 13 `MEMORIA_*.docx` (~40 KB c/u). El histórico ya contiene estos blobs (no se reduce con `rm --cached`, pero deja de crecer).

✅ **Corregido (desindexado, conservado en disco):** se ejecutó `git rm --cached` sobre los artefactos **inequívocamente generados/transitorios**: `__pycache__/`, `.tmp_*`, `streamlit_*.log`, `motor_bt.db`, `eventos_2026*`, `REPORTE_*`, `MEMORIA_*.docx`, `07_CONTROL/` y las imágenes WhatsApp. Los archivos permanecen en el disco de trabajo; solo se quitan del índice.

## H-09 (🟡 Bajo) — No tocados (requieren decisión del propietario)

| Archivo | Motivo de no removerlo |
|---|---|
| `calculo_bt.spec`, `motor_bt.spec` | `.gitignore` los excluye (`*.spec`), pero `motor_bt.spec` fue añadido **deliberadamente** (commit `68bf90d`, FASE-F). Es config de build: decide si lo versionas (entonces añade `!motor_bt.spec`) o lo ignoras. |
| `Referencias/*.pdf`, `HCI5D-14-TD-EN_Rev_A.pdf` | Son **documentos de entrada/referencia** (datasheet del alternador, estudio de coordinación), no salidas. Si quieres versionarlos, mantenlos con un `!Referencias/` explícito en `.gitignore`. |

## Verificación post-corrección
- `.gitignore` ahora es UTF-8 válido y sus reglas filtran correctamente.
- Los artefactos desindexados aparecen como `D` (staged for deletion del índice) en `git status`, **sin pérdida de archivos en disco**.
- La suite sigue en verde tras la corrección (los `.db` temporales se regeneran en cada corrida de test).
