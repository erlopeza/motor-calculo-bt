# Cierre Gestor Graficos

- Fecha: 2026-04-22
- Base commit actual: 6eac0b3
- Estado validacion: PASS (327 passed / 0 failed)

## Alcance aplicado en este cierre
- Clasificacion de constantes TIPO A/B/C en `generador.py`, `ats.py`, `ups.py`, `motores.py`.
- Nuevo modulo `sugerencias.py` con funciones de sugerencia GE, motor, cargas y deteccion de sobredimensionamiento.
- Gate de emision en `reporteria_sec.py`:
  - `verificar_completitud_parametros(resultados)`
  - `generar_memoria_sec(..., modo_emision="auto"|"final"|"borrador")`
- Tests agregados:
  - `tests/test_sugerencias.py`
  - contrato R-01 en `tests/test_parser_reporte.py`
  - tests de gate en `test_reporteria_sec.py`

## Estado G2/G7
- G2 (decremento GE) y G7 (SIMARIS) **sin flujo TXT por diseno**.
- Motivo: esos datos no viven en el reporte TXT consolidado; permanecen en flujo directo de resultados para GUI/notebook.
- Decision: mantener separados para preservar arquitectura desacoplada TXT -> parser -> graficos.
