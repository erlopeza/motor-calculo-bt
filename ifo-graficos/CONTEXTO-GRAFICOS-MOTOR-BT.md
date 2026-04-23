---
tipo: contexto-modulo
area: python
modulo: graficos.py
tags: [motor-calculo-bt, graficos, matplotlib, visualizacion, contexto-chat]
fecha: 2026-04-22
estado: activo
proyecto: motor-calculo-bt
commit_base: 6eac0b3
tests_base: 283 passed / 0 failed
---

# Contexto — Módulo `graficos.py` Motor BT

## Estado del sistema al iniciar este módulo

```
Repositorio : github.com/erlopeza/motor-calculo-bt
Commit base : 6eac0b3
Tests       : 283 passed / 0 failed
Rama        : main
```

---

## Principio rector

`graficos.py` transforma números de cálculo en visualizaciones técnicas
normadas. No reemplaza criterio de ingeniero — lo apoya visualmente.

Las imágenes van a:
```
07_CONTROL/curvas/{proyecto}/   → del proyecto activo
```
Y se embeben automáticamente en la Memoria Explicativa SEC
generada por `reporteria_sec.py`.

---

## Fuentes de datos disponibles — por módulo

### 1. `calculos.py` → G1: Perfil ΔV por circuito

Datos disponibles:
```python
# Por cada circuito calculado:
{
    "id": str,
    "nombre": str,
    "dv_pct": float,        # caída de tensión del tramo
    "sum_dv_pct": float,    # caída acumulada desde secundario trafo
    "estado": str,          # "OPTIMO" | "ACEPTABLE" | "PRECAUCION" | "FALLA"
    "longitud_m": float,
    "seccion_mm2": float,
    "Ib_A": float,
    "tablero": str
}
```

Criterios de color (RIC N°10):
```
≤ 1.5%  → verde     ÓPTIMO
≤ 3.0%  → amarillo  ACEPTABLE
≤ 5.0%  → naranja   PRECAUCIÓN
> 5.0%  → rojo      FALLA
```

Tipo de gráfico: barras horizontales con líneas de referencia.

---

### 2. `generador.py` → G2: Curva de decremento Icc GE

Datos disponibles:
```python
{
    "Ik3_pp_kA": float,   # Ik'' subtransitorio  t=0
    "Ik3_p_kA": float,    # Ik'  transitorio
    "Ik3_kA": float,      # Ik   permanente
    "T_pp_s": 0.012,      # T''d constante subtransitoria (Stamford)
    "T_p_s": 0.08,        # T'd  constante transitoria
    "Ta_s": 0.018,        # Ta   constante armadura
    "Sn_kVA": float,
    "Vn_V": float,
    "modelo": str         # "HCI544D_W14" u otro
}
```

Fórmula curva de decremento IEC:
```
Ik(t) = (Ik'' - Ik') × e^(-t/T''d)
      + (Ik' - Ik)  × e^(-t/T'd)
      + Ik

Componente DC (asimétrica):
Ik_dc(t) = √2 × Ik'' × e^(-t/Ta)
```

Referencia visual: curva de decremento Stamford HCI534D página 6
(misma forma — SIMÉTRICA y ASIMÉTRICA, escala log en ambos ejes)

Tipo de gráfico: log-log, dos curvas (simétrica + asimétrica),
líneas horizontales para Ik'' / Ik' / Ik_perm.

---

### 3. `coordinacion.py` + `protecciones.py` → G3: Curvas TCC

Datos disponibles:
```python
# Por cada protección:
{
    "nombre": str,
    "tipo": str,           # "ETU600" | "ETU320" | "TM240" | "C" | "D" | "B"
    "In_A": float,
    "Im_A": float,         # corriente magnética
    "Ir_A": float,         # corriente de regulación sobrecarga
    "Icc_punto_kA": float, # Icc en el punto
    "nivel": int           # 1=aguas_arriba, 2=aguas_abajo
}
```

Curvas TCC estándar IEC:
```
Curva C: t = k / (I/In - 1)^α  (IEC 60898-1)
Curva D: Im = 10-20 × In
Curva B: Im = 3-5 × In
ETU300/600: ajuste por banda lr/tr/Im/ti configurable
```

