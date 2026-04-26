"""Tests de humo para EmergenciaWindow."""
import tkinter as tk

import pytest

from gui.emergencia_window import EmergenciaWindow, FG_ERROR


@pytest.fixture(scope="module")
def root_tk():
    """Crea root oculto reutilizable para tests GUI."""
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk no disponible para humo GUI M9: {error}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def ventana(root_tk):
    """Crea una EmergenciaWindow sobre root oculto."""
    win = EmergenciaWindow(root_tk)
    yield win
    win.destroy()


def test_ventana_abre(ventana):
    assert isinstance(ventana, EmergenciaWindow)


def test_campos_existen(ventana):
    assert hasattr(ventana, "_combo_tipo_consumo")
    assert isinstance(ventana._entry_num_pisos, tk.Entry)
    assert isinstance(ventana._entry_cargas, tk.Entry)


def test_calcular_grupo_ok(ventana):
    ventana._combo_tipo_consumo.set("bomba_incendio")
    ventana._calcular_grupo()
    assert "Grupo 1" in ventana._resultado_grupo.cget("text")


def test_calcular_autonomia_ok(ventana):
    _set_entry(ventana._entry_grupo, "0")
    _set_entry(ventana._entry_num_pisos, "6")
    ventana._calcular_autonomia()
    assert "120 min" in ventana._resultado_autonomia.cget("text")


def test_calcular_generador_ok(ventana):
    _set_entry(ventana._entry_cargas, "10,20,5")
    ventana._calcular_generador()
    assert "54.69 kVA" in ventana._resultado_generador.cget("text")


def test_error_campo_vacio(ventana):
    _set_entry(ventana._entry_cargas, "")
    ventana._calcular_generador()
    assert ventana._resultado_generador.cget("fg") == FG_ERROR


def _set_entry(entry, valor):
    """Reemplaza el contenido de un Entry."""
    entry.delete(0, tk.END)
    entry.insert(0, valor)
