# 09 — Informe técnico de funciones del proyecto

Referencia funcional del **núcleo de cálculo** (módulos productivos no-GUI/no-test). Para cada módulo: propósito, API pública y base normativa. Las líneas citadas corresponden al commit base `7c6e2a5`.

> Convención: `calcular_X` = motor de cálculo; `verificar_X` = chequeo normativo (devuelve apto/no apto + margen); `clasificar_X` = etiqueta cualitativa; `reporte_X` = render textual; `leer_X_excel` = ingreso desde planilla.

---

## 1. Conductores y caída de tensión

### `conductores.py`
| Función | Firma | Propósito |
|---|---|---|
| `get_tabla_conductores` | `(norma: str) -> dict` | Devuelve la tabla de conductores (sección mm² y capacidad A) según norma `AWG` o `MM2`. Fuente: NEC Table 310.15 / IEC 60228. |

### `calculos.py`
| Función | Firma | Propósito / Norma |
|---|---|---|
| `calcular_potencia` | `(I_diseno, cos_phi, sistema)` | Potencia activa (W) por sistema 1F/2F/3F. |
| `calcular_caida_tension` | `(L_m, S_mm2, I_diseno, paralelos, sistema)` | Caída de tensión (V y %) — modelo resistivo Cu. |
| `clasificar_caida` | `(dV_pct)` | Clasifica ÓPTIMO/ACEPTABLE/PRECAUCIÓN/FALLA (umbrales 1.5/3/5 %). |
| `calcular_caida_acumulada` | `(...)` | ΔV acumulada a lo largo de la cadena de circuitos. |
| `calcular_caida_alimentador` | `(...)` | ΔV del alimentador principal. |
| `capacidad_corregida` | `(I_max, paralelos, temp_amb)` | Corrige capacidad por temperatura (NEC 310.15(B)(1)) y paralelos. |
| `sugerir_conductor` | `(L_m, I_diseno, paralelos, sistema, temp_amb, norma="AWG")` | Selecciona conductor mínimo que cumple ΔV y ampacidad. |

---

## 2. Transformador y cortocircuito

### `transformador.py`
| Función | Firma | Propósito / Norma |
|---|---|---|
| `calcular_icc_transformador` | `(kVA, Vn_BT, Ucc_pct, ...)` | Icc en bornes BT del trafo (IEC 60909, factores c_max/c_min). |
| `icc_desde_tabla` | `(kVA)` | Icc de referencia por potencia normalizada. |
| `clasificar_icc` | `(Icc_kA)` | Etiqueta de nivel de Icc. |
| `reporte_transformador` | `(datos, modo, Icc_kA)` | Render del bloque transformador. |

### `icc_punto.py`
| Función | Firma | Propósito / Norma |
|---|---|---|
| `calcular_zt_cable` | `(L_m, S_mm2, paralelos=1, rho=RHO_CU)` | Impedancia del tramo de cable. |
| `calcular_icc_punto` | `(Zt_trafo_ohm, L_m, S_mm2, paralelos, sistema="3F")` | Icc en un punto aguas abajo. |
| `calcular_icc_fase_neutro` | `(...)` | **Icc fase-neutro (IEC 60364-4-41)** — bucle de falla y tiempo de desconexión. |
| `verificar_disparo_proteccion` | `(...)` | Verifica que la protección dispare ante la Icc mínima. |
| `reduccion_icc` | `(Icc_trafo_kA, Icc_punto_kA)` | % de reducción de Icc por impedancia de cable. |
| `clasificar_icc_punto` | `(Icc_kA)` | Etiqueta de Icc en punto. |
| `calcular_icc_todos_circuitos` | `(Zt_trafo_ohm, circuitos)` | Icc por punto para toda la lista de circuitos. |

---

## 3. Protecciones y coordinación

### `protecciones.py`
| Función | Firma | Propósito / Norma |
|---|---|---|
| `calcular_umbral_magnetico` | `(In_A, curva)` | Umbral de disparo magnético por curva B/C/D/K/MA (IEC 60898/60947-2). |
| `verificar_disparo` | `(Icc_punto_A, In_A, curva)` | ¿Dispara el magnético ante la Icc del punto? |
| `verificar_poder_de_corte` | `(Icc_punto_kA, poder_de_corte_kA)` | Verifica capacidad de ruptura. |
| `clasificar_margen_disparo` | `(margen_pct)` | Clasifica el margen de disparo. |
| `verificar_tiempo_desconexion` | `(Icc_punto_A, In_A, curva, Vn)` | Tiempo de desconexión vs. límite normativo. |
| `verificar_circuito_completo` | `(nombre, In_A, curva, poder_corte_kA, ...)` | Verificación integral de la protección de un circuito. |
| `leer_protecciones_excel` | `(libro_openpyxl)` | Ingreso de protecciones desde Excel. |

