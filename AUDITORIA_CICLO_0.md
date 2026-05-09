# Auditoría Ciclo 0 — Blindaje Paramétrico

Nota de criterio: el inventario cubre constantes de módulo, defaults de parámetros y literales numéricos hardcodeados con efecto de cálculo, validación, umbral, catálogo, unidad o formato. Los literales puramente estructurales de Python (`0`, `1`, índices, centinelas, precisiones de `round`) se listan agrupados cuando aparecen repetidamente, porque no representan criterio eléctrico, equipo ni norma.

## generador.py

### Tabla de constantes y defaults

| Línea | Nombre | Valor | Tipo | Justificación | Acción |
|---|---|---|---|---|---|
| 12-15 | POTENCIAS_ESTANDAR_IEC_KVA | 20, 30, 45, 60, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400, 500, 600, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000 | NORMATIVA | Serie de potencias estándar IEC usada para selección de GE. | mantener; citar IEC/criterio en siguiente brief |
| 18 | XD_PP_DEFAULT | 20.0 | DEFAULT_TIPICO | Reactancia subtransitoria por defecto; el comentario indica que debe verificarse con ficha técnica. | mantener temporal; reportar default |
| 19 | XD_P_DEFAULT | 28.0 | DEFAULT_TIPICO | Reactancia transitoria por defecto; debe ser parámetro de máquina real. | mantener temporal; reportar default |
| 20 | XD_DEFAULT | 120.0 | DEFAULT_TIPICO | Reactancia sincrónica por defecto; debe ser parámetro de máquina real. | mantener temporal; reportar default |
| 21 | R1_DEFAULT | 2.0 | DEFAULT_TIPICO | Resistencia porcentual por defecto; debe ser dato de máquina o ficha. | mantener temporal; reportar default |
| 22 | X0_DEFAULT | 5.0 | DEFAULT_TIPICO | Reactancia de secuencia cero por defecto; debe ser dato de máquina. | mantener temporal; reportar default |
| 23 | C_MAX_BT | 1.05 | NORMATIVA | Factor de tensión máxima BT IEC 60909-0 según comentario. | mantener |
| 24 | C_MIN_BT | 0.95 | NORMATIVA | Factor de tensión mínima BT IEC 60909-0 según comentario. | mantener |
| 26 | XD_DEFAULT_PCT | 25.0 | DEFAULT_TIPICO | Reactancia de evaluación rápida para caída de tensión en arranque. | reportar default |
| 27 | MARGEN_GE_DEFAULT | 1.25 | DEFAULT_TIPICO | Criterio conservador de diseño, no constante universal. | reportar default |
| 28 | COS_PHI_GE_DEFAULT | 0.8 | DEFAULT_TIPICO | Valor típico de alternador BT. | reportar default |
| 29 | DV_ARRANQUE_LIMITE_NORMAL | 15.0 | NORMATIVA | Límite de referencia NCh 4-2003 12.28.8 según comentario. | mantener |
| 30 | DV_ARRANQUE_LIMITE_CRITICO | 10.0 | DEFAULT_TIPICO | Umbral interno para cargas críticas. | reportar default/criterio |
| 32-35 | STAMFORD_HCI544D_W14 | 380/400/416 V; Xd_pp 0.10-0.12; Xd_p 0.14-0.17; Xd 2.93-3.51; X2 0.19-0.23; X0 0.09-0.11; Rs 0.0041; Sn 625 | DATO_FABRICANTE | Tabla de alternador Stamford HCI544D W14 en código productivo. | MOVER a preset/catálogo o fixture |
| 42-49 | _curve_multiplier | MA=12.0, D=15.0, K=11.0, C/default=10.0 | DEFAULT_TIPICO | Multiplicadores magnéticos típicos usados para verificación GE. | centralizar o documentar |
| 52 | _as_float default | 0.0 | DEFAULT_TIPICO | Fallback interno de parseo. | mantener |
| 61-69 | normalización pu/% | 10.0, 100.0, 1.0 | FISICA | Conversión dimensional entre pu y %. | mantener |
| 83, 151, 200, 237-242, 247, 262-273, 310-312, 350, 364, 493 | epsilons anti-cero | 1e-9, 1e-12 | DEFAULT_TIPICO | Guardas numéricas internas para evitar división por cero. | mantener; no son criterio eléctrico |
| 126-131 | derrateo altitud | 4000, 1500, 1.0, 0.04, 1500.0, 300.0, 0.01 | DEFAULT_TIPICO | Curva de derrateo por altitud; falta cita normativa/fabricante. | auditar fuente; reportar criterio |
| 134-138 | calcular_potencia_minima_ge defaults | factor_arranque_motor=6.0, altitud_msnm=0.0, margen=MARGEN_GE_DEFAULT | DEFAULT_TIPICO | Defaults de proyecto para arranque/altitud/margen. | reportar default |
| 244, 262-266, 277-295, 309-320, 351, 380, 493 | conversiones de unidad/fórmula | 1000.0, 100.0, sqrt(3.0), 2.0 | FISICA | Conversión VA/kVA, A/kA, porcentaje y ecuaciones trifásicas/monofásicas. | mantener |
| 268-273 | tolerancia comparación defaults | 1e-9 | DEFAULT_TIPICO | Tolerancia para detectar defaults. | mantener |
| 294-295 | Icc_max/Icc_min legado | 1.05, 0.95 | NORMATIVA | Compatibilidad usando factores IEC ya definidos. | reemplazar por constantes C_MAX_BT/C_MIN_BT |
| 300-307 | calcular_dv_arranque_ge defaults | cos_phi_motor=0.85, rendimiento_motor=0.92, Xd_pct=XD_DEFAULT_PCT | DEFAULT_TIPICO | Valores representativos de motor/GE si no se ingresan datos reales. | reportar default |
| 357-362 | interpolación consumo GE | 87.5, 75.0, 62.5, 50.0, 25.0 | DEFAULT_TIPICO | Interpolación por puntos de consumo 50/75/100%; depende de ficha del motor diesel. | exigir datos de consumo reales |
| 371 | autonomía mínima combustible | 6.0 h | DEFAULT_TIPICO | Umbral operativo interno sin cita en el módulo. | auditar fuente |
| 375-403 | protecciones modo GE | fallback curva D, proteccion 0.0, redondeos | DEFAULT_TIPICO | Fallbacks internos para poder evaluar lista incompleta. | reportar/validar entradas |
| 409-430 | calcular_generador defaults | Xd/R/X0 defaults; consumos/tanque/circuitos None | PARAM_EQUIPO | La firma permite datos reales, pero los valores omitidos son parámetros de equipo. | mantener firma; declarar defaults aplicados |

