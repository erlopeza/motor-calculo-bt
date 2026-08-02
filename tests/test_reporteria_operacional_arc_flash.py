"""Pruebas del cableado real de entradas Arc Flash hacia los reportes."""

from gui_core.presentadores import _circuitos_enriquecidos, _datos_run
from gui_core.sesion import SesionProyecto
from main import preparar_payload_reporte_cli


def test_cli_enriquece_circuitos_con_proteccion_para_arc_flash():
    circuitos = [{"nombre": "C1", "icc_ka": 4.2}]
    protecciones = {"C1": {"In_A": 63.0, "curva": "C"}}

    payload = preparar_payload_reporte_cli(
        circuitos,
        protecciones,
        datos_transformador={"Icc_nom_kA": 12.0, "Vn_BT": 380.0},
    )

    assert payload["circuitos"][0]["In_A"] == 63.0
    assert payload["circuitos"][0]["curva"] == "C"


def test_cli_arc_flash_recibe_barra_y_cabecera_explicita():
    payload = preparar_payload_reporte_cli(
        [{"nombre": "C1"}],
        {
            "C1": {"In_A": 63.0, "curva": "C"},
            "CABECERA": {"In_A": 400.0, "curva": "B"},
        },
        datos_transformador={"Icc_nom_kA": 12.0, "Vn_BT": 380.0},
    )

    assert payload["icc_barra_ka"] == 12.0
    assert payload["tension_barra_kv"] == 0.38
    assert payload["proteccion_cabecera"] == {"In_A": 400.0, "curva": "B"}


def test_gui_enriquece_circuitos_con_proteccion_para_arc_flash():
    sesion = SesionProyecto(
        circuitos=[{"nombre": "C1", "sistema": "3F"}],
        protecciones={"C1": {"In_A": 32.0, "curva": "D"}},
    )

    circuitos = _circuitos_enriquecidos(sesion)

    assert circuitos[0]["In_A"] == 32.0
    assert circuitos[0]["curva"] == "D"


def test_gui_arc_flash_expone_barra_y_cabecera_solo_si_es_explicita():
    sesion = SesionProyecto(
        circuitos=[{"nombre": "C1", "sistema": "3F"}],
        trafo={"kVA": 500.0, "Vn_BT": 380.0, "Ucc_pct": 5.0, "modo": "A"},
        protecciones={"C1": {"In_A": 32.0, "curva": "D"}},
    )
    sesion.trafo_z_ohm = 0.01444

    datos = _datos_run(sesion)

    assert datos["icc_barra_ka"] > 0
    assert "proteccion_cabecera" not in datos