### `coordinacion.py`
| Función | Firma | Propósito / Norma |
|---|---|---|
| `calcular_tiempo_disparo` | `(Icc_A, In_A, curva, ...)` | Tiempo de disparo según curva (para TCC). |
| `verificar_selectividad_par` | `(resultado_inferior, resultado_superior)` | Selectividad entre dos dispositivos en serie. |
| `verificar_iec60364` | `(t_disparo_s, sistema="3F_380")` | Cumplimiento de tiempos IEC 60364. |
| `verificar_cadena` | `(dispositivos, Icc_A, sistema="3F_380")` | Selectividad de la cadena completa. |
| `reporte_coordinacion` | `(resultado_cadena, nombre_cadena="Cadena")` | Render de coordinación. |

---

## 4. Demanda y balance

### `demanda.py`
| Función | Firma | Propósito / Norma |
|---|---|---|
| `obtener_fd` | `(tipo_instalacion, tipo_carga)` | Factor de demanda por tipo (RIC). |
| `calcular_fd_alumbrado_ric` | `(P_alumbrado_kW) -> dict` | FD de alumbrado según RIC. |
| `calcular_demanda_mixta` | `(...)` | Demanda combinada de cargas heterogéneas. |
| `calcular_demanda` | `(circuitos, balance_datos, params_demanda)` | Demanda total de la instalación. |
| `calcular_corriente_alimentador` | `(S_kva, Vn, sistema)` | Corriente del alimentador. |
| `seleccionar_transformador` | `(S_demanda_kva, factor_uso=USO_TRAFO_OPTIMO)` | Selección de trafo por demanda. |
| `dimensionar_acometida_sec` | `(S_demanda_kva, Vn, sistema, zona="urbana")` | Acometida según criterio SEC. |
| `reporte_demanda` | `(resultado_demanda, resultado_trafo=None, ...)` | Render de demanda. |

### `balance.py`
| Función | Firma | Propósito |
|---|---|---|
| `obtener_fs` | `(tipo_carga)` | Factor de simultaneidad. |
| `calcular_potencia_circuito` | `(I_diseno, cos_phi, sistema, Vn_sistema)` | Potencia por circuito. |
| `calcular_balance_tableros` | `(circuitos, balance_datos, tableros_datos, ...)` | Balance de fases por tablero. |
| `reporte_balance` | `(resultado)` | Render del balance. |

---

## 5. Motores (M8)

### `motores.py` — base NCh 4-2003 12.28
| Función | Firma | Propósito |
|---|---|---|
| `calcular_corriente_motor` | `(...)` | Corriente nominal del motor (1F/3F). |
| `calcular_corriente_arranque` | `(...)` | Corriente de arranque por factor. |
| `calcular_dv_arranque` | `(...)` | ΔV durante arranque (límite NCh 12.28). |
| `dimensionar_conductor_motor` | `(...)` | Conductor del motor. |
| `seleccionar_guardamotor` | `(...)` | Guardamotor (rango hasta 160 A). ⚠ duplicado en `src/arranque_motores.py` con rango distinto (ver H-04). |
| `verificar_proteccion_arranque` | `(...)` | Verifica protección frente al arranque. |
| `calcular_motor` | `(...)` | Orquestador completo del cálculo de motor. |

---

## 6. Generación de emergencia (M9 / GE)

### `generador.py` — IEC 60909, NCh 4-2003, derrateo altitud
| Función | Firma | Propósito |
|---|---|---|
| `get_parametros_alternador` | `(...)` | Devuelve parámetros del alternador (Xd_pp/Xd_p/Xd/X0/Rs). ⚠ datos Stamford HCI544D hardcodeados (H-07). |
| `calcular_derrateo_altitud` | `(altitud_msnm) -> float` | Factor de derrateo por altitud (⚠ sin cita, H-08). |
| `calcular_potencia_minima_ge` | `(...)` | Potencia mínima del GE por cargas + arranque + margen. |
| `verificar_ge_seleccionado` | `(...)` | Verifica el GE elegido contra requerimiento. |
| `calcular_icc_ge` | `(...)` | Icc aportada por el generador. |
| `calcular_dv_arranque_ge` | `(...)` | ΔV de arranque alimentado por GE. |
| `calcular_autonomia` | `(...)` | Autonomía por combustible (⚠ mínimo 6 h sin cita, H-08). |
| `verificar_protecciones_modo_ge` | `(...)` | Protecciones en modo GE (Icc reducida). |
| `calcular_generador` | `(...)` | Orquestador completo del GE. |

