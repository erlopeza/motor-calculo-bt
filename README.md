\# Motor de Cálculo BT

Herramienta para verificación y cálculo de circuitos eléctricos

en baja tensión. Lee datos desde Excel y genera reporte automático

con verificación normativa.



\*\*Versión:\*\* 1.0

\*\*Normativa:\*\* SEC RIC N°10 / NEC / IEC 60364

\*\*Sistemas:\*\* Monofásico (1F) / Bifásico (2F) / Trifásico (3F)



\---



\## ¿Qué calcula?



\- Caída de tensión por circuito (V y %)

\- Potencia activa (W)

\- Capacidad del conductor con corrección por temperatura

\- Verificación normativa automática

\- Sugerencia de conductor mínimo cuando hay falla



\---



\## Requisitos



\### Opción A — Ejecutable (usuarios sin Python)

\- Windows 10 o superior

\- No requiere instalación adicional



\### Opción B — Script Python (usuarios técnicos)

\- Python 3.10 o superior

\- Librería openpyxl:

&#x20; pip install openpyxl



\---



\## Instalación



\### Opción A — Ejecutable

1\. Copiar `calculo\_bt.exe` a cualquier carpeta

2\. Copiar `circuitos.xlsx` a la misma carpeta

3\. Listo — no requiere instalación



\### Opción B — Script Python

1\. Copiar los archivos del proyecto a una carpeta:

&#x20;  - conductores.py

&#x20;  - calculos.py

&#x20;  - excel.py

&#x20;  - main.py

&#x20;  - circuitos.xlsx

2\. Instalar dependencias:

&#x20;  pip install openpyxl

3\. Ejecutar:

&#x20;  python main.py



\---



\## Uso



\### Paso 1 — Preparar la planilla Excel

Abrir `circuitos.xlsx` y completar una fila por circuito:



| Columna | Campo | Valores válidos | Ejemplo |

|---|---|---|---|

| A | nombre | texto libre | CRAC Unit 1-A |

| B | sistema | `3F` `1F` `2F` | 3F |

| C | conductor | ver tabla de conductores | 6AWG |

| D | paralelos | entero ≥ 1 | 1 |

| E | I\_diseno | Amperios | 63 |

| F | cos\_phi | 0.0 a 1.0 | 0.85 |

| G | L\_m | metros | 10 |

| H | temp\_amb | 25/30/35/40/45/50 °C | 30 |



\### Paso 2 — Ejecutar la herramienta

\*\*Con ejecutable:\*\* doble click en `calculo\_bt.exe`

\*\*Con Python:\*\* python main.py



\### Paso 3 — Ingresar datos

```

Nombre del proyecto : NOMBRE-PROYECTO

Archivo Excel       : circuitos

```



\### Paso 4 — Revisar resultados

La herramienta genera dos archivos automáticamente:

```

REPORTE\_NOMBRE-PROYECTO\_FECHA.txt    ← resumen en texto

REPORTE\_NOMBRE-PROYECTO\_FECHA.xlsx   ← reporte con colores

```



\---



\## Tabla de conductores disponibles



| Conductor | Sección (mm²) | Capacidad (A) |

|---|---|---|

| 14AWG | 2.08 | 20 |

| 12AWG | 3.31 | 25 |

| 10AWG | 5.26 | 35 |

| 8AWG | 8.37 | 50 |

| 6AWG | 13.3 | 65 |

| 4AWG | 21.1 | 85 |

| 2AWG | 33.6 | 115 |

| 1/0AWG | 53.5 | 150 |

| 2/0AWG | 67.4 | 175 |

| 4/0AWG | 107.0 | 230 |

| 350MCM | 177.0 | 310 |

| 400MCM | 203.0 | 335 |

| 500MCM | 253.0 | 380 |



Capacidades a 30°C — conductor XLPE/PVC 90°C en conduit.

Fuente: NEC Table 310.15



\---



\## Interpretación de resultados



| Estado | Rango ΔV | Color Excel | Acción |

|---|---|---|---|

| ÓPTIMO | ≤ 1.5% | Verde | Sin acción |

| ACEPTABLE | ≤ 3.0% | Amarillo | Sin acción |

| PRECAUCIÓN | ≤ 5.0% | Naranja | Evaluar redimensionar |

| FALLA | > 5.0% | Rojo | Redimensionar — ver sugerencia |



Cuando hay FALLA la herramienta indica automáticamente

el conductor mínimo que resuelve el problema.



\---



\## Corrección por temperatura



La capacidad del conductor se reduce con la temperatura ambiente.

Factores aplicados (NEC Table 310.15(B)(1) — XLPE 90°C):



| Temp °C | Factor |

|---|---|

| 25 | 1.04 |

| 30 | 1.00 |

| 35 | 0.96 |

| 40 | 0.91 |

| 45 | 0.87 |

| 50 | 0.82 |



\---



\## Estructura del proyecto

```

motor-calculo-bt/

&#x20;   ├── conductores.py   → tabla AWG/MCM y factores de temperatura

&#x20;   ├── calculos.py      → fórmulas de caída, potencia, clasificación

&#x20;   ├── excel.py         → lectura Excel y exportación de reportes

&#x20;   ├── main.py          → programa principal

&#x20;   ├── circuitos.xlsx   → plantilla de entrada

&#x20;   └── README.md        → este archivo

```



\---



\## Limitaciones actuales



\- Solo conductores de cobre (RHO = 0.0175 Ω·mm²/m)

\- No incluye reactancia inductiva (válido para cables < 200m en BT)

\- No calcula corriente de cortocircuito

\- No verifica coordinación de protecciones



\---



\## Desarrollado con



\- Python 3.13

\- openpyxl 3.1.5

\- PyInstaller 6.19.0



\---



\## Historial de versiones



| Versión | Fecha | Cambios |

|---|---|---|

| 1.0 | 2026-03-21 | Versión inicial — 1F/2F/3F, paralelos, temperatura |

