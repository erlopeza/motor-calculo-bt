from gui_core.sesion import SesionProyecto
from gui_core.estado import Estado
from gui_core.fases import FASES, MODULOS, modulos_de_fase, estado_modulo, estado_fase, buscar_modulo


def test_siete_fases():
    assert set(FASES.keys()) == {0, 1, 2, 3, 4, 5, 6}

def test_cada_modulo_tiene_fase_valida():
    for m in MODULOS:
        assert m.fase in FASES
        assert m.nombre and m.norma is not None

def test_modulo_arc_flash_en_fase_3():
    af = buscar_modulo("arc_flash")
    assert af is not None and af.fase == 3

def test_estado_sin_datos_cuando_faltan_prereqs():
    s = SesionProyecto()
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.SIN_DATOS

def test_estado_listo_cuando_prereqs_ok_sin_resultado():
    s = SesionProyecto(circuitos=[{"nombre": "C1"}])
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.LISTO

def test_estado_calculado_y_alerta():
    s = SesionProyecto(circuitos=[{"nombre": "C1"}])
    s.registrar("dv", {"filas": []}, alertas=[])
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.CALCULADO
    s.registrar("dv", {"filas": []}, alertas=["C1"])
    assert estado_modulo(buscar_modulo("dv"), s) == Estado.ALERTA

def test_estado_fase_es_el_peor_de_sus_modulos():
    s = SesionProyecto(circuitos=[{"nombre": "C1"}])
    s.registrar("dv", {}, alertas=["C1"])
    assert estado_fase(1, s) == Estado.ALERTA

def test_modulos_de_fase_no_vacio():
    for n in FASES:
        assert isinstance(modulos_de_fase(n), list)
    assert len(modulos_de_fase(3)) >= 3
