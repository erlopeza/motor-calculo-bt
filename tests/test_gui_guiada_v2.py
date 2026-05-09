"""Tests de humo para GuiadaWindow v2."""
import ast
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from unittest.mock import Mock

import pytest

from gui.guiada_window import GuiadaWindow, FG_ERROR


@pytest.fixture(scope="module")
def root_tk():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk no disponible para humo GUI guiada v2: {error}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def ventana(root_tk):
    win = GuiadaWindow(root_tk)
    yield win
    win.destroy()


def test_guiada_v2_etapa2_no_aparece_sin_datos(ventana):
    assert not ventana._frame_etapa2.winfo_ismapped()


def test_guiada_v2_etapa2_aparece_con_datos_suficientes(ventana):
    _completar_etapa1(ventana)
    assert ventana._frame_etapa2.winfo_ismapped()


def test_guiada_v2_calculo_llama_calculos_py(ventana, monkeypatch):
    fake = _fake_calculos()
    import_mock = Mock(return_value=fake)
    monkeypatch.setattr("gui.guiada_window.importlib.import_module", import_mock)

    _completar_etapa1(ventana)
    _set_entry(ventana._entry_longitud, "40")
    ventana._calcular_etapa2()

    import_mock.assert_called_once_with("calculos")
    assert fake.sugerir_conductor.called
    assert fake.calcular_caida_tension.called
    assert fake.clasificar_caida.called


def test_guiada_v2_resultado_muestra_campos_correctos(ventana, monkeypatch):
    monkeypatch.setattr("gui.guiada_window.importlib.import_module", Mock(return_value=_fake_calculos()))

    _completar_etapa1(ventana)
    _set_entry(ventana._entry_longitud, "40")
    ventana._calcular_etapa2()

    texto = ventana._resultado_texto.cget("text")
    assert "Seccion sugerida" in texto
    assert "Caida de tension" in texto
    assert "Corriente estimada" in texto
    assert "Advertencias" in texto


def test_guiada_v2_sin_longitud_no_calcula(ventana, monkeypatch):
    fake = _fake_calculos()
    import_mock = Mock(return_value=fake)
    monkeypatch.setattr("gui.guiada_window.importlib.import_module", import_mock)

    _completar_etapa1(ventana)
    _set_entry(ventana._entry_longitud, "")
    ventana._calcular_etapa2()

    import_mock.assert_not_called()
    assert ventana._resultado_texto.cget("fg") == FG_ERROR


def test_guiada_v2_no_importa_modulos_prohibidos():
    ruta = Path(__file__).resolve().parents[1] / "gui" / "guiada_window.py"
    tree = ast.parse(ruta.read_text(encoding="utf-8"))
    prohibidos = {"transformador", "icc_punto", "protecciones"}
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not (imports & prohibidos)


def _completar_etapa1(ventana):
    ventana._combo_perfil.set("DATACENTER")
    _set_entry(ventana._entry_carga, "CRAC")
    _set_entry(ventana._entry_potencia, "35000")
    _set_entry(ventana._entry_cantidad, "1")
    ventana._sugerir()


def _fake_calculos():
    return SimpleNamespace(
        sugerir_conductor=Mock(return_value=("6MM2", 6.0, 1.2)),
        calcular_caida_tension=Mock(return_value=(4.56, 1.2)),
        clasificar_caida=Mock(return_value="OPTIMO"),
    )


def _set_entry(entry, valor):
    entry.delete(0, tk.END)
    entry.insert(0, valor)
