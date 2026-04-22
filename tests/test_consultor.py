import uuid
from pathlib import Path

from rag_normativa import consultor, indexador
from rag_normativa.consultor import consultar, consultar_criterio_calculo
from rag_normativa.indexador import indexar_documento, inicializar_db


def _tmp_dir() -> Path:
    base = Path(__file__).resolve().parent / ".tmp_rag_consultor"
    base.mkdir(parents=True, exist_ok=True)
    d = base / uuid.uuid4().hex
    d.mkdir(parents=True, exist_ok=True)
    return d


def _preparar_indice(monkeypatch):
    monkeypatch.setattr(indexador, "_build_embedding_model", lambda *_: indexador._HashEmbeddingModel())
    monkeypatch.setattr(consultor, "_build_embedding_model", lambda *_: indexador._HashEmbeddingModel())
    base = _tmp_dir()
    ruta_db = base / "db"
    ruta_md = base / "RIC-N10.md"
    ruta_md.write_text(
        "Articulo N°10 Caida de tension\n"
        "Limite de caida de tension instalacion BT es 5%\n"
        "Articulo N°11 Conductores\n"
        "Seccion minima conductor cobre 2.5 mm2",
        encoding="utf-8",
    )
    cliente = inicializar_db(str(ruta_db))
    indexar_documento(str(ruta_md), "RIC-N10", cliente, indexador._HashEmbeddingModel())
    return ruta_db


def test_consultar_retorna_dict_esperado(monkeypatch):
    ruta_db = _preparar_indice(monkeypatch)
    out = consultar("limite caida de tension instalacion BT", str(ruta_db), n_resultados=3, umbral_confianza=0.0)
    assert isinstance(out, dict)
    assert {"ok", "respuesta", "cita", "norma", "confianza", "alternativas"} <= set(out.keys())


def test_consultar_con_confianza_baja_retorna_ok_false(monkeypatch):
    ruta_db = _preparar_indice(monkeypatch)
    out = consultar("pregunta irrelevante xyz", str(ruta_db), umbral_confianza=1.1)
    assert out["ok"] is False


def test_consultar_criterio_limite_dv(monkeypatch):
    def _fake_consultar(pregunta, ruta_db, **kwargs):
        return {"ok": True, "respuesta": pregunta, "cita": "RIC N°10 Art. 10", "norma": "RIC", "confianza": 0.9, "alternativas": []}

    monkeypatch.setattr(consultor, "consultar", _fake_consultar)
    out = consultar_criterio_calculo("calculos", "limite_dv")
    assert out["ok"] is True
    assert "caida de tension" in out["respuesta"]


def test_consultar_criterio_autonomia_ups(monkeypatch):
    def _fake_consultar(pregunta, ruta_db, **kwargs):
        return {"ok": True, "respuesta": pregunta, "cita": "TIA-942 Art. 7.4", "norma": "TIA", "confianza": 0.9, "alternativas": []}

    monkeypatch.setattr(consultor, "consultar", _fake_consultar)
    out = consultar_criterio_calculo("ups", "autonomia_minima")
    assert out["ok"] is True
    assert "autonomia minima" in out["respuesta"]


def test_consultar_criterio_icc_formula(monkeypatch):
    def _fake_consultar(pregunta, ruta_db, **kwargs):
        return {"ok": True, "respuesta": pregunta, "cita": "IEC 60909 §4.7.1", "norma": "IEC", "confianza": 0.95, "alternativas": []}

    monkeypatch.setattr(consultor, "consultar", _fake_consultar)
    out = consultar_criterio_calculo("generador", "icc_formula")
    assert out["ok"] is True
    assert "cortocircuito generador" in out["respuesta"]
