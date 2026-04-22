import uuid
from pathlib import Path

from rag_normativa import indexador
from rag_normativa.indexador import estado_indice, indexar_corpus, indexar_documento, inicializar_db


def _tmp_dir() -> Path:
    base = Path(__file__).resolve().parent / ".tmp_rag_indexador"
    base.mkdir(parents=True, exist_ok=True)
    d = base / uuid.uuid4().hex
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_indexar_md_sintetico(monkeypatch):
    monkeypatch.setattr(indexador, "_build_embedding_model", lambda *_: indexador._HashEmbeddingModel())
    base = _tmp_dir()
    ruta_db = base / "db"
    ruta_md = base / "RIC-N10.md"
    ruta_md.write_text(
        "Articulo N°10 Caida de tension\nDeltaV <= 5%\nArticulo N°11 Conductores\nSeccion minima",
        encoding="utf-8",
    )
    cliente = inicializar_db(str(ruta_db))
    modelo = indexador._build_embedding_model()
    out = indexar_documento(str(ruta_md), "RIC-N10", cliente, modelo)
    assert out["chunks_indexados"] >= 1


def test_estado_indice_retorna_dict(monkeypatch):
    monkeypatch.setattr(indexador, "_build_embedding_model", lambda *_: indexador._HashEmbeddingModel())
    base = _tmp_dir()
    ruta_db = base / "db"
    ruta_md = base / "IEC_62040.md"
    ruta_md.write_text("## UPS\nAutonomia minima 15 min", encoding="utf-8")
    cliente = inicializar_db(str(ruta_db))
    indexar_documento(str(ruta_md), "IEC_62040", cliente, indexador._build_embedding_model())
    est = estado_indice(str(ruta_db))
    assert isinstance(est, dict)
    assert "iec_sintetica" in est


def test_indexar_omite_extensiones_no_texto(monkeypatch):
    monkeypatch.setattr(indexador, "_build_embedding_model", lambda *_: indexador._HashEmbeddingModel())
    base = _tmp_dir()
    corpus = base / "corpus"
    (corpus / "ric").mkdir(parents=True)
    (corpus / "ric" / "plano.dwg").write_bytes(b"dwg")
    (corpus / "ric" / "foto.jpg").write_bytes(b"jpg")
    (corpus / "ric" / "norma.md").write_text("Articulo N°1 Texto", encoding="utf-8")
    out = indexar_corpus(str(corpus), str(base / "db"))
    assert out["total_docs"] == 1
    assert out["docs_fallidos"] == 0


def test_indexar_dos_veces_no_duplica(monkeypatch):
    monkeypatch.setattr(indexador, "_build_embedding_model", lambda *_: indexador._HashEmbeddingModel())
    base = _tmp_dir()
    ruta_db = base / "db"
    ruta_md = base / "NCH_4_2003.md"
    ruta_md.write_text("12.28 Caida de tension\nTexto", encoding="utf-8")
    cliente = inicializar_db(str(ruta_db))
    modelo = indexador._build_embedding_model()
    indexar_documento(str(ruta_md), "NCH_4_2003", cliente, modelo)
    indexar_documento(str(ruta_md), "NCH_4_2003", cliente, modelo)
    est = estado_indice(str(ruta_db))
    assert est["nch_electrica"]["chunks_total"] == 1
