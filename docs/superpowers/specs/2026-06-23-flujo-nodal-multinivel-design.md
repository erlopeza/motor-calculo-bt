# Diseño — Flujo de carga nodal multinivel desde la cadena

**Fecha:** 2026-06-23 · **Rama:** `feat/flujo-nodal-integracion` · **Estado:** aprobado para implementación
**Origen:** integrar el motor `flujo_nodal.py` (F3-P2.1, hoy aislado) a la memoria SEC, estructurado por la topología real del proyecto (hoja `cadena`).

---

## 1. Problema y objetivo

`flujo_nodal.py` (Bus/Rama/Red + Newton-Raphson) existe y está testeado, pero no lo consume nadie: el ingeniero no ve un perfil nodal. Este trabajo construye el grafo `Red` **desde la hoja `cadena`** del proyecto, corre el flujo de carga y vuelca un perfil nodal (tensiones, caídas, pérdidas) a la memoria SEC.

**Restricción rectora:** código genérico y multi-proyecto, sin UI nueva. La cadena es el dato; el código no conoce ningún proyecto concreto.

## 2. Alcance

**Entra:**
- Módulo nuevo `red_desde_cadena.py`: `construir_red(cadena, trafo_z_ohm, circuitos, *, xr=0.1) -> Red`.
- Sección "Flujo de Carga Nodal" en la memoria DOCX (tabla por barra + pérdidas + convergencia).
- Bloque `flujo_nodal` opcional en `exportar_json_epc`.
- Enhebrado mínimo en `gui.py` (pasar cadena + Z trafo a `datos_run`).

**No entra (YAGNI):**
- UI de captura de topología.
- Cargas por circuito con join exacto `circuito_ref`↔`circuitos.Nombre` (es la alternativa descartada en brainstorming).
- Mallas/anillos (la cadena es radial).
- Multi-fuente simultánea (trafo + generador a la vez): cada corrida toma una sola fuente slack.
- Fallback radial-auto cuando no hay cadena: si no hay hoja `cadena`, la sección se omite con nota (robustez, sin inventar topología).

## 3. Mapeo cadena → Red (núcleo)

Módulo `red_desde_cadena.py`, función `construir_red(cadena, trafo_z_ohm, circuitos, *, xr=0.1) -> Red`.

`cadena` es la lista de dispositivos de `leer_cadena_excel`: cada uno tiene `nombre`, `upstream` (nombre del padre, vacío en nivel 0), `nivel` (0 = cabecera), `In_A`, `curva`, `Icc_kA`, `circuito_ref`.

### 3.1 Topología
- Un **bus por dispositivo** (id = `nombre`).
- Una **rama** de la barra del `upstream` a la barra del dispositivo.
- Los dispositivos de `nivel 0` (upstream vacío) cuelgan del **slack = transformador** (bus `"TRAFO"`).
- Slack: `Bus(id="TRAFO", tipo="slack")`. Resto: `tipo="PQ"`.

### 3.2 Impedancia de rama (desde la escalera de Icc)
La impedancia acumulada hasta un nodo se deriva de su Icc:
```
Z_acum(nodo) = c_max · Vn / (√3 · Icc_nodo_A)     [Ω, magnitud]
```
con `c_max = 1.05` (IEC 60909) y `Vn` la tensión del sistema (V). La impedancia de la rama:
```
Z_rama(nodo) = Z_acum(nodo) − Z_acum(padre)        (padre = upstream)
Z_rama(nivel 0) = Z_acum(nodo) − Z_trafo            (Z_trafo = trafo_z_ohm, magnitud)
```
Como la escalera da **magnitud**, se reparte en R+jX con una relación X/R típica BT parametrizable (`xr`, default 0.1):
```
R = |Z_rama| / √(1 + xr²)     ;     X = R · xr
```
`Rama(from_bus, to_bus, R_ohm=R, X_ohm=X)`.

**Casos límite:**
- `Icc_nodo` ausente o ≤ 0 → no se puede derivar Z; **el nodo se excluye** con bandera (`red.nodos_excluidos`). Sus **hijos con Icc válida sobreviven re-enraizados al TRAFO**: `Z_acum(hijo)` es la impedancia total real desde la fuente (independiente de la topología intermedia), así que el hijo conserva su impedancia correcta y no se pierde su carga. Solo se pierde el bus intermedio sin dato.
- `Z_rama ≤ 0` (Icc del hijo ≥ del padre, físicamente inconsistente) → se fija a un mínimo positivo (1e-6 Ω) y se marca como dato sospechoso.