Tipo de gráfico: log-log, múltiples curvas por nivel,
zona de selectividad sombreada, línea vertical Icc_punto.

---

### 4. `balance.py` → G4: Balance de carga por fase

Datos disponibles:
```python
{
    "tablero": str,
    "L1_kW": float,
    "L2_kW": float,
    "L3_kW": float,
    "L1_A": float,
    "L2_A": float,
    "L3_A": float,
    "desequilibrio_pct": float,  # (Imax-Imin)/Imin × 100
    "limite_deseq_pct": 25.0     # NCh 4-2003 máx 25% entre fases
}
```

Tipo de gráfico: barras agrupadas L1/L2/L3 con línea de capacidad
del tablero y línea de alerta desequilibrio.

---

### 5. `ups.py` → G5: Curva de autonomía UPS

Datos disponibles:
```python
{
    "E_bat_kWh": float,
    "P_bat_kW": float,       # potencia en baterías = P_carga/η_ups
    "t_autonomia_min": float,
    "t_minimo_normado_min": float,  # 15 min TIA-942 Tier III
    "η_ups": float,
    "V_string_V": float,
    "Ah_efectivo_Ah": float,
    "nivel_infraestructura": str
}
```

Curva de descarga:
```
SOC(t) = 100 - (P_bat × t) / E_bat × 100  [%]
t va de 0 hasta t_autonomia
Línea de alerta: t_minimo_normado
Línea de corte: SOC = 20% (profundidad máxima descarga)
```

Tipo de gráfico: línea SOC% vs tiempo [min], zonas coloreadas
(verde / amarillo / rojo por nivel de carga).

---

### 6. `ats.py` + `generador.py` → G6: Secuencia de transferencia ATS

Datos disponibles:
```python
{
    "modo": str,          # "open" | "closed" | "sts"
    "t_deteccion_ms": float,
    "t_arranque_ge_ms": float,
    "t_estabilizacion_ms": float,
    "t_paralelo_ms": float,      # solo closed
    "t_total_ms": float,
    "t_interrupcion_ms": float,
    "V_red_V": float,
    "V_ge_V": float,
    "f_red_Hz": float,
    "f_ge_Hz": float
}
```

Tipo de gráfico: diagrama de barras apiladas horizontales
(timeline de eventos) + gráfico de tensión en el tiempo
(caída y recuperación durante transferencia).

---

### 7. `simulaciones/` → G7: Gráfico de divergencias SIMARIS

Datos disponibles:
```python
# Por cada escenario analizado:
{
    "id": str,
    "descripcion": str,
    "resultado_motor": float,
    "resultado_simaris": float,
    "divergencia_pct": float,
    "categoria": str    # "SUPUESTO_CONSERVADOR" | "EQUIPO_DISTINTO" |
                        # "VARIABLE_IGNORADA" | "ERROR_MOTOR"
}
```

Tipo de gráfico: barras horizontales de divergencia %
coloreadas por categoría, línea de referencia 0%,
línea de tolerancia ±5%.

---

### 8. `commissioning/` → G8: Estado de commissioning

Datos disponibles desde protocolos P1-P4:
```python
# Después de llenado en campo:
{
    "prueba": str,         # "P1" | "P2" | "P3" | "P4"
    "circuito": str,
    "valor_esperado": float,
    "valor_medido": float,
    "estado": str          # "APROBADO" | "PENDIENTE" | "FALLA"
}
```

Tipo de gráfico: tabla visual con semáforo por prueba/circuito.
(Solo cuando hay datos medidos — no genera gráfico vacío)

---

## Firma del módulo `graficos.py`

