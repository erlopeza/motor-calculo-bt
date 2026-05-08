import pytest

from sugerencias import (
    detectar_sobredimensionamiento,
    listar_perfiles,
    sugerir_carga_por_nombre,
    sugerir_parametros_ge,
    sugerir_parametros_motor,
    sugerir_parametros_por_perfil,
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


def test_listar_perfiles_incluye_tres_perfiles_guiados():
    perfiles = listar_perfiles()
    assert {"INDUSTRIAL", "DATACENTER", "COMERCIAL"}.issubset(set(perfiles))


def test_sugerir_carga_industrial_por_nombre():
    r = sugerir_carga_por_nombre("bomba", perfil="INDUSTRIAL")
    assert r["nombre"] == "Bomba_industrial"
    assert r["perfil"] == "INDUSTRIAL"


def test_sugerir_carga_datacenter_por_nombre():
    r = sugerir_carga_por_nombre("crac", perfil="DATACENTER")
    assert r["nombre"] == "CRAC"
    assert r["perfil"] == "DATACENTER"


def test_sugerir_carga_comercial_por_nombre():
    r = sugerir_carga_por_nombre("tomacorriente", perfil="COMERCIAL")
    assert r["nombre"] == "Tomacorrientes"
    assert r["perfil"] == "COMERCIAL"


def test_sugerir_carga_fuzzy_respeta_perfil():
    r = sugerir_carga_por_nombre("rack servidores", perfil="DATACENTER")
    assert r["nombre"] == "Rack_servidores"
    assert r["perfil"] == "DATACENTER"


def test_sugerir_carga_sin_perfil_mantiene_fallback_residencial():
    r = sugerir_carga_por_nombre("television")
    assert r["nombre"] == "TV"
    assert r["perfil"] == "RESIDENCIAL"


def test_sugerir_parametros_por_perfil_retorno_exacto():
    r = sugerir_parametros_por_perfil("DATACENTER")
    assert set(r.keys()) == {"gi", "cos_phi_base", "Vn_V", "sistema", "fuente"}
    assert isinstance(r["gi"], float)
    assert isinstance(r["cos_phi_base"], float)
    assert isinstance(r["Vn_V"], int)
    assert isinstance(r["sistema"], str)
    assert isinstance(r["fuente"], str)


def test_sugerir_parametros_por_perfil_invalido_controlado():
    with pytest.raises(ValueError):
        sugerir_parametros_por_perfil("MINERO_NO_DEFINIDO")
