# Diseño — Arc Flash + TCC en memoria SEC (genérico, validado en LEO-ARICA)

**Fecha:** 2026-06-22 · **Rama:** `main` · **Estado:** aprobado para implementación
**Origen:** roadmap consolidado F2 (P1.1/P1.2/P1.3 ya implementados como motores aislados) → integración a la salida del ingeniero (memoria SEC).

---

## 1. Problema y objetivo

Los módulos `arc_flash.py`, `tcc_curvas.py` y `coordinacion.py` existen y están testeados, pero **no los consume la memoria SEC**: su valor técnico está "en el estante". Este trabajo los conecta a la memoria DOCX/PDF que usa el ingeniero, produciendo análisis de arco eléctrico y coordinación con curvas reales.

**Restricción rectora (decisión del usuario):** el código debe ser **genérico y aplicable a múltiples proyectos**. Ningún valor de un proyecto concreto se hardcodea. El proyecto real **LEO-ARICA** se usa solo como **caso de validación**, entrando como *dato* (un libro Excel que conforma el formato canónico de la herramienta), nunca como lógica.

## 2. Alcance

**Entra:**
- Sección nueva "Análisis de Arco Eléctrico (IEEE 1584)" en la memoria DOCX y PDF.
- Arc Flash en **barra principal** (Icc de bornes del transformador) + **tabla por circuito**.
- Unificación de la región tiempo-corriente: `coordinacion.py` delega su región térmica IEC 60898 en `tcc_curvas.py` (fuente única).
- Resultados de arco incluidos en `exportar_json_epc` (trazabilidad EPC).
- Validación end-to-end sobre datos reales LEO-ARICA conformados al formato canónico.

**No entra (YAGNI):**
- Importador DWG/DXF/OLE (descartado por spike de factibilidad — ver §7).
- Modelo de barras/topología completo (se cubre barra principal + circuitos sin inventar grafo).
- UI nueva para parámetros de arco (defaults normativos parametrizables).
- IEEE 1584-2018 (se mantiene el modelo 2002 ya implementado).
- Mapeo automático de Excels arbitrarios: cada proyecto conforma el formato canónico de la herramienta.
- Cadena de respaldo (back-up) aguas arriba en el cálculo de t de despeje: diferido.

## 3. Arquitectura y fronteras de módulo

```
arc_flash.py            motor IEEE 1584-2002 (existe, endurecido)
   + arc_flash_desde_proteccion()   NUEVO: puente Ia -> t_despeje -> energía
coordinacion.py         delega región térmica IEC 60898 en tcc_curvas (fuente única)
tcc_curvas.py           catálogo DATA-3 (sin cambios)
reporteria_sec.py       + _agregar_seccion_arc_flash()  (solo renderiza)
excel.py                formato canónico de entrada (sin cambios; se reutiliza)
gui.py                  enhebra In_A/curva en circuitos_persistencia + icc_barra
```

**Regla de separación:** el **cálculo** vive en `arc_flash.py` (incluido el puente que evalúa el despeje en Ia vía `coordinacion`). `reporteria_sec.py` solo **arma la tabla y la escribe** — la sección de memoria se testea sin generar DOCX, pasando estructuras ya calculadas.

## 4. Diseño detallado

### 4.1 Puente Arc-Flash ↔ protección (el corazón)

Función nueva en `arc_flash.py`:

```
arc_flash_desde_proteccion(
    Ibf_kA, V_kV, In_A, curva,
    *, G_mm=32.0, D_mm=455.0, config="box", t_techo_s=2.0
) -> dict
```

Pasos:
1. `Ia = calcular_corriente_arco(Ibf_kA, V_kV, G_mm)` → corriente de arco.
2. `disp = coordinacion.calcular_tiempo_disparo(Ia*1000, In_A, curva)` — **evaluado en Ia**, no en Icc (corriente de arco menor → la protección puede tardar más; es el peor caso real que exige IEEE 1584).
3. Resolución del tiempo de despeje:
   - `region == "instantaneo"` → `t = 0.02 s`.
   - `region in ("termico","idmt")` → `t = disp.t_s` (puede ser grande — la trampa que se busca exponer).
   - `region == "no_dispara"` → `t = t_techo_s` (2 s, máximo práctico IEEE 1584) **+ `despeje_incierto=True`**.
   - `region == "verificar_simaris"` (ETU propietaria) → `t = t_techo_s` + `verificar_simaris=True`.
4. `calcular_arc_flash_completo(Ibf_kA, V_kV, G_mm, t_s=t, D_mm=D_mm, config=config)` → energía, frontera, categoría EPP.
5. Retorna dict con: `Ia_kA, t_despeje_s, region_despeje, E_cal_cm2, D_afb_mm, categoria_ppe, despeje_incierto, verificar_simaris`.

Defaults `G_mm=32`, `D_mm=455`, `config="box"`: valores típicos IEEE 1584-2002 Tabla para tablero BT cerrado; parametrizables, no hardcode de proyecto.

### 4.2 Unificación tcc ↔ M7 (coordinacion.py)

Validado con datos: en la región térmica B/C/D, `K_CURVA` (M7) y `tcc_curvas` dan **0.00 % de diferencia** (mismos `k`, misma fórmula `t = k/(I/In)²`).

