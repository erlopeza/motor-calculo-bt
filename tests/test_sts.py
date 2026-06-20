from sts import (
    FACTOR_CRESTA_IT,
    calcular_sts,
    verificar_capacidad_sts,
    verificar_carga_no_lineal,
    verificar_overload,
    verificar_redundancia_2N,
    verificar_transferencia,
)


def test_capacidad_ok():
    r = verificar_capacidad_sts(P_carga_kVA=20, P_modulo_kVA=30, n_modulos=1)
    assert r["ok"] is True
    assert r["uso_pct"] < 80.0


def test_capacidad_excedida():
    r = verificar_capacidad_sts(P_carga_kVA=28, P_modulo_kVA=30, n_modulos=1)
    assert r["ok"] is False
    assert r["uso_pct"] > 80.0


def test_capacidad_modular():
    r = verificar_capacidad_sts(P_carga_kVA=35, P_modulo_kVA=30, n_modulos=2)
    assert r["P_sts_total_kVA"] == 60.0
    assert r["ok"] is True


def test_transferencia_it_ok():
    r = verificar_transferencia(t_transferencia_ms=4, tipo_carga="it")
    assert r["ok"] is True
    assert r["t_max_ms"] == 8.0


def test_transferencia_it_falla():
    r = verificar_transferencia(t_transferencia_ms=10, tipo_carga="it")
    assert r["ok"] is False


def test_transferencia_ups():
    r = verificar_transferencia(t_transferencia_ms=10, tipo_carga="ups")
    assert r["ok"] is True
    assert r["observacion"] == "transparente"


def test_overload_normal():
    r = verificar_overload(P_carga_kVA=30, P_sts_total_kVA=30, t_sobrecarga_seg=0)
    assert r["nivel"] == "normal"
    assert r["ok"] is True


def test_overload_leve():
    r = verificar_overload(P_carga_kVA=33, P_sts_total_kVA=30, t_sobrecarga_seg=30)
    assert r["nivel"] == "leve"
    assert r["ok"] is True


def test_overload_severo():
    r = verificar_overload(P_carga_kVA=48, P_sts_total_kVA=30, t_sobrecarga_seg=2)
    assert r["nivel"] == "severa"
    assert r["ok"] is False


def test_redundancia_2N_ok():
    r = verificar_redundancia_2N(P_carga_total_kVA=20, P_modulo_kVA=30, n_modulos=1, n_sts=2)
    assert r["ok_normal"] is True
    assert r["ok_falla"] is True


def test_redundancia_2N_falla_bus():
    r = verificar_redundancia_2N(P_carga_total_kVA=35, P_modulo_kVA=30, n_modulos=2, n_sts=2)
    assert r["ok_falla"] is True


def test_carga_no_lineal_ok():
    r = verificar_carga_no_lineal(P_total_kVA=30, P_no_lineal_kVA=10)
    assert r["ok"] is True


def test_carga_no_lineal_alerta():
    r = verificar_carga_no_lineal(P_total_kVA=30, P_no_lineal_kVA=25)
    assert r["ok"] is False


def test_calcular_sts_simple():
    r = calcular_sts(
        nombre="STS-A",
        modelo_sts="APC Upsilon STS30",
        P_modulo_kVA=30,
        n_modulos=1,
        t_transferencia_ms=4,
        V_nominal=380,
        P_carga_kVA=22,
        cos_phi_carga=0.9,
        tipo_carga="it",
        topologia="simple",
        n_sts=1,
        P_no_lineal_kVA=5,
        t_sobrecarga_seg=0,
    )
    assert r["capacidad"]["ok"] is True
    assert r["transferencia"]["ok"] is True
    assert r["redundancia_2N"] is None
    assert r["carga_no_lineal"]["factor_cresta_requerido"] == FACTOR_CRESTA_IT


def test_calcular_sts_2N():
    r = calcular_sts(
        nombre="STS-2N",
        modelo_sts="APC Upsilon STS30",
        P_modulo_kVA=30,
        n_modulos=1,
        t_transferencia_ms=4,
        V_nominal=380,
        P_carga_kVA=20,
        cos_phi_carga=0.9,
        tipo_carga="it",
        topologia="2N",
        n_sts=2,
        P_no_lineal_kVA=0,
        t_sobrecarga_seg=0,
    )
    assert r["topologia"] == "2n"
    assert r["redundancia_2N"] is not None