### `src/sistemas_emergencia.py` — M9 RIC-N08 (coexiste, no duplica)
`clasificar_grupo`, `autonomia_requerida`, `potencia_generador`, `calcular_emergencia_completo` — clasificación normativa RIC-N08 (distinta del cálculo técnico de `generador.py`).

---

## 7. Continuidad de servicio (M11/M12): STS, UPS, Trafo aislamiento, ATS

### `sts.py` — transferencia estática, topología 2N
`verificar_capacidad_sts`, `verificar_transferencia`, `verificar_overload`, `verificar_redundancia_2N`, `verificar_carga_no_lineal`, `calcular_sts`.

### `ups.py` — banco de baterías, autonomía (TIA-942 / IEC 62040)
`verificar_capacidad_ups`, `calcular_banco_baterias`, `calcular_autonomia`, `calcular_tiempo_recarga`, `verificar_tipo_ups`, `calcular_ups`.

### `trafo_iso.py` — transformador de aislamiento (IEC 60076)
`verificar_capacidad_trafo`, `calcular_corriente_nominal`, `calcular_icc_secundario`, `calcular_dv_trafo`, `calcular_trafo_iso`.

### `ats.py` — transferencia automática y sincronización
`verificar_sincronizacion`, `calcular_tiempos_transferencia`, `verificar_corriente_ats`, `verificar_protecciones_modo_ge`, `calcular_ats`. (Reutiliza el cálculo de `generador.py` — commit `f4329fb`.)

---

## 8. Perfiles, sugerencias y soporte

| Módulo | Funciones clave | Propósito |
|---|---|---|
| `perfiles.py` | `obtener_perfil`, `validar_perfil_vs_datos`, `icc_empalme_sec`, `hay_bloqueo` | Perfiles INDUSTRIAL/DATACENTER/COMERCIAL + validación y bloqueo de selector. |
| `sugerencias.py` | `sugerir_parametros_por_perfil`, `sugerir_parametros_ge`, `sugerir_parametros_motor`, `sugerir_carga_por_nombre`, `detectar_sobredimensionamiento` | Recomendador de parámetros y detección de sobredimensionamiento. |

---

## 9. I/O, persistencia y reportería

| Módulo | Funciones clave | Propósito |
|---|---|---|
| `excel.py` (34 def) | lectura de hojas (circuitos, cadena, demanda, ...) + export con formato/colores | Toda la I/O Excel. |
| `persistencia.py` (10 def) | capa SQLite sobre `schema.sql` (3 tablas) | Persistencia de corridas/eventos. |
| `exportar_eventos.py` | export JSON/CSV de eventos | Exportación de eventos EPC. |
| `parser_reporte.py` | parsing de reportes de texto | Lectura de reportes generados. |
| `reporteria_sec.py` (22 def) | reporte SEC DOCX/PDF + **gate de emisión** (`BORRADOR`/`INCOMPLETO`) | Reporte normativo SEC; controla emisión cuando hay defaults. |
| `graficos.py` (12 def) | curvas TCC, ΔV, autonomía (matplotlib/numpy) | Generación de gráficos. |
| `src/generador_memoria.py` (16 def) | memoria explicativa DOCX | Documento explicativo del cálculo. |

---

## 10. Subsistemas auxiliares

| Paquete | Propósito |
|---|---|
| `commissioning/` (P1 continuidad, P2 motores, P3 transferencia, P4 Icc, reporte) | Protocolo de puesta en marcha. |
| `simulaciones/` (analizador, escenarios, reporte) | Escenarios de simulación y análisis de divergencias. |
| `rag_normativa/` (extractor, chunker, indexador, consultor, referencias_iec) | RAG sobre corpus IEC/NCh/TIA — ⚠ deps de embeddings no instaladas en el entorno auditado (ver `07`). |
| `presets/alternadores/stamford_hci544d.py` | Preset de alternador (destino recomendado para H-07). |

---

## Orquestación

`main.py` ensambla el reporte invocando `generar_seccion_{transformador,motores,generador,sts,trafo_iso,ups,ats}` y expone CLI (`--proyecto`, `--excel`, ...). `gui.py` / `gui/*` proveen la interfaz tkinter. `calculo_bt.py` actúa como fachada de cálculo. Ver acoplamiento y recomendaciones en [`04_modulos_funciones.md`](04_modulos_funciones.md).
