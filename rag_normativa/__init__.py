"""RAG normativa para Motor BT."""

from .consultor import consultar, consultar_criterio_calculo
from .indexador import (
    COLECCIONES,
    MODELO_EMBEDDINGS,
    estado_indice,
    indexar_corpus,
    indexar_documento,
    inicializar_db,
)
from .referencias_iec import generar_referencias_iec, listar_referencias

__all__ = [
    "COLECCIONES",
    "MODELO_EMBEDDINGS",
    "consultar",
    "consultar_criterio_calculo",
    "estado_indice",
    "indexar_corpus",
    "indexar_documento",
    "inicializar_db",
    "generar_referencias_iec",
    "listar_referencias",
]