### Resumen por tipo
- FISICA: 3
- NORMATIVA: 5
- DEFAULT_TIPICO: 15
- PARAM_EQUIPO: 1
- DATO_FABRICANTE: 1
- FIXTURE_TEST: 0

### Funciones inspeccionadas
- _curve_multiplier(curva)
- _as_float(value, default=0.0)
- _norm_to_pu(x)
- _norm_r_to_pu(x)
- get_parametros_alternador(modelo, Vn_V, Sn_kVA)
- calcular_derrateo_altitud(altitud_msnm)
- calcular_potencia_minima_ge(P_demanda_kW, P_motor_max_kW, factor_arranque_motor=6.0, altitud_msnm=0.0, margen=MARGEN_GE_DEFAULT)
- verificar_ge_seleccionado(modelo_ge, P_ge_kVA_prime, P_ge_kVA_emergencia, cos_phi_ge, P_demanda_kW, P_motor_max_kW, factor_arranque_motor, altitud_msnm, regimen_uso)
- calcular_icc_ge(P_kVA, V_nominal, Xd_pp_pct=XD_PP_DEFAULT, Xd_p_pct=XD_P_DEFAULT, Xd_pct=XD_DEFAULT, R1_pct=R1_DEFAULT, Rs_ohm=None, X0_pct=X0_DEFAULT, c_max=C_MAX_BT, c_min=C_MIN_BT)
- calcular_dv_arranque_ge(P_motor_kW, factor_arranque, P_ge_kVA, V_nominal, cos_phi_motor=0.85, rendimiento_motor=0.92, Xd_pct=XD_DEFAULT_PCT)
- calcular_autonomia(P_demanda_kW, P_ge_prime_kW, consumo_100_galhr, consumo_75_galhr, capacidad_tanque_gal, consumo_50_galhr=None)
- verificar_protecciones_modo_ge(circuitos, Icc_ge_kA)
- calcular_generador(nombre, modelo_ge, P_ge_kVA_prime, P_ge_kVA_emergencia, cos_phi_ge, V_nominal, regimen_uso, P_demanda_kW, P_motor_max_kW, factor_arranque_motor, altitud_msnm, Xd_pp_pct=XD_PP_DEFAULT, Xd_p_pct=XD_P_DEFAULT, Xd_pct=XD_DEFAULT, R1_pct=R1_DEFAULT, Rs_ohm=None, X0_pct=X0_DEFAULT, consumo_100_galhr=None, consumo_75_galhr=None, capacidad_tanque_gal=None, circuitos=None)

