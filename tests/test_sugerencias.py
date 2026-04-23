from sugerencias import (
    detectar_sobredimensionamiento,
    sugerir_carga_por_nombre,
    sugerir_parametros_ge,
    sugerir_parametros_motor,
)


def test_sugerir_ge_normal_retorna_parametros():
    r = sugerir_parametros_ge(500, "normal")
    assert r["parametros"]["P_kVA_requerido"] == 500.0
    assert r["parametros"]["t_arranque_ms"] == 10000


def test_sugerir_ge_critico_sts_recomienda_topologia():
    r = sugerir_parametros_ge(500, "critico_sts")
    assert r["topologia_recomendada"] == "STS_O_UPS_REQUERIDO"


def test_sugerir_motor_dol_factor_6():
    r = sugerir_parametros_motor(45, "DOL")
    assert r["parametros"]["factor_arranque"] == 6.0


def test_sugerir_motor_vfd_factor_1_2():
    r = sugerir_parametros_motor(45, "VFD")
    assert r["parametros"]["factor_arranque"] == 1.2


def test_sugerir_carga_tv_por_nombre():
    r = sugerir_carga_por_nombre("TV")
    assert r["P_W"] == 150


def test_sugerir_carga_fuzzy_television_encuentra_tv():
    r = sugerir_carga_por_nombre("television")
    assert r["nombre"] == "TV"


def test_detectar_sobredimensionamiento_activa_alerta():
    r = detectar_sobredimensionamiento(180, 100, tolerancia_pct=30)
    assert r["sobredimensionado"] is True


def test_detectar_sobredimensionamiento_dentro_tolerancia_no_alerta():
    r = detectar_sobredimensionamiento(120, 100, tolerancia_pct=30)
    assert r["sobredimensionado"] is False
