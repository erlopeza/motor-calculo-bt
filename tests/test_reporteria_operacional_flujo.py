"""Pruebas del contexto nodal que llega al reporte desde el CLI."""

from main import preparar_payload_reporte_cli
from red_desde_cadena import construir_red


def test_cli_payload_transporta_contexto_nodal_para_memoria():
    payload = preparar_payload_reporte_cli(
        [{"nombre": "Q1", "I_diseno": 40.0}],
        {},
        datos_transformador={"Icc_nom_kA": 12.0, "Vn_BT": 380.0},
        cadena=[{"nombre": "Q1", "Icc_kA": 8.0, "In_A": 40.0}],
        trafo_z_ohm=0.01,
        tension_sistema_v=380.0,
    )

    assert payload["cadena"][0]["nombre"] == "Q1"
    assert payload["trafo_z_ohm"] == 0.01
    assert payload["tension_sistema_v"] == 380.0


def test_cli_payload_nodal_es_consumible_por_constructor_de_red():
    payload = preparar_payload_reporte_cli(
        [{"nombre": "Q1", "I_diseno": 40.0, "cos_phi": 0.9}],
        {},
        cadena=[{"nombre": "Q1", "Icc_kA": 8.0, "In_A": 40.0}],
        trafo_z_ohm=0.01,
        tension_sistema_v=380.0,
    )

    red = construir_red(
        payload["cadena"],
        payload["trafo_z_ohm"],
        payload["circuitos"],
        vn_v=payload["tension_sistema_v"],
    )

    assert any(r.to_bus == "Q1" for r in red.ramas)
