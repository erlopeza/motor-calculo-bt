# 13 — Matriz de gobernanza técnica (primer tramo)

**Fecha:** 2026-10-02 · **Alcance:** `calculos.py` + `icc_punto.py` (los dos módulos más usados — caída de tensión y cortocircuito). Primer tramo de una matriz que, según el roadmap, se extendería a `transformador.py`, `protecciones.py`, `coordinacion.py`, `demanda.py`, `balance.py`, `motores.py`, `generador.py`, `ups.py`, `ats.py`, `arc_flash.py`, `flujo_nodal.py`.

**Formato:** una entrada por función en vez de una tabla de 14 columnas — la versión tabla resultó ilegible en markdown (línea de >300 caracteres por fila). Mismos campos que pedía el brief original: fenómeno, fórmula, variables, unidades, norma/fuente, rango de validez, supuestos, default permitido, test asociado, benchmark, estado.

**Criterio de "estado"** (más estricto que "tiene test"):
- **VALIDADO** — tiene test Y benchmark (comparación contra cálculo manual/norma/herramienta externa con tolerancia declarada).
- **PARCIAL** — tiene test, no tiene benchmark formal.
- **PENDIENTE** — sin test, o hallazgo abierto sin resolver.

De las 16 funciones auditadas, **solo 1 tiene benchmark formal**. Es la brecha más grande y honesta que deja esta matriz — consistente con lo que ya se había señalado como pendiente (`auditoria/11_ROADMAP_CONSOLIDADO.md`).

---

## calculos.py

### `calcular_potencia(I_diseno, cos_phi, sistema) -> int`
- **Fenómeno:** potencia activa de un circuito.
- **Fórmula:** P = √3·V·I·cosφ (3F) · P = V·I·cosφ (1F/2F).
- **Variables:** I_diseno [A], cos_phi [adim], sistema [1F/2F/3F]; V desde `TENSION_SISTEMA[sistema]` [V].
- **Norma/fuente:** fórmula física estándar; sin cita normativa en el código.
- **Rango/supuestos:** `sistema` debe existir en `TENSION_SISTEMA`; sin corrección por desbalance de fases.
- **Default permitido:** No.
- **Test asociado:** `tests/test_calculos.py`, `tests/test_generador.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `calcular_caida_tension(L_m, S_mm2, I_diseno, paralelos, sistema) -> (dV_V, dV_pct)`
- **Fenómeno:** caída de tensión en un tramo de conductor.
- **Fórmula:** ΔV = factor·ρ·L·I / (S·paralelos); factor = 2 (1F/2F) o √3 (3F).
- **Variables:** L_m [m], S_mm2 [mm²], I_diseno [A], paralelos [int]; ρ = `RHO_CU` = 0.0175 Ω·mm²/m (IEC 60228, 20°C).
- **Norma/fuente:** IEC 60228 (resistividad Cu); sin versión/edición citada.
- **Rango/supuestos:** **modelo puramente resistivo** (sin componente reactiva X) — a diferencia de `icc_punto.py`, que sí modela R+jX. Válido para tramos cortos; el error crece con la longitud (README ya documenta esta limitación para tramos >50 m).
- **Default permitido:** No.
- **Test asociado:** `test_calculos.py`, `test_propiedades.py` (property: ΔV>0, crece con L, decrece con paralelos), `test_caida_acumulada.py`, `test_validacion_ingenieril_rapida.py`.
- **Benchmark:** **Nivel 1 (cálculo manual)** — `test_caida_tension_trifasica_contra_formula_manual` recalcula la fórmula a mano y compara con tolerancia `abs=0.001`. Única función de esta matriz con benchmark formal.
- **Estado:** **VALIDADO.**

### `clasificar_caida(dV_pct) -> str`
- **Fenómeno:** clasificación cualitativa de ΔV (ÓPTIMO/ACEPTABLE/PRECAUCIÓN/FALLA).
- **Fórmula:** umbral, no ecuación.
- **Variables:** dV_pct [%].
- **Norma/fuente:** RIC N°10 / NCh Elec. 4/2003 (umbrales 1.5/3/5%); el umbral "ACEPTABLE" usa `LIMITE_DV` importado de `conductores.py` (acoplamiento entre módulos a tener presente).
- **Rango/supuestos:** ninguno adicional.
- **Default permitido:** No.
- **Test asociado:** `test_calculos.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `calcular_caida_acumulada(dv_alimentador_pct, dv_circuito_pct) -> dict`
- **Fenómeno:** ΔV acumulada alimentador + circuito terminal.
- **Fórmula:** ΔV_total = ΔV_alimentador + ΔV_circuito.
- **Variables:** ambos [%].
- **Norma/fuente:** RIC N°10 / NCh Elec. 4/2003; límite `DV_MAX_TOTAL_RIC_PCT` = 5.0.
- **Rango/supuestos:** suma simple; asume mismo sistema de tensión en alimentador y circuito.
- **Default permitido:** No.
- **Test asociado:** `tests/test_caida_acumulada.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `calcular_caida_alimentador(P_W, L_m, S_mm2, Vn_V, sistema, cos_phi=0.9, norma="MM2") -> dict`
- **Fenómeno:** ΔV del alimentador, derivando I_diseño desde potencia.
- **Fórmula:** I = P/(√3·V·cosφ) [3F] o P/(V·cosφ); reutiliza `calcular_caida_tension` (hereda su supuesto resistivo puro).
- **Variables:** P_W [W], L_m [m], S_mm2 [mm²], Vn_V [V], sistema, cos_phi [adim].
- **Norma/fuente:** RIC N°10.
- **Rango/supuestos:** `cos_phi=0.9` está comentado en el código como `DEFAULT_TIPICO: factor de potencia de diseno sin dato real`.
- **Default permitido:** **Sí — y no trazado.** El dict de retorno no incluye un campo `usa_defaults`, a diferencia de generador/ats/ups/motores (cerrado en `ecca4f3`). Mismo patrón H-08 que ya se corrigió en otros módulos; aquí sigue abierto.
- **Test asociado:** `tests/test_caida_acumulada.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL — **hallazgo:** default de `cos_phi` sin trazabilidad.