### Hallazgos
- Stamford HCI544D está en código productivo en `STAMFORD_HCI544D_W14` y en `get_parametros_alternador()`, no en preset externo.
- `generador.py` no importa `ats.py`.
- `calcular_icc_ge()` ya es paramétrica; la deuda no es la fórmula, sino la convivencia de defaults y catálogo de fabricante dentro del módulo productivo.
- Valores que parecen físicos pero son de equipo/modelo: `Xd_pp`, `Xd_p`, `Xd`, `X2`, `X0`, `Rs_ohm`, `Sn_base_kVA` de Stamford; consumo de combustible por puntos 50/75/100 depende de ficha.

---

## ats.py

### Tabla de constantes y defaults

| Línea | Nombre | Valor | Tipo | Justificación | Acción |
|---|---|---|---|---|---|
| 10-14 | MODOS_TRANSFERENCIA | open, closed, sts, soft; textos con 100-500 ms y <4 ms | DEFAULT_TIPICO | Descripciones operativas; contienen rangos típicos en texto. | mantener; separar texto de criterio si se valida |
| 17 | SYNC_DV_MAX_PCT | 5.0 | NORMATIVA | Límite de sincronismo de tensión IEC 60947-6-1 según comentario. | mantener |
| 18 | SYNC_DF_MAX_HZ | 0.2 | NORMATIVA | Límite de sincronismo de frecuencia IEC 60947-6-1 según comentario. | mantener |
| 19 | SYNC_DFASE_MAX_DEG | 5.0 | NORMATIVA | Límite de ángulo de fase IEC 60947-6-1 según comentario. | mantener |
| 20 | T_PARALELO_MAX_MS | 200.0 | NORMATIVA | Closed transition IEC 60947-6-1 según comentario. | mantener |
| 22 | T_DETECCION_DEFAULT_MS | 3000.0 | DEFAULT_TIPICO | Lógica AMF configurable, no universal. | reportar default |
| 23 | T_ARRANQUE_GE_DEFAULT_MS | 10000.0 | DEFAULT_TIPICO | Tiempo típico de arranque GE; depende de equipo. | reportar default |
| 24 | T_ESTABILIZACION_DEFAULT_MS | 5000.0 | DEFAULT_TIPICO | Tiempo típico AVR/GE; depende de equipo. | reportar default |
| 25 | T_CIERRE_CONTACTOR_MS | 200.0 | DEFAULT_TIPICO | Tiempo típico de maniobra. | reportar default |
| 27-30 | STAMFORD_HCI544D_W14 | misma tabla que generador.py | DATO_FABRICANTE | Tabla Stamford duplicada en módulo ATS productivo. | MOVER/eliminar duplicado |
| 37-44 | _curve_multiplier | MA=12.0, D=15.0, K=11.0, C/default=10.0 | DEFAULT_TIPICO | Multiplicadores de protección duplicados respecto a generador.py. | centralizar |
| 49-57 | normalización pu/% | 10.0, 100.0, 1.0 | FISICA | Conversión dimensional entre pu y %. | mantener o reutilizar |
| 71, 124-125, 134, 147-158, 186, 267 | epsilons anti-cero | 1e-9, 1e-12 | DEFAULT_TIPICO | Guardas numéricas internas. | mantener |
| 100-107 | get_parametros_alternador round | precisión 6 | DEFAULT_TIPICO | Formato de salida de preset. | mantener si se mueve a preset |
| 112-122 | calcular_icc_ge_ats defaults | Xd=20/28/120, R1=2, X0=5, c=1.05/0.95 | DEFAULT_TIPICO/NORMATIVA | Reactancias/R son defaults de equipo; c_max/c_min son IEC 60909. | reutilizar generador.calcular_icc_ge |
| 126-166 | fórmula Icc GE | 1000.0, sqrt(3.0), 2.0, 1000.0 | FISICA | Misma física que `generador.calcular_icc_ge()`. | eliminar duplicación |
| 153-158 | detección defaults Icc | 20, 28, 120, 2, 5, 1e-9 | DEFAULT_TIPICO | Detección de parámetros omitidos. | conservar en núcleo único |
| 171-177 | fase defaults | 0.0, 0.0 | DEFAULT_TIPICO | Ángulo por defecto para sincronismo. | reportar default si se usa |
| 209-214 | calcular_tiempos_transferencia defaults | t_paralelo_ms=150.0 | DEFAULT_TIPICO | Tiempo de paralelo por defecto. | reportar default |
| 223-254 | tiempos por modo | cierre 200 ms; STS 4.0 ms; interrupción 0.0 | DEFAULT_TIPICO/NORMATIVA | STS 4 ms coincide con módulo STS; cierre es típico. | separar normativo de típico |
| 261-264 | factor_uso_max | 0.85 | DEFAULT_TIPICO | Criterio conservador de uso ATS. | reportar default |
| 286-313 | protecciones GE | 1000.0, 0.0, redondeos | FISICA/DEFAULT_TIPICO | Conversión kA/A y fallbacks de datos faltantes. | mantener; validar entradas |
| 320-343 | calcular_ats defaults | Xd/R/X0, tiempos, fase 0.0 | PARAM_EQUIPO | Son datos de equipo o ajustes de sistema cuando no se ingresan. | reportar defaults |

