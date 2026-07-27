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


@requiere_display
def test_app_render_no_tabulares_no_vacio(tmp_path):
    from gui.app import AppBT
    from gui.cargador import cargar_excel_a_sesion
    from pathlib import Path
    import gui.app as app_mod
    LIBRO = str(Path(app_mod.__file__).resolve().parents[1] / "circuitos.xlsx")
    app = AppBT()
    app.withdraw()
    app.carpeta_reportes = str(tmp_path)
    try:
        cargar_excel_a_sesion(LIBRO, app.sesion)
        for fase, mid in [(2, "icc_trafo"), (4, "balance"), (4, "demanda"),
                          (4, "flujo_nodal"), (6, "reporte")]:
            app.mostrar_fase(fase)
            app.ejecutar_modulo(mid)
            assert mid in app.sesion.resultados
            panel = next(p for p in app.paneles_actuales if p.modulo.id == mid)
            assert len(panel.contenedor_resultados.winfo_children()) >= 1, f"{mid} sin render"
    finally:
        app.destroy()


@requiere_display
def test_app_render_tabular_sigue_funcionando():
    from gui.app import AppBT
    app = AppBT()
    app.withdraw()
    try:
        app.sesion.cargar({"circuitos": [{"nombre": "C1", "sistema": "3F",
            "conductor": "6AWG", "S_mm2": 13.3, "I_max": 65, "paralelos": 1,
            "I_diseno": 40, "cos_phi": 0.9, "L_m": 15, "temp_amb": 30}]})
        app.mostrar_fase(1)
        app.ejecutar_modulo("dv")
        panel = next(p for p in app.paneles_actuales if p.modulo.id == "dv")
        assert len(panel.contenedor_resultados.winfo_children()) >= 1
    finally:
        app.destroy()
