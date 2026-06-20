# 07 — Dependencias y empaquetado

## `requirements.txt`

```
openpyxl==3.1.5          # Excel
pytest==9.0.2            # tests
pyinstaller==6.19.0      # .exe
python-docx==1.2.0       # memoria DOCX
reportlab==4.4.10        # reporte PDF
llama-index-core==0.13.6                  ┐
llama-index-vector-stores-chroma==0.6.3   │
chromadb==1.0.20                          │  RAG normativa
sentence-transformers==5.1.0              │  (deps pesadas / ML)
pdfplumber==0.11.7                        ┘
matplotlib>=3.8          # curvas (sin pin exacto)
numpy>=1.26              # curvas (sin pin exacto)
```

## H-06 (🟠 Medio) — Estado de dependencias y empaquetado

### Pins inconsistentes
- 10 de 12 deps están **fijadas con `==`** (reproducible) pero `matplotlib` y `numpy` usan `>=` (rango abierto). Inconsistente; con numpy 2.x ya instalado (2.3.2) hay riesgo de cambios de comportamiento. → fijar todas o ninguna.

### Dependencias pesadas no instaladas en el entorno auditado
Verificación en el entorno actual:

| Dependencia | Estado | Uso |
|---|---|---|
| openpyxl, python-docx, reportlab, pdfplumber, numpy, matplotlib, pytest | ✅ instaladas | núcleo + reportes + RAG (extracción) |
| `torch` (vía sentence-transformers), `chromadb`, `llama-index-*` | ❌ **no instaladas** | indexado/embeddings del RAG |

El módulo `rag_normativa/indexador.py` importa `sentence_transformers` y `chromadb` **de forma diferida (lazy, dentro de funciones)**, por lo que el import del módulo no falla y **la suite pasa sin esas deps**. Consecuencia: **el camino de indexado/embeddings del RAG no se ejercita en tests** en este entorno. → riesgo de regresión silenciosa en RAG.

### Sin estructura de packaging
| Falta | Impacto |
|---|---|
| `pyproject.toml` / `setup.py` | No instalable como paquete; imports dependen del cwd |
| `conftest.py` | rootdir/paths de test implícitos (ver `05`) |
| CI (GitHub Actions) | Los 480 tests no se ejecutan automáticamente en push/PR |
| Separación de extras | Las deps ML pesadas son obligatorias aunque el usuario solo quiera el motor de cálculo |

## PyInstaller
- Dos `.spec`: `calculo_bt.spec` (legado) y `motor_bt.spec` (FASE-F, `MotorBT.exe`). Ambos versionados pese a `*.spec` en `.gitignore` (ver H-09). Conviene conservar **solo el vigente** (`motor_bt.spec`) con `!motor_bt.spec` explícito y borrar el legado.

## Recomendaciones

| Acción | Prioridad |
|---|---|
| Añadir `pyproject.toml` con dependencias core + extras `[rag]` opcionales (torch/chromadb/llama-index) | Alta |
| Fijar `numpy`/`matplotlib` con `==` (o todas con `>=` coherente) | Media |
| Añadir CI que corra `pytest` en cada push/PR | Alta |
| Añadir `pytest-cov` y, si se versiona RAG, un job que instale extras y ejercite indexado | Media |
| Resolver duplicidad de `.spec` (conservar `motor_bt.spec`) | Baja |
