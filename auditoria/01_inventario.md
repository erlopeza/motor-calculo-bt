# 01 — Inventario y estructura

## Métricas globales (archivos versionados)

| Métrica | Valor |
|---|---|
| Archivos versionados (git) | 189 |
| Módulos Python productivos (no-test) | 53 |
| LOC código productivo | ~14.199 |
| Archivos de test | 38 (12 raíz + 26 `tests/`) |
| LOC tests | ~4.905 |
| Funciones/clases en código productivo | ~470 (def/class) |
| Commits | 76 |
| Ramas | 1 (`main`) |
| Tags | 0 |

## Árbol de paquetes (código productivo)

```
motor-calculo-bt/
├── main.py                 (1137 LOC) — orquestador CLI + ensamblado de reporte
├── gui.py                  (1812 LOC) — interfaz tkinter monolítica
├── excel.py                (1034 LOC) — lectura Excel + exportación de reportes
│
│   # Núcleo de cálculo eléctrico (raíz, plano)
├── conductores.py          — tablas AWG/MM2 + factores temperatura
├── calculos.py             — caída de tensión, potencia, clasificación
├── transformador.py        — Icc de transformador, clasificación
├── icc_punto.py            — Icc por punto, fase-neutro (IEC 60364-4-41)
├── protecciones.py         — umbral magnético, disparo, poder de corte
├── coordinacion.py         — selectividad, tiempos de disparo, IEC 60364
├── balance.py              — balance de tableros, factor simultaneidad
├── demanda.py              — demanda (RIC), FD alumbrado, acometida SEC
├── motores.py              — arranque motores NCh 12.28, guardamotor
├── generador.py            — verificación GE, derrateo altitud, Icc GE
├── sts.py                  — transferencia estática, topología 2N
├── trafo_iso.py            — transformador de aislamiento
├── ups.py                  — banco de baterías, autonomía TIA-942
├── ats.py                  — transferencia automática, sincronización
├── perfiles.py             — perfiles INDUSTRIAL/DATACENTER/COMERCIAL
├── sugerencias.py          — recomendador de parámetros por perfil
├── coordinacion.py / icc_punto.py / ...
├── persistencia.py         — capa SQLite (schema.sql)
├── dashboard.py            — dashboard de eventos
├── exportar_eventos.py     — export JSON/CSV de eventos
├── reporteria_sec.py       — reporte SEC (DOCX/PDF)
├── parser_reporte.py       — parser de reportes de texto
├── graficos.py             — curvas TCC/ΔV (matplotlib)
│
├── src/                    # Fachada GUI (M8/M9) + memoria
│   ├── arranque_motores.py     — fachada arranque (duplica motores.py)
│   ├── sistemas_emergencia.py  — M9 RIC-N08
│   └── generador_memoria.py    — memoria explicativa DOCX
│
├── gui/                    # Ventanas tkinter separadas
│   ├── arranque_window.py
│   ├── emergencia_window.py
│   ├── guiada_window.py
│   └── reporte_window.py
│
├── commissioning/          # Puesta en marcha (P1–P4)
│   ├── p1_continuidad.py
│   ├── p2_motores.py
│   ├── p3_transferencia.py
│   ├── p4_icc.py
│   └── reporte.py
│
├── simulaciones/           # Escenarios de simulación
│   ├── analizador.py
│   ├── escenarios.py
│   └── reporte.py
│
├── rag_normativa/          # RAG sobre normativa (llama-index/chroma)
│   ├── extractor.py        — extracción PDF (pdfplumber)
│   ├── chunker.py
│   ├── indexador.py        — embeddings (sentence-transformers) + chroma
│   ├── consultor.py
│   ├── referencias_iec.py
│   └── corpus/iec_ref/     — IEC 60076/60909/60947/62040, NCh 4, TIA-942 (.md)
│
└── presets/
    └── alternadores/stamford_hci544d.py
```

## Observaciones estructurales

1. **Capa de cálculo "plana" en la raíz** (~25 módulos) conviviendo con paquetes (`src/`, `gui/`, `commissioning/`, `simulaciones/`, `rag_normativa/`). No hay un paquete raíz único (`motor_bt/`), lo que dificulta empaquetado e import absoluto. → ver H-06.
2. **`gui.py` (1812 LOC) monolítico** coexiste con el paquete `gui/` (ventanas separadas). Indica una migración a mitad de camino de GUI monolítica → modular.
3. **`src/` no es la raíz del código**, sino una fachada para GUI (M8/M9) más generación de memoria. Nombre confuso: sugiere "fuente principal" pero contiene un subconjunto. → ver H-04.
4. **Corpus normativo versionado en Markdown** (`rag_normativa/corpus/iec_ref/`) — correcto, es dato de entrada del RAG.
5. **Fixtures Excel de test** (`circuitos_*_test.xlsx`, `tests/circuitos_test_mm2.xlsx`) versionados — correcto, son entradas de prueba.
