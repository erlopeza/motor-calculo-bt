# 10 — Auditoría comparativa: `motor-calculo-bt` vs. ETAP

**Fecha:** 2026-06-19
**Tipo:** comparativa de **funciones y usabilidad** — solo lectura.
**Sujeto A (propio):** `motor-calculo-bt` (commit base `7c6e2a5`).
**Sujeto B (referencia):** `C:\ETAP Demo` — **ETAP 22.x, edición Demo** (DLLs Sep-2023; carpeta `Formats2200`; `etap_overview.pdf` 2019).

> **Naturaleza del sujeto B:** ETAP es software **comercial closed-source** (~900 MB de DLL/EXE compilados .NET/nativos; `etaps64.exe` ≈ 143 MB). **No hay código fuente que auditar**; la comparación "a nivel de funciones" se hace por **conjunto de módulos de análisis** (cada motor de cálculo es un ejecutable/DLL con nombre identificable) y por **capacidades**, no por lectura de funciones Python. La parte de usabilidad se basa en arquitectura del producto, librerías, ejemplos y flujo de trabajo observados en disco.

---

## 1. Veredicto comparativo (resumen)

Son **dos clases de herramienta distintas**, no competidoras directas:

- **ETAP** = plataforma integral de análisis de sistemas de potencia (PSA) de grado industrial: ~35 motores de cálculo, modelado de red completo (unifilar), solucionadores iterativos, dinámica/transitorios, librerías validadas y aceptación regulatoria mundial.
- **`motor-calculo-bt`** = utilitario **focalizado** en verificación/cálculo de instalaciones BT y **generación automática de memoria/reporte conforme a SEC RIC (Chile)**, con entrada Excel y salida documental.

ETAP **supera ampliamente en amplitud y profundidad de análisis**. `motor-calculo-bt` **gana en su nicho**: cumplimiento normativo chileno (SEC RIC / NCh), automatización del entregable, costo cero, transparencia/auditabilidad de fórmulas y simplicidad de flujo. No es realista ni necesario que `motor-calculo-bt` "alcance" a ETAP; el valor está en cubrir lo que ETAP **no** automatiza (la memoria SEC) con una fracción del costo y la complejidad.

| Dimensión | ETAP 22 Demo | motor-calculo-bt | Ventaja |
|---|---|---|---|
| Amplitud de análisis | ~35 módulos | ~12 dominios | **ETAP** |
| Profundidad de cálculo | Solucionadores de red iterativos, dinámica | Cálculo determinista por circuito/equipo | **ETAP** |
| Normativa local (SEC RIC / NCh Chile) | No específica | **Nativa** | **motor-calculo-bt** |
| Entregable (memoria/reporte SEC) | Reporte genérico | **Automatizado y a medida** | **motor-calculo-bt** |
| Costo / licencia | Comercial (alto) | **Libre / propio** | **motor-calculo-bt** |
| Transparencia de fórmulas | Caja negra | **Código abierto y auditable** | **motor-calculo-bt** |
| Curva de aprendizaje | Alta | Baja | **motor-calculo-bt** |
| Validación / aceptación industrial | Estándar de facto | Propia (480 tests) | **ETAP** |

---

## 2. Comparativa función por función (módulos de análisis)

Mapeo de los motores de ETAP (identificados por EXE/DLL) frente a los módulos de `motor-calculo-bt`:

| Análisis | ETAP (módulo/binario) | motor-calculo-bt | Cobertura propia |
|---|---|---|---|
| **Flujo de carga (Load Flow)** | `LF3PH.exe`, `lfnr.exe` (Newton-Raphson), `lfgs.exe` (Gauss-Seidel), `lffd.exe` (Fast-Decoupled), `lfle.exe` | `demanda.py`, `balance.py`, `calculos.py` (caída acumulada) | **Parcial** — cálculo de demanda/ΔV por circuito y acumulada, sin solucionador de red iterativo ni balance de potencia nodal |
| **Cortocircuito IEC 60909** | `sciec1p.exe`, `sciec3p.exe`, `sciectr.exe`, `scsource.exe` | `transformador.py`, `icc_punto.py` (c_max/c_min) | **Sí (BT)** — Icc en trafo y por punto; alcance BT, sin aporte dinámico de máquinas |
| **Cortocircuito fase-tierra (IEC 60364-4-41)** | incluido en SC IEC | `icc_punto.py::calcular_icc_fase_neutro` | **Sí** — bucle de falla y tiempo de desconexión |
| **Cortocircuito ANSI/IEEE** | `scansi1p.exe`, `scansi3p.exe` | — | **No** (enfoque IEC/SEC) |
| **Coordinación de protecciones / Star (TCC)** | DLLs de relé/coordinación, `EtapPlotLib`, curvas TCC | `protecciones.py`, `coordinacion.py`, `graficos.py` (TCC) | **Sí (básico)** — selectividad de cadena, tiempos IEC 60364, curvas; sin biblioteca de relés ni curvas de fabricante extensas |
| **Arranque de motores (Motor Starting)** | `ms.exe`, `etload64`, `etmtrupd64` | `motores.py` (NCh 4-2003 12.28, ΔV arranque) | **Sí (estático)** — corriente/ΔV de arranque, guardamotor; sin perfil dinámico de aceleración temporal |
| **Estabilidad transitoria (Transient Stability)** | `ts.exe` | — | **No** |
| **Armónicos** | `harmonic.exe`, `HarmonicRPG.exe`, `ethf64` (filtros) | — (UPS/STS evalúan carga no lineal cualitativa) | **No** |
| **Flujo óptimo (OPF)** | `opf.exe` | — | **No** |
| **Sistemas DC (load flow / SC)** | `dccalc.exe`, `etdc*64` (bus, breaker, máquina, fusible, cargador, convertidor) | — | **No** (AC BT) |
| **Confiabilidad (Reliability)** | `ra.exe` | — | **No** |
| **Ubicación óptima de capacitores** | `OCP.exe` | — | **No** |
| **Arc Flash (IEEE 1584)** | `EtArcFlash64.dll` | — | **No** |
| **Dimensionamiento de baterías (IEEE 485)** | `etbatt64.dll` | `ups.py::calcular_banco_baterias` | **Parcial** — banco/autonomía BT |
| **Cargador / UPS** | `etcharg64`, `etups64` | `ups.py` (TIA-942 / IEC 62040) | **Sí (BT)** |
| **Ampacidad / dimensionamiento de cables** | `etcb64`, tablas `Cable_Sizing`, `CablePulling` | `conductores.py`, `calculos.py::sugerir_conductor` (AWG/MM2, derrateo temp.) | **Sí (BT)** — sin pulling/derrateo por agrupamiento avanzado |
| **Transformadores** | modelado en LF/SC + `etpe64` | `transformador.py`, `trafo_iso.py` | **Sí (BT)** |
| **Generador / Grupo electrógeno** | modelado en LF/SC/TS | `generador.py` (derrateo altitud, autonomía, Icc GE), `ats.py` | **Sí (especializado)** — verificación GE + transferencia |
| **VFD / Inversores / PV** | `etvfd64`, `etinvert64` | — | **No** |
| **Ground Grid (IEEE 80)** | `GRDData64`, `GRDREP64` | — | **No** |
| **Perfiles de carga** | `etprofile64`, `ProfileLibrary.SDF` | `perfiles.py` (INDUSTRIAL/DATACENTER/COMERCIAL) | **Sí (simplificado)** |
| **Cumplimiento normativo SEC (Chile) + memoria** | No nativo | **`reporteria_sec.py`, `src/generador_memoria.py` (DOCX/PDF)** | **Exclusivo de motor-calculo-bt** |

**Lectura:** de ~20 familias de análisis de ETAP, `motor-calculo-bt` cubre ~9 con alcance **BT y determinista** (cortocircuito IEC, coordinación, arranque de motores, cables, trafo, GE/ATS, UPS/batería, demanda, perfiles) y **agrega una capa que ETAP no tiene**: generación automática de la memoria SEC chilena. No aborda: ANSI SC, transitorios, armónicos, OPF, DC, confiabilidad, arc flash, ground grid, VFD/PV.