### `capacidad_corregida(I_max, paralelos, temp_amb) -> float`
- **Fenómeno:** ampacidad corregida por temperatura y conductores en paralelo.
- **Fórmula:** I_cap = I_max · paralelos · factor_temp(temp_amb).
- **Variables:** I_max [A], paralelos [int], temp_amb [°C]; `factor_temp` desde tabla `FACTORES_TEMP` (`conductores.py`).
- **Norma/fuente:** NEC 310.15(B)(1) (según cita en `conductores.py`, no reverificada aquí).
- **Rango/supuestos:** `FACTORES_TEMP.get(int(temp_amb), 1.0)` — **temperaturas fuera de tabla caen silenciosamente a factor 1.0**, sin advertencia ni excepción.
- **Default permitido:** No declarado como tal, pero el fallback a 1.0 es un comportamiento implícito no trazado.
- **Test asociado:** `test_calculos.py`, `test_validacion_ingenieril_rapida.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL — **hallazgo:** fallback silencioso fuera de rango de tabla.

### `sugerir_conductor(L_m, I_diseno, paralelos, sistema, temp_amb, norma="AWG") -> tuple`
- **Fenómeno:** selecciona el conductor mínimo que cumple ΔV y ampacidad.
- **Fórmula:** búsqueda (no ecuación única); usa `calcular_caida_tension` + `capacidad_corregida`.
- **Variables:** L_m [m], I_diseno [A], paralelos [int], sistema, temp_amb [°C].
- **Norma/fuente:** RIC N°10 (ΔV) + tabla de conductores (ampacidad).
- **Rango/supuestos:** hereda el supuesto resistivo puro de `calcular_caida_tension`.
- **Default permitido:** No.
- **Test asociado:** `test_calculos.py`, `test_validacion_ingenieril_rapida.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

---

## icc_punto.py

