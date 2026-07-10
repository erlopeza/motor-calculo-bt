import pytest
from gui.headless import hay_display

requiere_display = pytest.mark.skipif(not hay_display(), reason="sin display (headless)")


@requiere_display
def test_app_arranca_y_selecciona_fase():
    from gui.app import AppBT
    app = AppBT()
    app.withdraw()
    try:
        assert app.sesion is not None
        app.mostrar_fase(1)                     # cálculo base
        assert app.fase_actual == 1
        assert len(app.paneles_actuales) >= 1   # ΔV, capacidad, sugerencia
    finally:
        app.destroy()


@requiere_display
def test_app_calcular_registra_y_refresca():
    from gui.app import AppBT
    app = AppBT()
    app.withdraw()
    try:
        app.sesion.cargar({"circuitos": [{"nombre": "C1", "sistema": "3F",
            "conductor": "6AWG", "S_mm2": 13.3, "I_max": 65, "paralelos": 1,
            "I_diseno": 40, "cos_phi": 0.9, "L_m": 15, "temp_amb": 30}]})
        app.mostrar_fase(1)
        app.ejecutar_modulo("dv")               # llama presentador + registrar
        assert "dv" in app.sesion.resultados
    finally:
        app.destroy()


def test_app_importable_sin_display():
    import gui.app          # importar no debe crear ventanas
    assert hasattr(gui.app, "AppBT")