### Resumen por tipo
- FISICA: 3
- NORMATIVA: 5
- DEFAULT_TIPICO: 13
- PARAM_EQUIPO: 1
- DATO_FABRICANTE: 1
- FIXTURE_TEST: 0

### Funciones inspeccionadas
- _curve_multiplier(curva)
- _norm_to_pu(x)
- _norm_r_to_pu(x)
- get_parametros_alternador(modelo, Vn_V, Sn_kVA)
- calcular_icc_ge_ats(Sn_kVA, Vn_V, Xd_pp_pct=20.0, Xd_p_pct=28.0, Xd_pct=120.0, R1_pct=2.0, Rs_ohm=None, X0_pct=5.0, c_max=1.05, c_min=0.95)
- verificar_sincronizacion(V_fuente1_V, V_fuente2_V, f_fuente1_Hz, f_fuente2_Hz, fase_fuente1_deg=0.0, fase_fuente2_deg=0.0)
- calcular_tiempos_transferencia(modo, t_deteccion_ms=T_DETECCION_DEFAULT_MS, t_arranque_ge_ms=T_ARRANQUE_GE_DEFAULT_MS, t_estabilizacion_ge_ms=T_ESTABILIZACION_DEFAULT_MS, t_paralelo_ms=150.0)
- verificar_corriente_ats(I_carga_A, I_nominal_ats_A, factor_uso_max=0.85)
- verificar_protecciones_modo_ge(circuitos, Icc_ge_subtrans_kA, Icc_ge_perm_kA)
- calcular_ats(nombre, modelo_ats, I_nominal_A, V_nominal_V, modo_transferencia, I_carga_A, Sn_ge_kVA, Xd_pp_pct=20.0, Xd_p_pct=28.0, Xd_pct=120.0, R1_pct=2.0, Rs_ohm=None, X0_pct=5.0, t_deteccion_ms=T_DETECCION_DEFAULT_MS, t_arranque_ge_ms=T_ARRANQUE_GE_DEFAULT_MS, t_estabilizacion_ge_ms=T_ESTABILIZACION_DEFAULT_MS, t_paralelo_ms=150.0, V_red_V=None, V_ge_V=None, f_red_Hz=None, f_ge_Hz=None, fase_red_deg=0.0, fase_ge_deg=0.0, circuitos=None)

### Hallazgos
- Stamford HCI544D está en código productivo y duplicado respecto a `generador.py`.
- `ats.py` no recibe `icc_ge` ya calculado; recalcula Icc del generador en `calcular_icc_ge_ats()` y lo llama desde `calcular_ats()`.
- No hay import circular: `ats.py` no importa `generador.py`, y `generador.py` no importa `ats.py`.

### Hallazgo crítico — duplicación con generador.py
- Sí, `ats.py` recalcula Icc del generador.
- Lógica duplicada exacta:
  - `ats.py:47-57` duplica normalización pu/% de `generador.py:59-69`.
  - `ats.py:112-166` duplica la fórmula central de Icc de `generador.py:225-296`.
  - `ats.py:153-158` duplica detección de defaults de `generador.py:268-273`.
  - `ats.py:27-30` duplica la tabla Stamford de `generador.py:32-35`.

