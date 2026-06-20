# 08 — Documentación

## H-03 (🔴 Alto) — README obsoleto y mal renderizado

### Problema 1: Markdown escapado → no renderiza
Cada carácter especial del README está **escapado con barra invertida**: `\#`, `\*\*`, `\-`, `\## `, `\### `. En un visor Markdown (GitHub) esto se muestra **literal** (`\# Motor de Cálculo BT`) en lugar de aplicar el formato. El archivo se ve roto en GitHub.

### Problema 2: Contenido desactualizado respecto al estado real
El README describe la **versión 1.0** (2026-03-21), pero el proyecto evolucionó a ~14.200 LOC con 12+ módulos. Discrepancias críticas:

| README dice | Realidad del código |
|---|---|
| "Estructura del proyecto": solo `conductores.py, calculos.py, excel.py, main.py` | 53 módulos productivos (transformador, icc_punto, protecciones, coordinacion, demanda, motores, generador, sts, ups, ats, trafo_iso, RAG, GUI, commissioning...) |
| **"No calcula corriente de cortocircuito"** | `icc_punto.py`, `transformador.py`, `calcular_icc_fase_neutro` (IEC 60364-4-41) **sí lo hacen** |
| **"No verifica coordinación de protecciones"** | `coordinacion.py`, `protecciones.py` **sí lo hacen** |
| "Desarrollado con: openpyxl, PyInstaller" | 12 dependencias incl. docx, reportlab, matplotlib, RAG (llama-index/chroma) |
| Historial: solo v1.0 | 76 commits, M1–M12, ciclos 0/1 |
| Instalación: `pip install openpyxl` | requiere `requirements.txt` completo |

**Conclusión:** el README **induce a error** sobre las capacidades del producto (niega features que sí existen). Riesgo alto para un usuario nuevo o para el propio mantenimiento.

## Documentación interna (fortalezas)

| Documento | Estado |
|---|---|
| `AUDITORIA_CICLO_0.md` | ✅ Inventario detallado de constantes/defaults — excelente |
| `AUDITORIA_SRC_M8_M9.md` | ✅ Análisis de duplicación src/ ↔ raíz — excelente |
| `docs/NOTA-CICLO-0-BLINDAJE.md` | ✅ Nota técnica |
| `NOTA_OBSIDIAN_CIERRE_GESTOR_GRAFICOS.md` | ✅ Nota de cierre |
| `ifo-graficos/CONTEXTO-GRAFICOS-MOTOR-BT.md` | ✅ Contexto de gráficos |
| `rag_normativa/corpus/iec_ref/*.md` | ✅ Corpus normativo estructurado |

La **documentación técnica interna es de buena calidad**; el problema está concentrado en el README de cara al usuario.

## Recomendaciones

| Acción | Prioridad |
|---|---|
| Reescribir el README desde cero en Markdown **sin escapar** | Alta |
| Actualizar capacidades reales (Icc, coordinación, GE, UPS, STS, ATS, RAG) | Alta |
| Reemplazar la sección "Limitaciones actuales" (ya no aplica) | Alta |
| Sustituir "Estructura del proyecto" por la estructura real (ver `01_inventario.md`) | Alta |
| Documentar dependencias completas y modo de ejecución (CLI/GUI) | Media |
| Mover las auditorías (`AUDITORIA_*.md`) a `auditoria/` para centralizar | Baja |
