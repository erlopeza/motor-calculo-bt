import pytest
from gui.headless import hay_display

requiere_display = pytest.mark.skipif(not hay_display(), reason="sin display (headless)")


def test_hay_display_es_bool():
    assert isinstance(hay_display(), bool)


@requiere_display
def test_badge_estado_muestra_color_por_estado():
    import tkinter as tk
    from gui_core.estado import Estado, color_de_estado
    from gui.componentes import BadgeEstado
    root = tk.Tk(); root.withdraw()
    try:
        b = BadgeEstado(root, Estado.CALCULADO)
        assert b.cget("foreground") == color_de_estado(Estado.CALCULADO) or b.color == color_de_estado(Estado.CALCULADO)
        b.set_estado(Estado.ALERTA)
        assert b.color == color_de_estado(Estado.ALERTA)
    finally:
        root.destroy()


@requiere_display
def test_boton_accion_deshabilitado():
    import tkinter as tk
    from gui.componentes import BotonAccion
    root = tk.Tk(); root.withdraw()
    try:
        llamado = []
        btn = BotonAccion(root, "Calcular", lambda: llamado.append(1))
        btn.set_habilitado(False)
        assert str(btn["state"]) == "disabled"
        btn.set_habilitado(True)
        assert str(btn["state"]) == "normal"
    finally:
        root.destroy()


@requiere_display
def test_tabla_resultados_llena_filas():
    import tkinter as tk
    from gui.componentes import TablaResultados
    root = tk.Tk(); root.withdraw()
    try:
        t = TablaResultados(root, ["Circuito", "Icc (kA)"])
        t.set_filas([["C-01", "10.8"], ["C-02", "9.1"]])
        assert t.num_filas() == 2
    finally:
        root.destroy()
