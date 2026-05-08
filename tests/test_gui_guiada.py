"""Tests de humo para GuiadaWindow."""
import ast
from pathlib import Path
import tkinter as tk

import pytest

from gui.guiada_window import GuiadaWindow, FG_ERROR


@pytest.fixture(scope="module")
def root_tk():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk no disponible para humo GUI guiada: {error}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def ventana(root_tk):
    win = GuiadaWindow(root_tk)
    yield win
    win.destroy()


def test_ventana_abre(ventana):
    assert isinstance(ventana, GuiadaWindow)


def test_controles_existen(ventana):
    assert hasattr(ventana, "_combo_perfil")
    assert isinstance(ventana._entry_carga, tk.Entry)
    assert isinstance(ventana._entry_potencia, tk.Entry)
    assert isinstance(ventana._entry_cantidad, tk.Entry)


def test_perfil_actualiza_resumen(ventana):
    ventana._combo_perfil.set("DATACENTER")
    ventana._actualizar_perfil()
    assert "DATACENTER" in ventana._resultado_texto.cget("text")
    assert "cos_phi_base" in ventana._resultado_texto.cget("text")


def test_carga_y_potencia_muestran_resumen(ventana):
    ventana._combo_perfil.set("DATACENTER")
    _set_entry(ventana._entry_carga, "CRAC")
    _set_entry(ventana._entry_potencia, "35000")
    _set_entry(ventana._entry_cantidad, "2")
    ventana._sugerir()
    texto = ventana._resultado_texto.cget("text")
    assert "CRAC" in texto
    assert "70000.0 W" in texto
    assert "sin faltantes para v1" in texto


def test_error_si_falta_carga(ventana):
    _set_entry(ventana._entry_carga, "")
    ventana._sugerir()
    assert ventana._resultado_texto.cget("fg") == FG_ERROR


def test_guiada_no_importa_modulos_prohibidos():
    ruta = Path(__file__).resolve().parents[1] / "gui" / "guiada_window.py"
    tree = ast.parse(ruta.read_text(encoding="utf-8"))
    prohibidos = {"calculos", "conductores", "transformador", "icc_punto"}
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not (imports & prohibidos)


def _set_entry(entry, valor):
    entry.delete(0, tk.END)
    entry.insert(0, valor)
