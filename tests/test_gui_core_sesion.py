from gui_core.sesion import SesionProyecto


def test_sesion_vacia_flags_false():
    s = SesionProyecto()
    assert s.tiene_circuitos is False
    assert s.tiene_trafo is False
    assert s.tiene_cadena is False
    assert s.tiene_protecciones is False

def test_cargar_setea_flags():
    s = SesionProyecto()
    s.cargar({
        "circuitos": [{"nombre": "C1"}],
        "trafo": {"modo": "A", "kVA": 1000},
        "protecciones": {"C1": {"In_A": 100, "curva": "C"}},
        "cadena": [{"nombre": "G0"}],
        "proyecto": "P", "perfil": "industrial",
    })
    assert s.tiene_circuitos and s.tiene_trafo
    assert s.tiene_protecciones and s.tiene_cadena
    assert s.proyecto == "P" and s.perfil == "industrial"

def test_cargar_ignora_claves_desconocidas():
    s = SesionProyecto()
    s.cargar({"basura": 123, "circuitos": [{"nombre": "C1"}]})
    assert s.tiene_circuitos
    assert not hasattr(s, "basura")

def test_registrar_resultado():
    s = SesionProyecto()
    s.registrar("dv", {"filas": [1, 2]}, alertas=["C1"])
    assert s.resultados["dv"]["alertas"] == ["C1"]
    assert s.resultados["dv"]["resultado"] == {"filas": [1, 2]}
