# 04 — Módulos y funciones

## Distribución de funciones/clases por módulo (Top)

| def/class | Módulo | Rol |
|---:|---|---|
| 47 | `gui.py` | GUI monolítica tkinter |
| 34 | `excel.py` | I/O Excel + export |
| 23 | `rag_normativa/indexador.py` | indexado embeddings |
| 22 | `reporteria_sec.py` | reporte SEC DOCX/PDF |
| 17 | `gui/guiada_window.py` | asistente guiado |
| 16 | `src/generador_memoria.py` | memoria explicativa |
| 14 | `generador.py` | verificación GE |
| 12 | `motores.py` / `graficos.py` | arranque motores / curvas |
| 10 | `persistencia.py` / `calculo_bt.py` | SQLite / fachada |
| 8–9 | `demanda.py`, `ups.py`, `sugerencias.py`, `main.py`, `calculos.py` | — |

## Acoplamiento y altitud

- **`main.py` (1137 LOC)** concentra el ensamblado de reporte (`generar_seccion_*` por cada dominio) + CLI argparse. Es el principal punto de acoplamiento: conoce todos los módulos de cálculo. Aceptable como orquestador, pero crece linealmente con cada módulo nuevo. → candidato a dividir `generar_seccion_*` en un paquete `reporte/`.
- **`gui.py` (1812 LOC)** monolítico coexiste con el paquete `gui/`. Migración incompleta GUI monolítica → modular.
- Los módulos de cálculo de dominio (`transformador`, `icc_punto`, `protecciones`, `coordinacion`, `motores`, `generador`, `sts`, `ups`, `ats`, `trafo_iso`) están **bien aislados**: cada uno expone `calcular_X(...)` + verificaciones + `reporte_X`. Esta es la fortaleza arquitectónica del proyecto.

## H-04 (🟠 Medio) — Duplicación conocida `src/` ↔ raíz

Confirmado y documentado en [`../AUDITORIA_SRC_M8_M9.md`](../AUDITORIA_SRC_M8_M9.md):

| `src/` | Equivalente raíz | Veredicto |
|---|---|---|
| `arranque_motores.py::corriente_nominal` | `motores.py::calcular_corriente_motor` | **duplica** |
| `arranque_motores.py::corriente_arranque` | `motores.py::calcular_corriente_arranque` | **duplica** |
| `arranque_motores.py::seleccionar_guardamotor` | `motores.py::seleccionar_guardamotor` | **duplica** (rangos distintos: src llega a 63 A, motores.py a 160 A) |
| `arranque_motores.py::calcular_arranque_completo` | `motores.py::calcular_motor` | coexiste (fachada GUI) |
| `sistemas_emergencia.py` (M9 RIC-N08) | `generador.py` (GE técnico) | coexiste (dominios distintos) |

**Riesgo:** dos implementaciones de `seleccionar_guardamotor` con **rangos de catálogo diferentes** pueden devolver protecciones distintas para la misma entrada según qué módulo invoque la GUI. → **Consolidar:** que la fachada `src/` delegue en `motores.py`.

## Funciones potencialmente sin uso / huérfanas

- `simulaciones/escenarios.py` y varios `__init__.py` tienen 0 defs (módulos de datos/paquete) — esperado.
- `transformador.py::icc_desde_tabla` y `protecciones`/`generador` exponen helpers `_*` privados consistentes.
- No se detectó código muerto evidente a nivel de módulo; un análisis de cobertura (`pytest --cov`) cuantificaría líneas no ejercitadas (recomendado, ver `05_tests.md`).

## Recomendaciones

| Acción | Prioridad |
|---|---|
| Hacer que `src/arranque_motores.py` delegue en `motores.py` (eliminar cálculo duplicado) | Alta |
| Unificar rango de `seleccionar_guardamotor` (catálogo único) | Alta |
| Extraer `generar_seccion_*` de `main.py` a un paquete `reporte/` | Media |
| Decidir GUI monolítica (`gui.py`) vs. modular (`gui/`) y eliminar la obsoleta | Media |
| Renombrar `src/` a algo descriptivo (`fachada_gui/`) o integrarlo | Baja |
