"""Analisis de divergencias Motor BT vs SIMARIS."""

from .analizador import (
    analizar_todos,
    calcular_divergencia,
    calcular_resultado_motor,
    categorizar,
)
from .escenarios import CATEGORIAS, ESCENARIOS
from .reporte import generar_reporte_divergencias

__all__ = [
    "CATEGORIAS",
    "ESCENARIOS",
    "analizar_todos",
    "calcular_divergencia",
    "calcular_resultado_motor",
    "categorizar",
    "generar_reporte_divergencias",
]

