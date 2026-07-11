# Motor de Cálculo BT

Herramienta de cálculo eléctrico para instalaciones de baja tensión (BT) según normativa chilena (SEC/NCh) e internacional (IEC/NEC). Lee datos desde Excel, calcula y verifica toda la instalación, y genera la memoria técnica SEC en DOCX/PDF.

**Versión:** 2.1  
**Python:** ≥ 3.12  
**Tests:** 766 (758 passed + 8 skipped: RAG opcional + GUI Tk sin display) — `pytest` verde en cada commit

---

## Qué calcula

| Módulo | Capacidad | Norma |
|---|---|---|
| Caída de tensión | ΔV por circuito y acumulada, corrección por temperatura y paralelos | NEC 310.15 / IEC 60228 |
| Cortocircuito | Icc trifásica y fase-neutro aguas abajo, reducción por cable | IEC 60909 / IEC 60364-4-41 |
| Protecciones | Disparo magnético (B/C/D/K/MA), poder de corte, tiempo de desconexión | IEC 60898 / 60947-2 |
| Coordinación | Selectividad en cadena, verificación IEC 60364 | IEC 60364 |
| Demanda y balance | FD por tipo de carga, balance de fases, selección de transformador | RIC N°10 |
| Aporte de motores al Icc | Contribución subtransitoria de motores al cortocircuito | IEC 60909-4:2021 |
| Arc Flash | Energía incidente, frontera de arco, categoría EPP (evaluado en Ia, no solo Ibf) | IEEE 1584-2002 / NFPA 70E |
| Curvas TCC | Catálogo tiempo-corriente por curva (B/C/D/K/MA), fuente única de `k` térmico | IEC 60898-1 / IEC 60255-151 |
| Coordinación | Selectividad en cadena, márgenes, verificación de respaldo (back-up) | IEC 60364 / IEC 60947-2 |
| Flujo de carga nodal | Newton-Raphson multinivel desde la cadena de protecciones: tensión por barra, pérdidas | IEEE 399 / IEC 60909 |
| Motores (M8) | Corriente nominal y arranque, ΔV arranque, conductor, guardamotor | NCh 4-2003 §12.28 |
| Generador (M9) | Potencia mínima, derrateo altitud, Icc GE, autonomía, ATS | NCh 4-2003 / RIC N°08 |
| STS | Capacidad, transferencia, sobrecarga, redundancia 2N | TIA-942 |
| UPS | Banco de baterías, autonomía, tiempo de recarga | IEC 62040 |
| Trafo de aislamiento | Capacidad, Icc secundario, ΔV | IEC 60076 |
| ATS | Sincronización, tiempos de transferencia | RIC N°08 |
| Memoria SEC | Reporte DOCX + PDF + JSON EPC, con gate de emisión (FINAL/BORRADOR/INCOMPLETO) según parámetros TIPO-A confirmados | SEC Chile |

---

## Instalación

```bash
# Dependencias core (cálculo + reportes)
pip install openpyxl python-docx reportlab "matplotlib>=3.8" "numpy>=1.26"

# O desde pyproject.toml (incluye pytest)
pip install ".[dev]"

# Solo si se usa el subsistema RAG (rag_normativa/)
pip install ".[rag]"
```

---

## Uso

### CLI

```bash
python main.py --proyecto NOMBRE --excel circuitos.xlsx
```

Genera:

```
REPORTE_NOMBRE_FECHA.txt     ← resumen en texto
REPORTE_NOMBRE_FECHA.xlsx    ← reporte con colores
MEMORIA_NOMBRE_FECHA.docx    ← memoria técnica SEC
```

### GUI (tkinter)

```bash
python gui.py
```

Navegación por **7 fases del proceso SEC** (Datos → Cálculo base → Cortocircuito → Protección → Carga y red → Emergencia → Reporte), paleta **Tokyo Night**, con estado por módulo derivado de los datos cargados (sin datos / listo / calculado / alerta). Arquitectura en dos capas:
- `gui_core/` — lógica pura sin tkinter (`SesionProyecto`, registro de módulos, presentadores que orquestan el motor), 100 % testeable sin abrir ventanas.
- `gui/` — capa visual Tkinter delgada (`AppBT`, componentes reutilizables) que solo renderiza y enruta eventos sobre `gui_core`.