### 3.3 Cargas (agregadas en hojas)
- **Nodos hoja** = dispositivos sin hijos en el árbol.
- Carga total del sistema = `Σ P` de `circuitos` (solo el total, sin join por nombre). `P_circuito = √3 · V · I_diseno · cos_phi` (3F) o `V · I_diseno · cos_phi` (1F); si el circuito trae `p_kw`, se usa ese.
- Reparto a hojas proporcional a `In_A` (peso por capacidad):
```
P_hoja = P_total · In_hoja / Σ In_hojas
```
- Nodos intermedios: sin carga local (solo transmiten).
- Q por hoja: `Q_hoja = P_hoja · tan(acos(cos_phi_default))`, `cos_phi_default = 0.9`.
- Inyección PQ: `P_kW = −P_hoja`, `Q_kVAR = −Q_hoja` (convención de carga de `flujo_nodal`).

## 4. Integración en la memoria

`reporteria_sec._agregar_seccion_flujo_nodal(doc, datos_run, circuitos)`, llamada en `generar_memoria_docx` tras la sección de Arc Flash, envuelta en try/except (nunca rompe la memoria; loguea a stdout + párrafo de omisión).

Lee de `datos_run`: `cadena` (lista), `trafo_z_ohm` (float), `tension_sistema_v` (default 380). Si falta `cadena` o está vacía → párrafo "Flujo nodal: sin cadena de coordinación cargada; se omite."

Contenido cuando hay datos:
- Tabla por barra: `Bus | V (pu) | V (kV) | Caída % | P (kW)` (caída% = (1 − V_pu)·100).
- Línea resumen: pérdidas totales (kW), iteraciones, estado de convergencia.
- Bandera de nodos excluidos por Icc faltante/inconsistente.

## 5. exportar_json_epc

Reusar el parámetro `circuitos` ya existente; añadir, cuando `datos_run` traiga `cadena`, un bloque:
```
payload["flujo_nodal"] = {
    "convergido": bool, "iteraciones": int, "perdidas_totales_kW": float,
    "buses": [{"id":.., "V_pu":.., "V_kV":.., "P_kW":..}, ...],
}
```

## 6. Datos desde la GUI

`gui.py` ya tiene `self.cadena_datos`, `self.datos_trafo`, `self.circuitos`. En el bloque que arma `datos_run` (mismo lugar donde se enhebró Arc Flash), añadir:
- `"cadena": self.cadena_datos or []`
- `"trafo_z_ohm": float(Zt)` — la impedancia del trafo ya calculada (`calcular_icc_transformador` retorna `(Icc, Zt_ohm, datos)`); usar ese `Zt_ohm`.
- `"tension_sistema_v"`: la tensión del sistema en uso.

## 7. Estrategia de pruebas (TDD)

| Archivo | Cubre |
|---|---|
| `tests/test_red_desde_cadena.py` | árbol correcto (upstream→ramas), slack=TRAFO, Z_rama>0 y Z_acum creciente con profundidad, reparto de carga conserva el total, nodo sin Icc se excluye con bandera |
| `tests/test_reporteria_flujo_nodal.py` | sección presente, tabla por barra, omisión sin cadena, no rompe la memoria |
| `tests/test_integracion_flujo_nodal_real.py` | cadena real de `circuitos.xlsx` (G0A→G1A→C1A→C2A): converge, tensiones decrecientes en cascada |

Criterio global: la suite completa sigue verde.

## 8. Decisiones registradas

1. Topología desde hoja `cadena` (multinivel), no radial-auto.
2. Impedancia de rama derivada de la escalera de Icc (`Z_acum` por nodo), repartida R/X con X/R típico parametrizable (default 0.1).
3. Cargas agregadas en nodos hoja, repartidas por peso de `In_A`; carga total = Σ P de circuitos.
4. Sin cadena → sección omitida con nota (no fallback radial).
5. Una sola fuente slack por corrida (trafo); generador como corrida alternativa futura.
6. cos φ por defecto 0.9 para Q; `c_max` = 1.05.
7. Integración paralela al patrón Arc Flash (sección memoria + JSON EPC + enhebrado GUI), reusa `flujo_nodal.py` sin modificarlo.