---

## ups.py

### Tabla de constantes y defaults

| Línea | Nombre | Valor | Tipo | Justificación | Acción |
|---|---|---|---|---|---|
| 8-14 | AUTONOMIA_MINIMA_MIN | tier1=10, tier2=10, tier3=15, tier4=15, critico=15, general=10 | NORMATIVA | Referencias TIA-942, ANSI/BICSI 002 e IEC 62040-4 según comentarios. | mantener; citar en reporte |
| 17 | AUTONOMIA_ALERTA_MIN | 10 | DEFAULT_TIPICO | Umbral interno de alerta operativa. | reportar criterio |
| 18 | AUTONOMIA_WARNING_MIN | 15 | DEFAULT_TIPICO | Umbral interno de warning. | reportar criterio |
| 26 | ETA_UPS_DEFAULT | 0.94 | DEFAULT_TIPICO | Eficiencia típica UPS online. | reportar default |
| 27 | ETA_BAT_DEFAULT | 0.85 | DEFAULT_TIPICO | Eficiencia típica banco de baterías. | reportar default |
| 28 | FACTOR_USO_MAX_UPS | 0.80 | DEFAULT_TIPICO | Criterio conservador de operación continua. | reportar default |
| 30-35 | FACTOR_TEMP_BAT | 20:1.03, 25:1.00, 30:0.97, 35:0.94, 40:0.90 | DEFAULT_TIPICO | Curva térmica simplificada para batería; no cita fabricante/norma. | auditar fuente; reportar default |
| 39-53 | interpolación temperatura | índices 0/1, precisión 4, fallback 25 | DEFAULT_TIPICO | Interpolación interna de tabla térmica. | mantener |
| 56 | verificar_capacidad_ups default | factor_uso_max=FACTOR_USO_MAX_UPS | DEFAULT_TIPICO | Criterio operativo si no se entrega factor. | reportar default |
| 62-64 | uso porcentual | 1e-9, 100.0 | FISICA | Evita división por cero y convierte a %. | mantener |
| 75-83 | calcular_banco_baterias defaults | temperatura=25.0, eta_bat=ETA_BAT_DEFAULT, mínimos 1 string/batería | DEFAULT_TIPICO | Valores típicos y clamps de banco. | reportar default |
| 93 | energía batería | 1000.0 | FISICA | Conversión Wh a kWh. | mantener |
| 104 | calcular_autonomia defaults | eta_ups=ETA_UPS_DEFAULT, nivel_infraestructura='critico' | DEFAULT_TIPICO | Eficiencia/tier por defecto. | reportar default |
| 110-116 | autonomía | 1e-9, 0.0, 60.0 | FISICA/DEFAULT_TIPICO | Conversión horas a minutos y guardas numéricas. | mantener |
| 143 | calcular_tiempo_recarga default | eta_ups=ETA_UPS_DEFAULT | DEFAULT_TIPICO | Eficiencia típica si no se ingresa. | reportar default |
| 154-156 | recarga | 1000.0, 10.0, 12.0 | DEFAULT_TIPICO | Fórmula de carga y límite 12 h; falta trazabilidad normativa. | auditar fuente; reportar criterio |
| 186-201 | calcular_ups defaults | temperatura=25.0, eta_ups=ETA_UPS_DEFAULT, eta_bat=ETA_BAT_DEFAULT | DEFAULT_TIPICO | Defaults de operación/batería. | reportar defaults |

### Resumen por tipo
- FISICA: 3
- NORMATIVA: 1
- DEFAULT_TIPICO: 14
- PARAM_EQUIPO: 0
- DATO_FABRICANTE: 0
- FIXTURE_TEST: 0

### Funciones inspeccionadas
- _factor_temp_bat(temperatura)
- verificar_capacidad_ups(P_carga_kVA, P_ups_kVA, factor_uso_max=FACTOR_USO_MAX_UPS)
- calcular_banco_baterias(n_baterias_serie, V_bat_unitaria, Ah_bat, n_strings, temperatura=25.0, eta_bat=ETA_BAT_DEFAULT)
- calcular_autonomia(P_carga_kW, E_bat_kWh, eta_ups=ETA_UPS_DEFAULT, nivel_infraestructura='critico')
- calcular_tiempo_recarga(Ah_efectivo, P_ups_kVA, V_string, eta_ups=ETA_UPS_DEFAULT)
- verificar_tipo_ups(tipo, tipo_carga)
- calcular_ups(nombre, modelo_ups, tipo_ups, P_ups_kVA, V_nominal, P_carga_kW, cos_phi_carga, tipo_carga, nivel_infraestructura, n_baterias_serie, V_bat_unitaria, Ah_bat, n_strings, temperatura=25.0, eta_ups=ETA_UPS_DEFAULT, eta_bat=ETA_BAT_DEFAULT)

