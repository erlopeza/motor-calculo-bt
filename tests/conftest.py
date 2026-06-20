"""
conftest.py — fixtures compartidas para toda la suite de tests.

El directorio raíz del proyecto está en sys.path gracias a
pythonpath = ["."] en pyproject.toml, por lo que los módulos del
proyecto (calculos, icc_punto, generador, etc.) se importan
directamente sin prefijo de paquete.
"""
import pathlib

import pytest

# Ruta al directorio tests/ — útil para localizar archivos de datos de test
TESTS_DIR = pathlib.Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent


@pytest.fixture(scope="session")
def tests_dir() -> pathlib.Path:
    """Directorio tests/ — para acceder a archivos de datos de test."""
    return TESTS_DIR


@pytest.fixture(scope="session")
def circuitos_xlsx() -> pathlib.Path:
    """Excel de circuitos de prueba (MM2) reutilizado en varios tests."""
    return TESTS_DIR / "circuitos_test_mm2.xlsx"
