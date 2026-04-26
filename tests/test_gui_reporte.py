"""Tests de humo para ReporteWindow."""
import tkinter as tk
from unittest.mock import patch

import pytest

from gui.reporte_window import ReporteWindow


@pytest.fixture(scope="module")
def root_tk():
    """Crea root oculto reutilizable para tests GUI."""
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk no disponible para humo GUI reporte: {error}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def ventana(root_tk):
    """Crea ReporteWindow con datos de calculo minimos."""
    win = ReporteWindow(root_tk, datos_calculo_fixture())
    yield win
    win.destroy()


def test_ventana_abre(ventana):
    assert isinstance(ventana, ReporteWindow)


def test_campos_obligatorios_existen(ventana):
    assert isinstance(ventana._entry_nombre, tk.Entry)
    assert isinstance(ventana._entry_instalador, tk.Entry)
    assert isinstance(ventana._entry_licencia, tk.Entry)


def test_boton_generar_existe(ventana):
    assert _existe_boton(ventana, "GENERAR MEMORIA")


def test_clase_options_correctas(ventana):
    assert ventana._clase_var.get() in {"A", "B"}


def test_sin_datos_no_genera(root_tk):
    win = ReporteWindow(root_tk, datos_calculo_fixture())
    with patch("gui.reporte_window.generar_memoria") as mock_generar:
        win._generar()
    mock_generar.assert_not_called()
    win.destroy()


def datos_calculo_fixture():
    return {
        "tension_v": 380,
        "potencia_total_kw": 10,
        "corriente_total_a": 20,
        "circuitos": [{"nombre": "C1", "long_m": 10, "seccion_mm2": 2.5, "ducto_mm": 20, "proteccion_a": 16, "curva": "C"}],
        "alimentador": {"seccion_mm2": 10, "long_m": 30, "caida_pct": 1.0, "tipo_cable": "Cu"},
        "emergencia": None,
        "arranque": None,
    }


def _existe_boton(widget, texto):
    """Busca un boton por texto en el arbol de widgets."""
    pendientes = [widget]
    while pendientes:
        actual = pendientes.pop()
        if isinstance(actual, tk.Button) and actual.cget("text") == texto:
            return True
        pendientes.extend(actual.winfo_children())
    return False