### Hallazgos
- No hay marca comercial hardcodeada en `ups.py`; `modelo_ups` es texto de entrada.
- El módulo opera paramétricamente con potencia, batería, strings, temperatura y eficiencias.
- La deuda principal es trazabilidad: si se omiten `eta_ups`, `eta_bat`, `temperatura` o `factor_uso_max`, el resultado no declara defaults aplicados.
- La tabla `FACTOR_TEMP_BAT` parece criterio típico simplificado; requiere cita o marca explícita como default.

---

## motores.py

### Tabla de constantes y defaults

| Línea | Nombre | Valor | Tipo | Justificación | Acción |
|---|---|---|---|---|---|
| 14-18 | FACTORES_ARRANQUE_DEFAULT | directo=6.0, estrella_triangulo=2.0, variador=1.2, arranque_suave=2.5 | DEFAULT_TIPICO | Factores típicos de arranque; deben verificarse con placa/configuración real. | reportar default |
| 21-25 | FACTORES_ARRANQUE_RANGO | directo 5-8, estrella 1.5-2.5, variador 1-1.5, suave 1.5-3 | DEFAULT_TIPICO | Rangos típicos de validación. | documentar fuente |
| 28-33 | FACTORES_NCH_1228 | breve/intermitente/periodico/permanente con factores 0.85-1.5 y periodos 5/15/30/60/999 | NORMATIVA | Comentario indica NCh Elec 12/2003 para régimen y duración de servicio. | mantener; citar |
| 36 | DV_ARRANQUE_LIMITE_NORMAL | 15.0 | NORMATIVA | NCh 4-2003 12.28.8 según comentario. | mantener |
| 37 | DV_ARRANQUE_LIMITE_CRITICO | 10.0 | DEFAULT_TIPICO | Umbral interno para cargas sensibles. | reportar criterio |
| 45-55 | _resolver_periodo | 5, 15, 30, 60, 999 | NORMATIVA | Buckets usados por FACTORES_NCH_1228. | mantener |
| 75 | calcular_corriente_motor default | sistema='3F' | DEFAULT_TIPICO | Sistema por defecto de motor. | reportar default |
| 82-91 | corriente motor | 1000.0, 1e-9, sqrt(3.0), round 2 | FISICA | Conversión kW/W y fórmula monofásica/trifásica. | mantener |
| 94-101 | calcular_corriente_arranque default | factor_arranque=None | PARAM_EQUIPO | Si falta, se toma factor típico por tipo de arranque. | reportar default aplicado |
| 107-112 | rango/round arranque | índices 0/1, precisión 2/3 | DEFAULT_TIPICO | Validación/formatos internos. | mantener |
| 119-133 | calcular_dv_arranque | paralelos=1, 1e-9, 100.0 | FISICA/DEFAULT_TIPICO | Fórmula de caída y conversión %. | mantener |
| 153-158 | dimensionar_conductor_motor defaults | temperatura=30.0, norma='AWG' | DEFAULT_TIPICO | Temperatura/norma por defecto. | reportar default |
| 168-185 | dimensionamiento conductor | precisión 2/3 | DEFAULT_TIPICO | Formato de salida. | mantener |
| 189-196 | seleccionar_guardamotor rangos | 0.1-160 A | DEFAULT_TIPICO | Tabla de rangos comerciales genéricos de guardamotor. | mover a catálogo genérico o citar |
| 211-225 | verificar_proteccion_arranque | MA=12.0, D=15.0, K/default=11.0 | DEFAULT_TIPICO | Multiplicadores de curva usados localmente. | centralizar |
| 227-229 | requerimiento/margen | 1.25, 1e-9, 100.0 | DEFAULT_TIPICO | Margen de arranque 125%; falta cita. | auditar fuente |
| 250-265 | calcular_motor defaults | S_mm2_conductor=None, proteccion_A=None, curva='MA', factor_arranque=None, temperatura=30.0, Icc_punto=None, norma='AWG' | DEFAULT_TIPICO/PARAM_EQUIPO | Defaults operativos; conductor/protección/factor son datos de proyecto cuando existen. | reportar defaults |