---

## 3. Profundidad de cálculo (diferencia metodológica clave)

| Aspecto | ETAP | motor-calculo-bt |
|---|---|---|
| Modelo de red | Topología completa (unifilar) con buses/ramas; solucionador iterativo (NR/GS/FD) | Lista de circuitos; cálculo **determinista por circuito** y caída acumulada en cadena |
| Cortocircuito | Aporte de todas las fuentes (red, máquinas, motores) con decremento AC/DC | Icc desde trafo + reducción por impedancia de cable (modelo resistivo Cu) |
| Dinámica | Sí (estabilidad transitoria, arranque temporal) | No (verificación estática de ΔV de arranque) |
| Reactancia de cable | Sí | **No** (declarado: válido cables < 200 m en BT) |
| Validación | Suite interna + 30+ años de uso industrial | **480 tests unitarios** (verde), trazabilidad normativa en commits |

**Implicación:** `motor-calculo-bt` es válido y suficiente para su dominio declarado (instalaciones BT, cables cortos, verificación normativa), pero **no modela la red como sistema acoplado** — su precisión depende de que las simplificaciones (sin reactancia de cable, sin acoplamiento nodal) sean aceptables para el caso.

---

## 4. Usabilidad

### ETAP 22 Demo
| Fortalezas | Limitaciones |
|---|---|
| Editor de diagrama unifilar gráfico; modelado visual de toda la planta | **Curva de aprendizaje alta**; requiere formación |
| Librerías validadas (cables, relés, ANSI/IEC) — `Tables/` con ANSI-1ph/3ph/LG, Cable_Sizing | **Costo de licencia alto**; la versión Demo limita tamaño de red/funciones |
| Casos de estudio y ejemplos listos (`Example-ANSI/IEC/New`) | **Solo Windows**, instalación pesada (~900 MB), dependencias COM/.NET |
| Reportería extensa (Crystal/Syncfusion/PDF), co-simulación (PSCAD/OPAL-RT) | Caja negra: fórmulas no auditables por el usuario |
| Estándar de facto → aceptación ante terceros/auditorías | Sobredimensionado para un cálculo BT puntual |

### motor-calculo-bt
| Fortalezas | Limitaciones |
|---|---|
| **Flujo simple**: Excel de entrada → reporte/memoria automáticos | GUI tkinter básica (monolítico `gui.py` 1812 LOC, ver `04`) |
| **Entregable SEC listo** (DOCX/PDF) con gate de emisión BORRADOR | Sin diagrama unifilar ni modelado visual de red |
| Costo cero, portable como `.exe` (PyInstaller) | Documentación de usuario obsoleta (README, ver `08`) |
| Transparencia total: fórmulas y normas citadas en código | Cobertura de análisis acotada a BT determinista |
| Bajo tiempo de adopción para el caso de uso chileno | Sin librerías de fabricante ni validación de terceros |

---

## 5. Conclusiones y recomendaciones

1. **No son sustitutos.** ETAP es la herramienta de modelado/análisis integral; `motor-calculo-bt` es un **automatizador de cumplimiento y memoria SEC** para BT. Conviven: se puede modelar/verificar en ETAP y **emitir la memoria SEC con `motor-calculo-bt`**.
2. **Nicho defendible.** El diferenciador real de `motor-calculo-bt` (memoria SEC automatizada + normativa chilena + costo cero + transparencia) **no existe en ETAP**. Es ahí donde debe concentrar su evolución, no en perseguir módulos de ETAP.
3. **Mejoras de alto valor / bajo costo** para acercarse en credibilidad sin competir en amplitud:
   - Incorporar **reactancia de cable** opcional para Icc/ΔV (hoy es una limitación declarada) → mayor precisión y defensa técnica.
   - Adjuntar **curvas TCC con biblioteca de relés/fabricantes** (ya hay base en `graficos.py`/`coordinacion.py`).
   - Documentar explícitamente el **rango de validez** (BT, cables cortos, sin acoplamiento nodal) en el reporte, para que el alcance quede claro frente a un revisor acostumbrado a ETAP.