### `calcular_zt_cable(L_m, S_mm2, paralelos=1, rho=RHO_CU) -> float`
- **Fenómeno:** resistencia del cable (solo R, sin X) — función legacy de retrocompatibilidad.
- **Fórmula:** R = ρ·L / (S·paralelos).
- **Variables:** L_m [m], S_mm2 [mm²], paralelos [int], rho [Ω·mm²/m].
- **Norma/fuente:** IEC 60228.
- **Rango/supuestos:** documentado explícitamente en el docstring como "sin reactancia — para Icc usar `calcular_zt_cable_complejo`"; valida `S_mm2>0`/`paralelos>0` (`ValueError` si no).
- **Default permitido:** No.
- **Test asociado:** `test_calculos.py`, `test_impedancia_compleja.py`, `test_motor_robustez.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `calcular_zt_cable_complejo(L_m, S_mm2, paralelos=1, rho=RHO_CU) -> complex`
- **Fenómeno:** impedancia compleja del cable Z = R + jX.
- **Fórmula:** R = ρ·L/(S·paralelos); X = interpolación tabla(S)·L/1000/paralelos.
- **Variables:** igual que arriba; reactancia desde `get_reactancia_cable_ohm_km` (`conductores.py`).
- **Norma/fuente:** IEC 60909-2 Tabla B.1; edición no citada en el código.
- **Rango/supuestos:** rango de secciones de la tabla de interpolación no documentado en este módulo (depende de `conductores.py`, no auditado en este tramo).
- **Default permitido:** No.
- **Test asociado:** `test_impedancia_compleja.py`, `test_motor_robustez.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `calcular_icc_punto(Zt_trafo_ohm, L_m, S_mm2, paralelos, sistema="3F", c_max=C_MAX_IEC60909) -> tuple`
- **Fenómeno:** Icc **máxima** en un punto de la instalación, aguas abajo del transformador — alimenta la verificación de poder de corte de cada protección.
- **Fórmula (corregida hoy, ver `12_HALLAZGO_C_MAX_ICC.md`):** Icc = c_max·Vn/(√3·|Z_total|) [3F] · c_max·Vn/|Z_total+Z_retorno| [1F/2F].
- **Variables:** Zt_trafo_ohm [Ω, resistivo puro], L_m [m], S_mm2 [mm²], paralelos [int], sistema, c_max [adim, default 1.05].
- **Norma/fuente:** IEC 60909-2 Tabla B.1 (cable) + IEC 60909 §4.3.1 (factor c) — ambos consistentes entre sí desde hoy.
- **Rango/supuestos:** Z_trafo modelado **puramente resistivo** (comentario explícito en el código: "fase posterior: añadir X_trafo"); en 1F/2F el neutro se asume mismo calibre que la fase.
- **Default permitido:** Sí — `c_max=1.05`, parametrizable y declarado en la firma (no es un default oculto).
- **Test asociado:** `test_calculos.py`, `test_impedancia_compleja.py` (incluye los 3 tests nuevos de c_max), `test_aporte_motores_icc.py`, `test_motor_robustez.py`, `test_propiedades.py` (property-based).
- **Benchmark:** pendiente — candidato prioritario para un benchmark Nivel 1 dado el fix reciente.
- **Estado:** PARCIAL (buena cobertura y recién corregido/verificado end-to-end; falta benchmark formal para subir a VALIDADO).

