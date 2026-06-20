from ups import (
    calcular_autonomia,
    calcular_banco_baterias,
    calcular_tiempo_recarga,
    calcular_ups,
    verificar_capacidad_ups,
    verificar_tipo_ups,
)


def test_capacidad_ups_ok():
    r = verificar_capacidad_ups(P_carga_kVA=120, P_ups_kVA=250)
    assert r["ok"] is True
    assert r["uso_pct"] < 80.0


def test_capacidad_ups_excedida():
    r = verificar_capacidad_ups(P_carga_kVA=230, P_ups_kVA=250)
    assert r["ok"] is False


def test_banco_baterias_leo_arica():
    r = calcular_banco_baterias(
        n_baterias_serie=40,
        V_bat_unitaria=12.0,
        Ah_bat=100.0,
        n_strings=2,
        temperatura=25.0,
        eta_bat=0.85,
    )
    assert 81.0 <= r["E_kWh"] <= 82.0


def test_banco_derrateo_temperatura():
    r = calcular_banco_baterias(
        n_baterias_serie=40,
        V_bat_unitaria=12.0,
        Ah_bat=100.0,
        n_strings=2,
        temperatura=35.0,
        eta_bat=0.85,
    )
    assert r["factor_temp"] == 0.94


def test_autonomia_ok():
    r = calcular_autonomia(P_carga_kW=200.0, E_bat_kWh=60.0, nivel_infraestructura="tier3")
    assert r["estado"] == "OK"
    assert r["t_min"] >= 15.0


def test_autonomia_warning():
    r = calcular_autonomia(P_carga_kW=250.0, E_bat_kWh=45.0, nivel_infraestructura="tier3")
    assert r["estado"] == "WARNING"
    assert 10.0 <= r["t_min"] < 15.0


def test_autonomia_insuficiente():
    r = calcular_autonomia(P_carga_kW=300.0, E_bat_kWh=40.0, nivel_infraestructura="tier3")
    assert r["estado"] == "INSUFICIENTE"
    assert r["t_min"] < 10.0


def test_tiempo_recarga_ok():
    r = calcular_tiempo_recarga(Ah_efectivo=170.0, P_ups_kVA=250.0, V_string=480.0)
    assert r["ok"] is True
    assert r["t_recarga_hr"] <= 12.0


def test_tipo_ups_vfi_critico():
    r = verificar_tipo_ups(tipo="VFI", tipo_carga="it")
    assert r["ok_para_carga"] is True


def test_tipo_ups_vfd_critico():
    r = verificar_tipo_ups(tipo="VFD", tipo_carga="it")
    assert r["ok_para_carga"] is False


def test_calcular_ups_completo():
    r = calcular_ups(
        nombre="UPS-01",
        modelo_ups="Vertiv APM2",
        tipo_ups="VFI",
        P_ups_kVA=250,
        V_nominal=380,
        P_carga_kW=180,
        cos_phi_carga=0.9,
        tipo_carga="it",
        nivel_infraestructura="tier3",
        n_baterias_serie=40,
        V_bat_unitaria=12,
        Ah_bat=100,
        n_strings=2,
        temperatura=25,
    )
    for k in ["capacidad", "banco_baterias", "autonomia", "recarga", "tipo_validacion"]:
        assert k in r


def test_autonomia_leo_arica():
    banco = calcular_banco_baterias(
        n_baterias_serie=40,
        V_bat_unitaria=12.0,
        Ah_bat=100.0,
        n_strings=2,
        temperatura=25.0,
        eta_bat=0.85,
    )
    r = calcular_autonomia(
        P_carga_kW=220.0,
        E_bat_kWh=banco["E_kWh"],
        nivel_infraestructura="tier3",
    )
    assert 20.0 <= r["t_min"] <= 23.5
    assert r["estado"] == "OK"
