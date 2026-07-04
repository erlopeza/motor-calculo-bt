from gui_core.estado import COLORES, Estado, color_de_estado


def test_paleta_tokyo_night_hexes():
    assert COLORES["fondo"] == "#1a1b26"
    assert COLORES["acento"] == "#7aa2f7"
    assert COLORES["ok"] == "#9ece6a"
    assert COLORES["alerta"] == "#f7768e"
    assert COLORES["precaucion"] == "#ff9e64"

def test_estados_existen():
    assert {e.value for e in Estado} == {"sin_datos", "listo", "calculado", "alerta"}

def test_color_de_estado():
    assert color_de_estado(Estado.CALCULADO) == COLORES["ok"]
    assert color_de_estado(Estado.ALERTA) == COLORES["alerta"]
    assert color_de_estado(Estado.LISTO) == COLORES["acento"]
    assert color_de_estado(Estado.SIN_DATOS) == COLORES["texto_tenue"]