Alcance actual: fases 0–4 y 6 (reporte) completas con entrada/cálculo/resultado en pantalla; fase 5 (Emergencia: generador/ATS/UPS/STS) muestra estado pero sus paneles de parámetros de entrada quedan para una iteración posterior.

### Tests

```bash
pytest
```

---

## Estructura del proyecto

```
motor-calculo-bt/
├── calculos.py          caída de tensión, potencia, ampacidad
├── conductores.py       tablas AWG / MM2 (NEC / IEC 60228)
├── icc_punto.py         Icc aguas abajo, fase-neutro IEC 60364-4-41
├── transformador.py     Icc bornes BT (IEC 60909)
├── protecciones.py      disparo, poder de corte, tiempo desconexión
├── coordinacion.py      selectividad en cadena
├── demanda.py           FD, selección de transformador, acometida SEC
├── balance.py           balance de fases por tablero
├── motores.py           cálculo motor NCh 4-2003 + aporte al Icc (IEC 60909-4)
├── arc_flash.py         Arc Flash IEEE 1584-2002 (energía, frontera, Cat EPP)
├── tcc_curvas.py        catálogo de curvas TCC + fuente única de k térmico
├── red_desde_cadena.py  traduce la cadena de protecciones a un grafo bus/rama
├── flujo_nodal.py        flujo de carga nodal Newton-Raphson
├── generador.py         generador de emergencia + ATS
├── sts.py               Static Transfer Switch
├── ups.py               UPS + banco de baterías
├── trafo_iso.py         transformador de aislamiento
├── ats.py               Automatic Transfer Switch
├── perfiles.py          perfiles INDUSTRIAL / DATACENTER / COMERCIAL
├── sugerencias.py       recomendador de parámetros
├── excel.py             I/O Excel (openpyxl)
├── reporteria_sec.py    memoria SEC DOCX / PDF / JSON EPC + gate de completitud
├── graficos.py          curvas TCC, ΔV, autonomía (matplotlib)
├── persistencia.py      capa SQLite (corridas y eventos)
├── main.py              CLI principal
├── gui.py               lanzador delgado de la GUI (→ gui.app.main)
├── gui_core/            lógica de GUI sin tkinter (sesión, fases, presentadores)
├── gui/                 capa visual Tkinter (shell AppBT + componentes)
├── src/                 módulos de apoyo (arranque, memoria DOCX)
├── commissioning/       protocolos de puesta en marcha P1–P4
├── simulaciones/        escenarios y análisis de divergencias
├── rag_normativa/       RAG sobre corpus IEC/NCh/TIA (opcional)
├── presets/             datos de fabricante (alternadores Stamford)
├── tests/               suite de 766 tests (pytest)
└── auditoria/           auditoría integral + roadmap de desarrollo
```

---

## Limitaciones del modelo actual

- Ground Grid (IEEE 80), sistemas DC de datacenter, cortocircuito ANSI SC y análisis de armónicos no están implementados — quedan como expansión opcional (F4), a evaluar según demanda.
- El flujo de carga nodal usa `numpy` denso (adecuado para redes BT < 100 buses); `scipy.sparse` queda como mejora futura para redes grandes.
- GUI: la fase 5 (Emergencia) muestra estado de generador/ATS/UPS/STS pero aún no expone paneles de parámetros de entrada; y los módulos con salida no tabular (Icc trafo, balance, demanda, flujo nodal, reporte) calculan y registran resultado sin mostrar el detalle en pantalla todavía.

---

## Dependencias

| Paquete | Uso |
|---|---|
| openpyxl | I/O Excel |
| python-docx | memoria técnica DOCX |
| reportlab | reporte PDF |
| matplotlib / numpy | curvas y cálculos vectoriales |
| pytest | suite de tests (dev) |
| pyinstaller | empaquetado .exe (build) |
| llama-index / chromadb / sentence-transformers | RAG normativo (opcional) |
