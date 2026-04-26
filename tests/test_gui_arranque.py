"""
Tests de humo para ArranqueWindow.
Verifica que la ventana abre, tiene los widgets esperados
y que _calcular() produce resultados o errores correctamente.
"""
import tkinter as tk

import pytest

from gui.arranque_window import ArranqueWindow, FG_ERROR


@pytest.fixture(scope="module")
def root_tk():
    """Fixture: crea un root oculto reutilizable para tests GUI."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def ventana(root_tk):
    """Fixture: crea una ArranqueWindow sobre root oculto."""
    win = ArranqueWindow(root_tk)
    yield win
    win.destroy()


def test_ventana_abre(ventana):
    assert isinstance(ventana, ArranqueWindow)


def test_campos_existen(ventana):
    for nombre in [
        "_entry_potencia",
        "_entry_tension",
        "_entry_fp",
        "_entry_rend",
        "_entry_factor_ia",
    ]:
        assert isinstance(getattr(ventana, nombre), tk.Entry)


def test_calcular_motor_5kw(ventana):
    _set_entry(ventana._entry_potencia, "5.0")
    _set_entry(ventana._entry_tension, "380")
    _set_entry(ventana._entry_fp, "0.85")
    _set_entry(ventana._entry_rend, "0.92")
    _set_entry(ventana._entry_factor_ia, "6.0")

    ventana._calcular()

    assert ventana._frame_resultados.winfo_children()


def test_calcular_error_campo_vacio(ventana):
    _set_entry(ventana._entry_potencia, "")

    ventana._calcular()

    assert _hay_error(ventana)


def test_calcular_error_valor_invalido(ventana):
    _set_entry(ventana._entry_potencia, "abc")

    ventana._calcular()

    assert _hay_error(ventana)


def _set_entry(entry, valor):
    """Reemplaza el contenido de un Entry."""
    entry.delete(0, tk.END)
    entry.insert(0, valor)


def _hay_error(ventana):
    """Retorna True si existe un label de error visible."""
    return any(
        isinstance(widget, tk.Label) and widget.cget("fg") == FG_ERROR
        for widget in ventana._frame_resultados.winfo_children()
    )