4. **Si se busca interoperar:** evaluar import/export hacia formatos de ETAP o intercambio Excel compatible, para usar `motor-calculo-bt` como capa de cumplimiento sobre modelos hechos en ETAP.

---

## 6. Factibilidad de implementación (qué de ETAP conviene y es viable incorporar)

Evaluación de cada capacidad ausente o parcial en `motor-calculo-bt`, considerando el stack actual (Python 3.13, `numpy`/`matplotlib`/`openpyxl`, arquitectura determinista por circuito). Escalas: **Esfuerzo** S/M/L/XL · **Complejidad** Baja/Media/Alta · **Valor eléctrico** ★–★★★.

| Capacidad (ETAP) | Estado propio | Esfuerzo | Complejidad | Datos/dependencias nuevas | Valor eléctrico | Factibilidad | Prioridad |
|---|---|---|---|---|---|---|---|
| **Reactancia de cable (R+jX) en Icc/ΔV** | Ausente (solo R) | **S** | Baja | Tabla X por conductor (IEC 60909-2 / NEC Ch.9); `complex` nativo | ★★★ | **Muy alta** — reutiliza `icc_punto.py`/`calculos.py` | **P0** |
| **Aporte de motores al cortocircuito** | Ausente | M | Media | Reactancia subtransitoria de motores (ya hay patrón en `generador.py`) | ★★★ | Alta — sumar fuentes en Icc | **P0** |
| **Declarar rango de validez en el reporte** | Implícito | **S** | Baja | Texto + checks de límites | ★★ | Trivial; alto impacto de credibilidad | **P0** |
| **Arc Flash (IEEE 1584-2018)** | Ausente | M | Media | Fórmulas empíricas; **ya se tiene Icc + tiempo de despeje** de `coordinacion.py` | ★★★ | **Alta** — encaja con datos existentes; gran valor de seguridad | **P1** |
| **Librería de curvas TCC (relés/fabricantes)** | Base en `graficos.py` | M | Media | Catálogo de curvas (JSON/Excel) por dispositivo | ★★★ | Alta — extiende coordinación existente | **P1** |
| **Coordinación: márgenes y back-up reforzados** | Básico (`coordinacion.py`) | S–M | Media | — | ★★ | Alta | **P1** |
| **Flujo de carga nodal (bus/rama, Newton-Raphson)** | Determinista por circuito | **L–XL** | Alta | Modelo topológico de red + solucionador (`numpy`/`scipy.sparse`) | ★★★ | Media — salto arquitectónico, pero `numpy` ya está | **P2** |
| **Sistemas DC (load flow / SC)** | Ausente | L | Media | Modelos DC (batería/cargador/converter) | ★★ (datacenter) | Media | **P2/P3** |
| **Ground Grid (IEEE 80)** | Ausente | M | Media | Fórmulas IEEE 80 (malla, GPR, paso/contacto) | ★★ | Alta — módulo autónomo | **P3** |
| **Cortocircuito ANSI/IEEE** | Ausente (IEC sí) | M | Media | Método ANSI paralelo al IEC | ★ (fuera de SEC/Chile) | Media | **P3** |
| **Armónicos** | Ausente | L | Alta | Modelo en frecuencia + espectros de carga | ★★ | Baja-Media | **P3** |
| **Estabilidad transitoria / dinámica** | Ausente | **XL** | Alta | Integrador de EDOs + modelos dinámicos máquina | ★★ | **Baja** — desproporcionado al nicho | **Descartar** |
| **OPF / Confiabilidad (RA) / VFD-PV** | Ausente | L–XL | Alta | Optimizadores / modelos específicos | ★ | Baja | **Descartar (por ahora)** |

