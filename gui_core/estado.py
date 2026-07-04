"""Paleta Tokyo Night y estados de módulo para la GUI."""
from __future__ import annotations

from enum import Enum

COLORES = {
    "fondo":        "#1a1b26",
    "panel":        "#16161e",
    "seleccion":    "#292e42",
    "borde":        "#3b4261",
    "texto":        "#c0caf5",
    "texto_tenue":  "#565f89",
    "acento":       "#7aa2f7",
    "ok":           "#9ece6a",
    "alerta":       "#f7768e",
    "precaucion":   "#ff9e64",
    "amarillo":     "#e0af68",
    "violeta":      "#bb9af7",
}


class Estado(Enum):
    SIN_DATOS = "sin_datos"
    LISTO = "listo"
    CALCULADO = "calculado"
    ALERTA = "alerta"


_COLOR = {
    Estado.SIN_DATOS: COLORES["texto_tenue"],
    Estado.LISTO:     COLORES["acento"],
    Estado.CALCULADO: COLORES["ok"],
    Estado.ALERTA:    COLORES["alerta"],
}


def color_de_estado(estado: Estado) -> str:
    return _COLOR[estado]
