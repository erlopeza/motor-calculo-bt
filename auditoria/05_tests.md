# 05 — Tests

## Ejecución real de la suite

Comando: `python -m pytest -q --no-header -p no:cacheprovider`
Entorno: Python 3.13.14, pytest 9.0.2. Salida completa en [`_pytest_output.txt`](_pytest_output.txt).

```
........................................................................ [ 15%]
........................................................................ [ 30%]
........................................................................ [ 45%]
........................................................................ [ 60%]
........................................................................ [ 75%]
........................................................................ [ 90%]
................................................                         [100%]
480 passed in 23.94s
EXIT_CODE=0
```

✅ **480 tests, 100 % passed, 0 fallos, 0 errores, 23,94 s.** El estado de la suite es **verde y rápido**. (Los tests de GUI usan `pytest.skip` condicional si Tk no está disponible; en este entorno Tk estaba disponible y se ejecutaron.)

## H-05 (🟠 Medio) — Doble layout de tests

| Ubicación | Archivos | Funciones `test_*` |
|---|---|---|
| Raíz (`test_*.py`) | 12 | 208 |
| `tests/` | 26 | 250 |
| **Total** | **38** | **458** (480 con parametrize) |

Archivos en raíz: `test_ats, test_calculos, test_conductores, test_exportar_eventos, test_generador, test_motores, test_persistencia, test_reporteria_sec, test_sts, test_trafo_iso, test_ups, test_validacion_ingenieril_rapida`.

- ✅ **No hay colisiones de nombre** entre raíz y `tests/` (verificado con `comm`), por eso pytest no falla en colección.
- 🟠 **Pero** el layout dual es confuso: los tests "Ciclo 0/1" y de módulos nuevos viven en `tests/`, mientras los antiguos quedaron en la raíz. No hay `conftest.py` ni `pytest.ini`/`[tool.pytest]`, por lo que la configuración de rutas es implícita (depende del rootdir y de que la raíz esté en `sys.path`).

## Hallazgos de configuración

| Hallazgo | Severidad |
|---|---|
| Sin `conftest.py` (fixtures/rootdir/paths centralizados) | Medio |
| Sin `pytest.ini` / `[tool.pytest.ini_options]` (testpaths, markers) | Medio |
| Sin medición de cobertura (`pytest-cov` no está en requirements) | Medio |
| `.tmp_*` y `.pytest_cache` se generan en cada corrida (algunos quedaron versionados, ver H-02) | — |
| Tests de GUI con `skip` condicional por Tk — correcto y portable | ✅ |

## Recomendaciones

| Acción | Prioridad |
|---|---|
| Mover los 12 `test_*.py` de raíz a `tests/` (layout único) | Media |
| Añadir `conftest.py` (rootdir + fixtures de tmp dirs) y `[tool.pytest.ini_options]` con `testpaths=["tests"]` | Media |
| Añadir `pytest-cov` y publicar cobertura para detectar líneas muertas (ver `04`) | Media |
| Asegurar que los tmp dirs de test usen `tmp_path` de pytest en vez de `.tmp_*` en el repo | Media |
