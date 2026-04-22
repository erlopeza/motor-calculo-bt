from rag_normativa.chunker import chunk_normativo, detectar_tipo_norma


def test_chunk_ric_detecta_articulos():
    texto = (
        "Articulo N°10 Alcance\n"
        "Contenido A\n"
        "Articulo N°11 Requisitos\n"
        "Contenido B"
    )
    chunks = chunk_normativo(texto, "ric")
    assert len(chunks) >= 2
    assert chunks[0]["tipo"] == "ric"


def test_chunk_nch_detecta_secciones():
    texto = (
        "12.28 Caida de tension en BT\n"
        "Texto 1\n"
        "12.29 Seccion minima de conductores\n"
        "Texto 2"
    )
    chunks = chunk_normativo(texto, "nch")
    assert len(chunks) >= 2
    assert chunks[0]["tipo"] == "nch"


def test_chunk_fallback_sin_estructura():
    texto = " ".join(["texto"] * 1600)
    chunks = chunk_normativo(texto, "sec")
    assert len(chunks) >= 2
    assert chunks[0]["articulo"].startswith("chunk-")


def test_detectar_tipo_norma_ric():
    assert detectar_tipo_norma("RIC-N10_2025.pdf") == "ric"


def test_detectar_tipo_norma_nch():
    assert detectar_tipo_norma("NCH_4_2003.pdf") == "nch"


def test_detectar_tipo_norma_iec_ref():
    assert detectar_tipo_norma("IEC_60909.md") == "iec_ref"


def test_metadata_chunk_completa():
    texto = "Articulo N°1 Titulo\nTexto de articulo"
    chunk = chunk_normativo(texto, "ric")[0]
    assert {"texto", "norma", "articulo", "titulo", "tipo", "longitud_tokens"} <= set(chunk.keys())

