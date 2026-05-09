from demanda import calcular_demanda_mixta, calcular_fd_alumbrado_ric


def test_fd_alumbrado_tramo_hasta_2kw():
    r = calcular_fd_alumbrado_ric(1.5)
    assert r["fd"] == 1.00


def test_fd_alumbrado_tramo_2_a_5kw():
    r = calcular_fd_alumbrado_ric(3.0)
    assert r["fd"] == 0.90


def test_fd_alumbrado_tramo_5_a_10kw():
    r = calcular_fd_alumbrado_ric(7.5)
    assert r["fd"] == 0.85


def test_fd_alumbrado_tramo_10_a_20kw():
    r = calcular_fd_alumbrado_ric(15.0)
    assert r["fd"] == 0.80


def test_fd_alumbrado_tramo_20_a_30kw():
    r = calcular_fd_alumbrado_ric(25.0)
    assert r["fd"] == 0.75


def test_fd_alumbrado_tramo_mayor_30kw():
    r = calcular_fd_alumbrado_ric(50.0)
    assert r["fd"] == 0.70


def test_fd_alumbrado_limite_exacto_2kw():
    r = calcular_fd_alumbrado_ric(2.0)
    assert r["fd"] == 1.00


def test_fd_alumbrado_retorna_es_normativo_true():
    r = calcular_fd_alumbrado_ric(12.0)
    assert r["es_normativo"] is True


def test_demanda_mixta_solo_alumbrado():
    r = calcular_demanda_mixta(P_alumbrado_kW=10.0)
    assert r["fd_alumbrado"] == 0.85
    assert r["fd_fuerza"] == 1.0
    assert r["advertencia"] is None


def test_demanda_mixta_con_fuerza():
    r = calcular_demanda_mixta(P_alumbrado_kW=5.0, P_fuerza_kW=10.0)
    assert r["fd_fuerza"] == 1.0
    assert r["advertencia"] is not None


def test_demanda_mixta_total_correcto():
    r = calcular_demanda_mixta(P_alumbrado_kW=10.0, P_fuerza_kW=5.0)
    assert r["P_demanda_alumbrado"] == 8.5
    assert r["P_demanda_fuerza"] == 5.0
    assert r["P_demanda_total_kW"] == 13.5


def test_demanda_mixta_norma_presente():
    r = calcular_demanda_mixta(P_alumbrado_kW=10.0)
    assert "RIC N°03" in r["norma"]