- `coordinacion.py` introduce un helper interno `_tiempo_termico_iec60898(I, In, curva)` que delega en `tcc_curvas.calcular_tiempo_tcc(..., tipo="IEC60898", modelo=curva)`.
- Se elimina el dict `K_CURVA` duplicado para B/C/D.
- M7 conserva su lógica de región **instantánea** (umbral magnético), **ETU** (Isd/tsd) y **TM**.
- Criterio de hecho: los tests M7 existentes siguen verdes **sin modificarlos** (números idénticos).

### 4.3 Integración en la memoria (reporteria_sec.py)

Nueva función `_agregar_seccion_arc_flash(doc, datos_run, circuitos)`, llamada en `generar_memoria_docx` tras la sección de coordinación. Dos bloques:

**Barra principal:**
- `Ibf` = `datos_run["icc_barra_ka"]` (Icc bornes del transformador).
- Dispositivo de despeje = interruptor cabecera (`nivel == 0` en la cadena de protecciones) si está disponible; si no, se calcula igual con bandera "sin protección de cabecera definida".

**Tabla por circuito** — columnas:

| Circuito | Icc (kA) | Ia (kA) | t_desp (s) | E (cal/cm²) | Frontera (mm) | Cat EPP |

- Fila marcada (rojo) si `despeje_incierto` o `verificar_simaris`.
- Circuitos sin `In_A`/`curva` → no entran a la tabla; se listan aparte en "Circuitos sin datos de protección".

**Robustez:** si `Ibf <= 0` o faltan datos, la sección se omite con nota; **nunca** rompe la generación de la memoria (mismo patrón try/except que la reportería actual).

### 4.4 Enhebrado de datos (gui.py)

Cambios mínimos y localizados (~10 líneas) donde se arma `circuitos_persistencia` (gui.py ≈ líneas 927-945):
- Agregar `In_A`, `curva` a cada dict desde `self.protecciones[nombre]` (cuando exista).
- Agregar a `datos_run`: `icc_barra_ka` (de `icc_desde_tabla(kVA)`) y el dispositivo cabecera (`nivel == 0`).

### 4.5 Entrada de datos genérica

No se construye intake nuevo. Se reutiliza el formato Excel canónico de `excel.py` (dirigido por encabezados: `nombre, sistema, conductor, paralelos, i_diseno, cos_phi, l_m, temp_amb, …` + protecciones `In_A, curva, poder_corte_kA, nivel, upstream`). Cualquier proyecto que conforme ese formato calcula.

## 5. Validación LEO-ARICA (dato, no código)

- Se prepara un libro `tests/fixtures/leo_arica.xlsx` **conforme al formato canónico**, transcribiendo (data-prep manual) las hojas `01_FUENTES`, `03_TABLEROS_PANELES` y `04_CARGAS_CIRCUITOS` de `LEO_ARICA_BASE_TECNICA_v5.xlsx`.
- El mapeo proyecto→canónico vive en el **archivo de datos**, no en el código. El código permanece genérico.
- Un test de integración `test_integracion_leo_arica.py` corre el pipeline completo (lectura → cálculos → memoria de arco) y verifica que la memoria se genera con valores coherentes (rangos físicos, no números mágicos exactos).

## 6. Estrategia de pruebas (TDD)

| Archivo | Cubre |
|---|---|
| `test_arc_flash_proteccion.py` | puente: despeje en Ia, caso no_dispara→techo+bandera, verificar_simaris, monotonía |
| `test_coordinacion_unificada.py` | regresión: M7 idéntico tras delegar región térmica en tcc |
| `test_reporteria_arc_flash.py` | la memoria incluye sección, tabla, marca de despeje incierto, omisión robusta |
| `test_integracion_leo_arica.py` | end-to-end sobre datos reales conformados |

Criterio global: la suite completa (actual 645) sigue verde.

## 7. Apéndice — Resultado del spike de factibilidad DWG (2026-06-22)

Se evaluó extraer datos de protección directamente de los DWG/PDF del estudio LEO-ARICA (SIMARIS/ETAP).

- **Conversión DWG→DXF:** viable y automatizable con `accoreconsole.exe` (AutoCAD 2026) invocado **desde PowerShell**. (Desde Git Bash, MSYS mangla los flags `/i /s` → falla silenciosa.)
- **Extracción del schedule:** **no viable**. El schedule (In/curva/Icc) está embebido como **objetos OLE AutoCAD-wrapped** (1.5–1.8 MB, renders), no como entidades TEXT/MTEXT/TABLE. `ezdxf` solo recupera rótulo, mapa de ubicación y fragmentos sueltos.
- **Conclusión:** el importador DWG es un callejón sin salida. Los **datos fuente existen en Excel estructurado** (`LEO_ARICA_BASE_TECNICA_v5.xlsx`), que es justo lo que la herramienta ya consume. Camino correcto: Excel → herramienta.

## 8. Decisiones registradas

1. Alcance = Arc Flash + TCC en memoria (no flujo nodal en GUI, no F4).
2. tcc ↔ M7 → unificar (fuente única tcc en región térmica; 0% diff verificado).
3. Granularidad = barra principal + tabla por circuito.
4. t de despeje = evaluado en Ia (correcto/conservador); techo 2 s + bandera si no despeja.
5. Defaults arco: G=32 mm, D=455 mm, config="box" (parametrizables).
6. Back-up aguas arriba: diferido.
7. Entrada genérica vía formato Excel canónico; LEO-ARICA como dato de validación.
8. Importador DWG: descartado (spike).