```python
def grafico_dv_circuitos(
    circuitos: list,
    titulo: str = "Perfil ΔV por circuito",
    ruta_salida: str = None
) -> str:
    # retorna ruta del archivo .png generado

def grafico_decremento_ge(
    resultado_ge: dict,
    titulo: str = "Curva de decremento Icc GE",
    ruta_salida: str = None
) -> str:

def grafico_tcc(
    protecciones: list,
    Icc_punto_kA: float,
    titulo: str = "Curvas TCC",
    ruta_salida: str = None
) -> str:

def grafico_balance_fases(
    resultado_balance: dict,
    titulo: str = "Balance de carga por fase",
    ruta_salida: str = None
) -> str:

def grafico_autonomia_ups(
    resultado_ups: dict,
    titulo: str = "Curva de autonomía UPS",
    ruta_salida: str = None
) -> str:

def grafico_transferencia_ats(
    resultado_ats: dict,
    titulo: str = "Secuencia de transferencia ATS",
    ruta_salida: str = None
) -> str:

def grafico_divergencias_simaris(
    resultados_simulaciones: list,
    titulo: str = "Divergencias Motor BT vs SIMARIS",
    ruta_salida: str = None
) -> str:

def generar_todos(
    resultados: dict,
    ruta_salida: str,
    prefijo: str = ""
) -> dict:
    # genera todos los gráficos disponibles según los datos presentes
    # retorna dict {nombre_grafico: ruta_archivo}
```

---

## Estilo visual

Estilo técnico-industrial. Fondo oscuro con texto claro.
Paleta base:

```python
STYLE = {
    "bg":       "#1a1a2e",   # fondo principal
    "surface":  "#16213e",   # superficie de gráfico
    "grid":     "#2a2a4a",   # grilla
    "text":     "#e0e0e0",   # texto principal
    "accent":   "#00ff88",   # verde fosforescente — valores OK
    "warning":  "#ffaa00",   # amarillo — advertencia
    "danger":   "#ff4444",   # rojo — falla
    "info":     "#4488ff",   # azul — referencia/normativa
    "neutral":  "#888888",   # gris — secundario
}
```

Fuentes: monospace para valores numéricos, sans-serif para etiquetas.
DPI: 150 para reportes, 96 para pantalla.
Formato de salida: PNG (embebible en DOCX/PDF).

---

## Integración con `reporteria_sec.py`

Al generar la Memoria SEC, el módulo llama:

```python
from graficos import generar_todos

graficos = generar_todos(resultados, ruta_outputs)
# → {"dv_circuitos": "path/dv.png", "decremento_ge": "path/ge.png", ...}

# Los gráficos disponibles se insertan en las secciones correspondientes
# de la Memoria SEC (DOCX + PDF)
```

---

## Integración con `main.py`

```python
# Al ejecutar el motor desde CLI:
python main.py --proyecto LEO-ARICA --graficos

# Genera todos los gráficos en:
# {MOTOR_BT_OUTPUTS}/07_CONTROL/curvas/{proyecto}/
```

---

## Reglas del módulo

1. Si no hay datos para un gráfico → no genera archivo, no falla
2. Ruta de salida desde `MOTOR_BT_OUTPUTS` o parámetro explícito
3. Nombre de archivo incluye proyecto y timestamp
4. Formato: `{tipo_grafico}_{proyecto}_{YYYYMMDD_HHMM}.png`
5. No hardcodear rutas absolutas
6. Cada función es independiente — puede llamarse sola

---

## Tests requeridos

```python
test_grafico_dv_genera_archivo_png
test_grafico_dv_colores_por_zona_normativa
test_grafico_ge_genera_curva_decremento
test_grafico_ge_3_niveles_icc
test_grafico_tcc_escala_log_log
test_grafico_balance_3_fases
test_grafico_autonomia_linea_normada
test_grafico_ats_timeline
test_grafico_divergencias_colores_categoria
test_generar_todos_retorna_dict
test_grafico_no_falla_si_datos_vacios
```

---

## Archivos a crear

```
graficos.py              ← módulo principal
tests/test_graficos.py   ← tests
```

## Archivos a modificar

```
reporteria_sec.py        ← hook para embeber gráficos
main.py                  ← flag --graficos en CLI
requirements.txt         ← agregar matplotlib
```

## Archivos prohibidos

Todos los módulos de cálculo existentes.

---

## Validación

```
python -m pytest tests/test_graficos.py -q
python -m pytest -q   ← suite completa
```

Resultado esperado: **295+ passed / 0 failed**

---

## Conexiones

- [[NOTA-CIERRE-MOTOR-BT-2026-04-22]]
- [[NOTA-ESTADO-MOTOR-BT-2026-04-19]]
- [[NOTA-M9-GENERADOR-BT]]
- [[NOTA-M12-TRAFO-ISO-UPS]]
- [[Electrical BT Chile — Core Técnico]]