**Criterio rector:** priorizar lo que **(a)** aumenta la **exactitud y defendibilidad** de lo que ya se calcula y **(b)** reutiliza datos/módulos existentes, antes que perseguir amplitud. Lo de alto esfuerzo y bajo encaje con el nicho SEC-BT (transitorios, OPF, RA) se descarta o difiere.

---

## 7. Necesidades inmediatas para completar el motor (en pro del análisis eléctrico)

Roadmap priorizado. Las **P0** cierran brechas de exactitud sobre cálculos ya existentes (máximo valor por esfuerzo); las **P1** suman el diferenciador técnico; las **P2+** son expansión.

### P0 — Cierre de exactitud (semanas, esfuerzo S–M)
1. **Impedancia compleja de cable (R+jX).** Añadir tabla de reactancia por conductor y migrar `icc_punto.py`/`calculos.py` a aritmética `complex`. Elimina la limitación declarada "no incluye reactancia inductiva" y mejora Icc y ΔV en alimentadores largos.
2. **Aporte de motores al cortocircuito.** Sumar la contribución subtransitoria de motores a la Icc en el punto de falla (dato ya modelable; patrón presente en `generador.py`).
3. **Rango de validez explícito en el reporte SEC.** Declarar supuestos (BT, cables cortos, sin acoplamiento nodal) y validar límites de entrada — credibilidad frente a un revisor acostumbrado a ETAP.

### P1 — Diferenciador técnico (1–2 meses, esfuerzo M)
4. **Arc Flash IEEE 1584-2018.** Energía incidente y frontera de aproximación a partir de la Icc y el tiempo de despeje que ya entrega `coordinacion.py`. Alto valor de seguridad; encaje natural con los datos existentes.
5. **Librería de curvas TCC por dispositivo** (catálogo JSON/Excel de relés/interruptores) integrada a `graficos.py`/`coordinacion.py`, para coordinación con curvas reales de fabricante.
6. **Refuerzo de coordinación:** márgenes de selectividad, verificación de respaldo (back-up) y reporte gráfico TCC en la memoria.

### P2 — Salto a "análisis de red" (proyecto mayor, esfuerzo L–XL)
7. **Solucionador de flujo de carga nodal** (modelo bus/rama + Newton-Raphson sobre `numpy`/`scipy.sparse`). Convierte el utilitario determinista por circuito en un analizador de red acoplada — el mayor acercamiento real a ETAP. Requiere refactor del modelo de datos (hoy lista de circuitos → grafo de buses).

### P3 — Expansión opcional (según mercado)
8. Ground Grid (IEEE 80), sistemas DC (datacenter), ANSI SC, armónicos — solo si el mercado objetivo lo demanda.

### Habilitadores transversales (de la auditoría base — bloquean la "completitud" real)
- **Consolidar duplicación `src/`↔raíz** (H-04) y **unificar layout de tests** (H-05) antes de crecer en funciones, para no propagar deuda.
- **`pyproject.toml` + CI** (H-06): sin CI, cada nueva capacidad de cálculo se integra sin garantía automática de no-regresión.
- **README actualizado** (H-03): hoy niega features que ya existen; debe reflejar el alcance real antes de sumar más.
- **Datos faltantes a curar:** tablas de reactancia de cable, reactancias subtransitorias de motores y catálogo de curvas de protección — son el insumo común de P0–P1.

### Resumen de prioridad inmediata
> **Para "completar" el motor en pro del análisis eléctrico, lo inmediato es P0** (reactancia de cable + aporte de motores + rango de validez): pequeño esfuerzo, gran ganancia de exactitud y defendibilidad sobre lo ya construido. **Arc Flash (P1)** es el siguiente mejor retorno por reutilizar datos existentes. El **flujo nodal (P2)** es el salto estratégico, pero exige refactor y debe ir después de saldar los habilitadores transversales.

---

> Reporte generado en solo lectura. No se ejecutó ni modificó ETAP ni sus archivos. La identificación de módulos se basa en nombres de binarios/DLL, librerías (`Tables/`, `Lib/`) y ejemplos presentes en `C:\ETAP Demo`; no se descompiló ningún binario.
