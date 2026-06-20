# Motor de Cálculo BT

Herramienta de cálculo eléctrico para instalaciones de baja tensión (BT) según normativa chilena (SEC/NCh) e internacional (IEC/NEC). Lee datos desde Excel, calcula y verifica toda la instalación, y genera la memoria técnica SEC en DOCX/PDF.

**Versión:** 2.0  
**Python:** ≥ 3.12  
**Tests:** 480 (475 passed + 5 skipped RAG) — `pytest` verde en cada commit

---

## Qué calcula

| Módulo | Capacidad | Norma |
|---|---|---|
| Caída de tensión | ΔV por circuito y acumulada, corrección por temperatura y paralelos | NEC 310.15 / IEC 60228 |
| Cortocircuito | Icc trifásica y fase-neutro aguas abajo, reducción por cable | IEC 60909 / IEC 60364-4-41 |
| Protecciones | Disparo magnético (B/C/D/K/MA), poder de corte, tiempo de desconexión | IEC 60898 / 60947-2 |
| Coordinación | Selectividad en cadena, verificación IEC 60364 | IEC 60364 |
| Demanda y balance | FD por tipo de carga, balance de fases, selección de transformador | RIC N°10 |
| Motores (M8) | Corriente nominal y arranque, ΔV arranque, conductor, guardamotor | NCh 4-2003 §12.28 |
| Generador (M9) | Potencia mínima, derrateo altitud, Icc GE, autonomía, ATS | NCh 4-2003 / RIC N°08 |
| STS | Capacidad, transferencia, sobrecarga, redundancia 2N | TIA-942 |
| UPS | Banco de baterías, autonomía, tiempo de recarga | IEC 62040 |
| Trafo de aislamiento | Capacidad, Icc secundario, ΔV | IEC 60076 |
| ATS | Sincronización, tiempos de transferencia | RIC N°08 |
| Memoria SEC | Reporte DOCX + PDF con gate de emisión (BORRADOR/INCOMPLETO) | SEC Chile |

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
├── motores.py           cálculo motor NCh 4-2003
├── generador.py         generador de emergencia + ATS
├── sts.py               Static Transfer Switch
├── ups.py               UPS + banco de baterías
├── trafo_iso.py         transformador de aislamiento
├── ats.py               Automatic Transfer Switch
├── perfiles.py          perfiles INDUSTRIAL / DATACENTER / COMERCIAL
├── sugerencias.py       recomendador de parámetros
├── excel.py             I/O Excel (openpyxl)
├── reporteria_sec.py    memoria SEC DOCX / PDF
├── graficos.py          curvas TCC, ΔV, autonomía (matplotlib)
├── persistencia.py      capa SQLite (corridas y eventos)
├── main.py              CLI principal
├── gui.py               GUI tkinter
├── src/                 módulos de apoyo (arranque, memoria DOCX)
├── commissioning/       protocolos de puesta en marcha P1–P4
├── simulaciones/        escenarios y análisis de divergencias
├── rag_normativa/       RAG sobre corpus IEC/NCh/TIA (opcional)
├── presets/             datos de fabricante (alternadores Stamford)
├── tests/               suite de 480 tests (pytest)
└── auditoria/           auditoría integral + roadmap de desarrollo
```

---

## Limitaciones del modelo actual

- Impedancia de cable: modelo resistivo puro (sin reactancia X). Para cables > 200 m o secciones grandes el error es apreciable. **En roadmap F1-P0.1.**
- Sin aporte de motores al cortocircuito (IEC 60909 §4.3). **En roadmap F1-P0.2.**
- Sin Arc Flash IEEE 1584-2018. **En roadmap F2-P1.1.**
- Sin flujo de carga nodal (análisis de red acoplada). **En roadmap F3-P2.1.**

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
