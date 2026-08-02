"""Pruebas del aporte de motores en el payload de memoria."""

from gui_core.presentadores import _datos_run
from gui_core.sesion import SesionProyecto
from main import preparar_payload_reporte_cli


def _motor():
    return {
        "nombre": "M1",
        "tipo_carga": "motor",
        "P_kW": 75.0,
        "sistema": "3F",
        "icc_ka": 4.0,
    }


def test_cli_payload_expone_aporte_agregado_de_motores():
    payload = preparar_payload_reporte_cli(
        [_motor()],
        {},
        datos_transformador={"Icc_nom_kA": 12.0, "Vn_BT": 380.0},
    )

    assert payload["icc_red_ka"] == 12.0
    assert payload["icc_barra_ka"] > payload["icc_red_ka"]
    assert payload["aporte_motores"][0]["nombre"] == "M1"


def test_gui_payload_expone_aporte_agregado_de_motores():
    sesion = SesionProyecto(
        circuitos=[_motor()],
        trafo={"kVA": 500.0, "Vn_BT": 380.0, "Ucc_pct": 5.0, "modo": "A"},
    )

    datos = _datos_run(sesion)

    assert datos["icc_barra_ka"] > datos["icc_red_ka"]
    assert datos["aporte_motores"][0]["nombre"] == "M1"


def test_aporte_no_reemplaza_icc_individual_del_circuito():
    circuito = _motor()
    payload = preparar_payload_reporte_cli(
        [circuito],
        {},
        datos_transformador={"Icc_nom_kA": 12.0, "Vn_BT": 380.0},
    )

    assert payload["circuitos"][0]["icc_ka"] == 4.0


def test_sin_motores_conserva_icc_de_red():
    payload = preparar_payload_reporte_cli(
        [{"nombre": "L1", "tipo_carga": "alumbrado"}],
        {},
        datos_transformador={"Icc_nom_kA": 12.0, "Vn_BT": 380.0},
    )

    assert payload["icc_barra_ka"] == 12.0
    assert payload["aporte_motores"] == []


def test_cli_motor_sin_p_kw_usa_potencia_electrica_del_circuito():
    circuito = _motor()
    circuito.pop("P_kW")
    circuito.update({"I_diseno": 120.0, "cos_phi": 0.85})

    payload = preparar_payload_reporte_cli(
        [circuito],
        {},
        datos_transformador={"Icc_nom_kA": 12.0, "Vn_BT": 380.0},
    )

    assert payload["aporte_motores"]
    assert payload["aporte_motores"][0]["P_kW"] > 0


def test_gui_motor_sin_p_kw_usa_potencia_electrica_del_circuito():
    circuito = _motor()
    circuito.pop("P_kW")
    circuito.update({"I_diseno": 120.0, "cos_phi": 0.85})
    sesion = SesionProyecto(
        circuitos=[circuito],
        trafo={"kVA": 500.0, "Vn_BT": 380.0, "Ucc_pct": 5.0, "modo": "A"},
    )

    datos = _datos_run(sesion)

    assert datos["aporte_motores"]
    assert datos["aporte_motores"][0]["P_kW"] > 0
