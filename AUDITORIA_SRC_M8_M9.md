# Auditoria src/ M8-M9 - Motor BT

Fecha: 2026-05-07
Base revisada: commit 68bf90d / 386 tests

## Veredicto

| modulo | funcion | equivalente previo | veredicto | accion recomendada |
|---|---|---|---|---|
| src/arranque_motores.py | corriente_nominal | motores.py::calcular_corriente_motor | duplica | Consolidar en una sola fuente. Preferir `motores.py` como motor tecnico canonico por cubrir 1F/3F y flujo completo. |
| src/arranque_motores.py | corriente_arranque | motores.py::calcular_corriente_arranque | duplica | Mantener como fachada GUI solo si delega en `motores.py`; evitar dos defaults para factor de arranque. |
| src/arranque_motores.py | metodo_arranque | motores.py no tiene equivalente directo | coexiste | Puede mantenerse como recomendador simplificado de GUI M8. Documentar que no reemplaza calculo tecnico. |
| src/arranque_motores.py | seleccionar_guardamotor | motores.py::seleccionar_guardamotor | duplica | Consolidar rangos; hoy `src` llega hasta 63 A y `motores.py` hasta 160 A. |
| src/arranque_motores.py | calcular_arranque_completo | motores.py::calcular_motor | coexiste | Fachada simplificada para GUI. No debe considerarse reemplazo de `calcular_motor`. |
| src/sistemas_emergencia.py | clasificar_grupo | generador.py no tiene equivalente | coexiste | Mantener como M9 RIC-N08 independiente. |
| src/sistemas_emergencia.py | autonomia_requerida | generador.py::calcular_autonomia solo combustible GE | coexiste | Mantener separado: autonomia normativa RIC-N08 no es autonomia de combustible. |
| src/sistemas_emergencia.py | potencia_generador | generador.py::calcular_potencia_minima_ge | coexiste | Mantener separado: M9 calcula requerimiento basico por cargas; `generador.py` verifica GE tecnico con arranque/derrateo. |
| src/sistemas_emergencia.py | calcular_emergencia_completo | generador.py::calcular_generador | coexiste | No reemplaza `calcular_generador`; orquesta clasificacion RIC-N08 y potencia requerida. |

## Conclusion

`src/arranque_motores.py` no es una reorganizacion limpia de `motores.py`; contiene una fachada GUI M8 util, pero duplica calculos base. La limpieza futura recomendada es hacer que sus funciones base deleguen en `motores.py` y conservar solo la API ergonomica de GUI.

`src/sistemas_emergencia.py` no reemplaza a `generador.py`. Es M9 normativo RIC-N08 y puede coexistir con el calculo tecnico de generadores.
