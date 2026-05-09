from ups import (
    ETA_BAT_DEFAULT,
    ETA_UPS_DEFAULT,
    calcular_banco_baterias,
    calcular_ups,
)


def _ups_base(**overrides):
    datos = {
        "nombre": "UPS-X",
        "modelo_ups": "GENERICO",
        "tipo_ups": "VFI",
        "P_ups_kVA": 250,
        "V_nominal": 380,
        "P_carga_kW": 180,
        "cos_phi_carga": 0.9,
        "tipo_carga": "it",
        "nivel_infraestructura": "tier3",
        "n_baterias_serie": 40,
        "V_bat_unitaria": 12,
        "Ah_bat": 100,
        "n_strings": 2,
        "temperatura": 30.0,
        "eta_ups": 0.93,
        "eta_bat": 0.84,
    }
    datos.update(overrides)
    return datos


def test_ups_sin_defaults_no_marca_usa_defaults():
    r = calcular_ups(**_ups_base())
    assert r["usa_defaults"] is False
    assert r["defaults_aplicados"] == []


def test_ups_con_eta_ups_omitido_marca_usa_defaults():
    datos = _ups_base()
    datos.pop("eta_ups")
    r = calcular_ups(**datos)
    assert r["usa_defaults"] is True
    assert "eta_ups" in r["defaults_aplicados"]


def test_ups_con_eta_bat_omitido_marca_usa_defaults():
    datos = _ups_base()
    datos.pop("eta_bat")
    r = calcular_ups(**datos)
    assert r["usa_defaults"] is True
    assert "eta_bat" in r["defaults_aplicados"]


def test_ups_con_temperatura_omitida_marca_usa_defaults():
    datos = _ups_base()
    datos.pop("temperatura")
    r = calcular_ups(**datos)
    assert r["usa_defaults"] is True
    assert "temperatura" in r["defaults_aplicados"]


def test_ups_lista_defaults_aplicados_es_lista():
    r = calcular_ups(**_ups_base())
    assert isinstance(r["defaults_aplicados"], list)
    assert r["defaults_aplicados"] == []


def test_ups_calcular_banco_baterias_retorna_usa_defaults():
    r = calcular_banco_baterias(
        n_baterias_serie=40,
        V_bat_unitaria=12.0,
        Ah_bat=100.0,
        n_strings=2,
    )
    assert r["usa_defaults"] is True
    assert "temperatura" in r["defaults_aplicados"]
    assert "eta_bat" in r["defaults_aplicados"]
    assert ETA_UPS_DEFAULT == 0.94
    assert ETA_BAT_DEFAULT == 0.85