### `calcular_icc_fase_neutro(Vn_V, Zt_fuente_ohm, L_m, S_mm2, norma="MM2", c_min=C_MIN_IEC60909) -> dict`
- **Fenómeno:** Icc **mínima** fase-neutro — alimenta la verificación de disparo de protección.
- **Fórmula:** Icc_fn = c_min·U0/|Zs|; U0 = Vn/√3; Zs = Z_fuente + Z_fase + Z_neutro.
- **Variables:** Vn_V [V], Zt_fuente_ohm [Ω, resistivo puro], L_m [m], S_mm2 [mm²], c_min [adim, default 0.95].
- **Norma/fuente:** IEC 60364-4-41 / IEC 60909 (modelo R+jX).
- **Rango/supuestos:** Z_fuente puramente resistiva (misma limitación que `calcular_icc_punto`); neutro mismo calibre que fase.
- **Default permitido:** Sí — `c_min=0.95`, parametrizable; valor correcto y consistente con IEC 60909 (no es un hallazgo).
- **Test asociado:** `test_icc_fase_neutro.py`, `test_impedancia_compleja.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `verificar_disparo_proteccion(Icc_fn_A, Ia_A, U0_V, Zs_total_ohm) -> dict`
- **Fenómeno:** condición de disparo de protección.
- **Fórmula:** Zs × Ia ≤ U0.
- **Variables:** todas en A/V/Ω.
- **Norma/fuente:** IEC 60364-4-41 cláusula 411.4.4 (citada en el propio código).
- **Rango/supuestos:** ninguno adicional.
- **Default permitido:** No.
- **Test asociado:** `test_icc_fase_neutro.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `reduccion_icc(Icc_trafo_kA, Icc_punto_kA) -> float`
- **Fenómeno:** % de reducción de Icc entre bornes y un punto.
- **Fórmula:** reducción = (1 − Icc_punto/Icc_trafo) × 100.
- **Variables:** ambos [kA].
- **Norma/fuente:** — (cálculo derivado, no normativo per se).
- **Rango/supuestos:** guarda división por cero (`Icc_trafo==0` → retorna 0.0).
- **Default permitido:** No.
- **Test asociado:** `test_calculos.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL.

### `clasificar_icc_punto(Icc_kA) -> str`
- **Fenómeno:** clasificación cualitativa del nivel de Icc (MUY BAJO…EXTREMO).
- **Fórmula:** umbral (1/6/10/25/50 kA).
- **Variables:** Icc_kA.
- **Norma/fuente:** **sin cita normativa en el código** — mismo patrón H-08 (criterio interno sin fuente documentada).
- **Rango/supuestos:** umbrales sin justificación documentada en el módulo.
- **Default permitido:** No.
- **Test asociado:** **ninguno** (verificado: cero referencias en todo `tests/`).
- **Benchmark:** pendiente.
- **Estado:** **PENDIENTE** — sin test, sin fuente normativa citada.

### `calcular_icc_con_aporte_motores(Icc_red_kA, aportes_motores_A) -> tuple`
- **Fenómeno:** Icc total = aporte de red + aporte de motores (suma escalar, peor caso).
- **Fórmula:** Icc_total = Icc_red + Σ max(aporte, 0)/1000.
- **Variables:** Icc_red_kA [kA], aportes_motores_A [lista de A].
- **Norma/fuente:** IEC 60909:2016 cláusula 3.8 (citada en el propio código).
- **Rango/supuestos:** suma escalar documentada explícitamente como "peor caso (aportes en fase)"; aportes negativos se ignoran (no reducen Icc).
- **Default permitido:** No.
- **Test asociado:** `test_aporte_motores_icc.py`.
- **Benchmark:** pendiente.
- **Estado:** PARCIAL (buena cobertura, supuesto conservador explícito; falta benchmark).

### `calcular_icc_todos_circuitos(Zt_trafo_ohm, circuitos) -> list`
- **Fenómeno:** itera `calcular_icc_punto` sobre cada circuito de una lista — **es el camino real de producción**, llamado desde `main.py` (CLI) para construir la Icc de cada circuito de toda memoria SEC.
- **Fórmula:** delega en `calcular_icc_punto` (hereda `c_max=1.05` por defecto).
- **Variables:** Zt_trafo_ohm [Ω], circuitos [lista de dicts con L_m/S_mm2/paralelos/sistema].
- **Norma/fuente:** igual que `calcular_icc_punto`.
- **Rango/supuestos:** asume que cada circuito trae `L_m`/`S_mm2`/`paralelos`/`sistema` válidos; no captura `KeyError` si falta alguno.
- **Default permitido:** No expone el parámetro `c_max` de `calcular_icc_punto` — no hay forma de usar un `c_max` distinto (ej. MT) por este camino sin modificar el código.
- **Test asociado:** **ninguno directo** (verificado) — cubierta solo indirectamente por generación real de memorias (end-to-end), no por un test unitario propio.
- **Benchmark:** pendiente.
- **Estado:** **PENDIENTE** — sin test unitario pese a ser el camino de producción real para la Icc de cada circuito.

---

## Resumen y hallazgos nuevos de este tramo

| Estado | Funciones |
|---|---:|
| VALIDADO | 1 (`calcular_caida_tension`) |
| PARCIAL | 13 |
| PENDIENTE | 2 (`clasificar_icc_punto`, `calcular_icc_todos_circuitos`) |

**Hallazgos nuevos, no reportados antes de este tramo:**
1. `calcular_caida_alimentador`: `cos_phi=0.9` es un default sin trazabilidad (`usa_defaults` no existe en su dict de retorno) — mismo patrón H-08 que ya se cerró en generador/ats/ups/motores, pero sigue abierto en `calculos.py`.
2. `capacidad_corregida`: temperaturas fuera de la tabla `FACTORES_TEMP` caen silenciosamente a factor 1.0, sin advertencia.
3. `clasificar_icc_punto` y `calcular_icc_todos_circuitos`: sin test unitario — el segundo es, además, el camino de producción real para la Icc de cada circuito en toda memoria SEC.
4. Solo **1 de 16 funciones** tiene benchmark formal — confirma que el benchmarking externo (brief original, puntos 17-18) sigue siendo la brecha más grande, no solo una percepción.

**No incluido en este tramo (continuaría la matriz si se decide seguir):** `transformador.py`, `protecciones.py`, `coordinacion.py`, `demanda.py`, `balance.py`, `motores.py`, `generador.py`, `ups.py`, `ats.py`, `arc_flash.py`, `flujo_nodal.py`.