### Resumen por tipo
- FISICA: 2
- NORMATIVA: 3
- DEFAULT_TIPICO: 12
- PARAM_EQUIPO: 2
- DATO_FABRICANTE: 0
- FIXTURE_TEST: 0

### Funciones inspeccionadas
- _normalizar_arranque(tipo_arranque)
- _resolver_periodo(periodo_min)
- _factor_temperatura(temperatura)
- _buscar_por_mm2(tabla, s_mm2)
- calcular_corriente_motor(P_kW, V_nominal, cos_phi, rendimiento, sistema='3F')
- calcular_corriente_arranque(I_n, tipo_arranque, factor_arranque=None)
- calcular_dv_arranque(I_arranque, L_m, S_mm2, sistema, V_nominal)
- dimensionar_conductor_motor(I_n, regimen, periodo_min, temperatura=30.0, norma='AWG')
- seleccionar_guardamotor(I_n)
- verificar_proteccion_arranque(I_arranque, proteccion_A, curva, Icc_punto=None)
- calcular_motor(nombre, P_kW, V_nominal, cos_phi, rendimiento, sistema, tipo_arranque, regimen, periodo_min, L_m, S_mm2_conductor=None, proteccion_A=None, curva='MA', factor_arranque=None, temperatura=30.0, Icc_punto=None, norma='AWG')

### Hallazgos
- No hay dato de fabricante ni marca comercial.
- El módulo usa defaults típicos de arranque y guardamotor; son aceptables solo si el resultado declara que se usaron.
- La lógica de protección de arranque (`MA=12`, `D=15`, `K=11`) existe también en generador/ATS con variantes; conviene centralizar o documentar como criterio común.
- `motores.py` importa `calculos.py` y `conductores.py`, pero no importa `generador.py`, `ats.py` ni `ups.py`.

---

## Conclusiones para Ciclo 0

1. Módulos que requieren modificación: `generador.py`, `ats.py`, `ups.py`, `motores.py`.
2. Módulos limpios (no requieren cambio): ninguno queda completamente limpio para Ciclo 0, porque todos tienen al menos deuda de trazabilidad de defaults. `ups.py` y `motores.py` no requieren separación de marca/fabricante.
3. Stamford HCI544D ubicación actual:
   - `generador.py:32-35`: tabla `STAMFORD_HCI544D_W14`.
   - `generador.py:73-121`: `get_parametros_alternador()` usa esa tabla en runtime.
   - `ats.py:27-30`: tabla duplicada `STAMFORD_HCI544D_W14`.
   - `ats.py:61-109`: `get_parametros_alternador()` duplicado.
4. Duplicación ATS↔generador: SÍ.
   - `ats.py:112-166` duplica el núcleo de `generador.py:225-296`.
   - `ats.py:47-57` duplica normalización pu/% de `generador.py:59-69`.
   - `ats.py:27-30` duplica Stamford de `generador.py:32-35`.
5. Defaults sin trazabilidad:
   - `generador.py`: 15 grupos de defaults/criterios detectados; ya expone `usa_defaults` solo en `calcular_icc_ge()`, no en todo el orquestador.
   - `ats.py`: 13 grupos; expone `usa_defaults` solo en `calcular_icc_ge_ats()`, no en tiempos ni orquestador.
   - `ups.py`: 14 grupos; no expone `usa_defaults`.
   - `motores.py`: 12 grupos; no expone `usa_defaults`.
6. Conteo total por categoría:
   - FISICA: 11
   - NORMATIVA: 14
   - DEFAULT_TIPICO: 54
   - PARAM_EQUIPO: 4
   - DATO_FABRICANTE: 2
   - FIXTURE_TEST: 0
7. Hallazgos críticos:
   - Stamford está en producción y duplicado, no aislado como preset/fixture.
   - ATS recalcula Icc de generador en vez de reutilizar el núcleo universal.
   - Hay múltiples defaults de equipo/proyecto que permiten cálculo sin declarar trazabilidad.
   - UPS no está amarrado a Vertiv; el riesgo es trazabilidad de defaults, no marca.
   - Motores no está amarrado a fabricante; el riesgo es trazabilidad y centralización de criterios repetidos.
