"""Indexado normativo local con ChromaDB + embeddings."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .chunker import chunk_normativo, detectar_tipo_norma
from .extractor import extraer_documento

MODELO_EMBEDDINGS = "sentence-transformers/all-MiniLM-L6-v2"

COLECCIONES = {
    "ric_nacional": ["ric"],
    "nch_electrica": ["nch"],
    "sec_resoluciones": ["sec", "nseg"],
    "iec_sintetica": ["iec_ref"],
}

_EXT_OMITIR = {".dwg", ".jpg", ".jpeg", ".png", ".xls", ".xlsx", ".pptx"}


def _tipo_to_coleccion(tipo: str) -> str:
    for nombre, tipos in COLECCIONES.items():
        if tipo in tipos:
            return nombre
    return "sec_resoluciones"


class _HashEmbeddingModel:
    """Fallback deterministico cuando sentence-transformers no esta disponible."""

    def __init__(self, dims: int = 384) -> None:
        self.dims = dims

    def _encode_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dims
        palabras = (text or "").lower().split()
        if not palabras:
            return vec
        for palabra in palabras:
            h = int(hashlib.sha256(palabra.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dims
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self._encode_one(t) for t in texts]


def _build_embedding_model(modelo_embeddings: str = MODELO_EMBEDDINGS):
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(modelo_embeddings)
    except Exception as e:
        print(f"[rag_normativa] Advertencia embeddings fallback hash: {e}")
        return _HashEmbeddingModel()


def _embed(model, textos: list[str]) -> list[list[float]]:
    if hasattr(model, "encode"):
        vals = model.encode(textos)
        if hasattr(vals, "tolist"):
            return vals.tolist()
        return [list(v) for v in vals]
    raise ValueError("Modelo de embeddings invalido")


class _SimpleCollection:
    def __init__(self, base_path: Path, name: str) -> None:
        self.base_path = base_path
        self.name = name
        self.path = base_path / f"{name}.json"
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")

    def add(self, ids, documents, metadatas, embeddings):
        existing = set(self._data["ids"])
        for i, did in enumerate(ids):
            if did in existing:
                continue
            self._data["ids"].append(did)
            self._data["documents"].append(documents[i])
            self._data["metadatas"].append(metadatas[i])
            self._data["embeddings"].append(embeddings[i])
        self._save()

    def count(self):
        return len(self._data["ids"])

    def get(self, include=None):
        include = include or []
        out = {"ids": list(self._data["ids"])}
        if "metadatas" in include:
            out["metadatas"] = list(self._data["metadatas"])
        if "documents" in include:
            out["documents"] = list(self._data["documents"])
        return out

    def query(self, query_embeddings, n_results=3, include=None):
        include = include or []
        q = query_embeddings[0]
        sims: list[tuple[int, float]] = []
        for idx, emb in enumerate(self._data["embeddings"]):
            dot = sum((a * b) for a, b in zip(q, emb))
            sims.append((idx, dot))
        sims.sort(key=lambda t: t[1], reverse=True)
        top = sims[:n_results]
        ids = [[self._data["ids"][i] for i, _ in top]]
        docs = [[self._data["documents"][i] for i, _ in top]]
        mets = [[self._data["metadatas"][i] for i, _ in top]]
        dists = [[max(0.0, 1.0 - sim) for _, sim in top]]
        out = {"ids": ids}
        if "documents" in include:
            out["documents"] = docs
        if "metadatas" in include:
            out["metadatas"] = mets
        if "distances" in include:
            out["distances"] = dists
        return out


class _SimpleChromaClient:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def get_or_create_collection(self, name: str):
        return _SimpleCollection(self.path, name)


def inicializar_db(ruta_db: str):
    """
    Crea cliente ChromaDB persistente en ruta_db.
    Si no hay chromadb, usa backend JSON local.
    """
    path = str(Path(ruta_db))
    try:
        import chromadb

        return chromadb.PersistentClient(path=path)
    except Exception as e:
        print(f"[rag_normativa] Advertencia Chroma fallback JSON: {e}")
        return _SimpleChromaClient(path=path)


def _make_chunk_id(ruta: str, chunk: dict) -> str:
    key = f"{Path(ruta).name}|{chunk.get('articulo')}|{chunk.get('titulo')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def indexar_documento(
    ruta: str,
    norma: str,
    cliente_chroma,
    modelo_embeddings,
) -> dict:
    """
    Pipeline completo para un documento.
    """
    t0 = time.time()
    texto = extraer_documento(ruta)
    tipo = detectar_tipo_norma(norma or Path(ruta).name)
    chunks = chunk_normativo(texto, norma=tipo if tipo else "sec")
    if not chunks:
        return {
            "norma": norma,
            "chunks_indexados": 0,
            "chunks_fallidos": 0,
            "tiempo_seg": round(time.time() - t0, 3),
        }

    collection_name = _tipo_to_coleccion(tipo)
    col = cliente_chroma.get_or_create_collection(collection_name)

    ids = [_make_chunk_id(ruta, c) for c in chunks]
    documentos = [c["texto"] for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {
            "norma": str(c.get("norma") or norma),
            "articulo": str(c.get("articulo") or ""),
            "titulo": str(c.get("titulo") or ""),
            "tipo": str(c.get("tipo") or tipo),
            "fuente": str(Path(ruta).name),
            "fecha_indexado": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        metadatas.append(meta)

    embeddings = _embed(modelo_embeddings, documentos)
    before = col.count() if hasattr(col, "count") else 0
    col.add(ids=ids, documents=documentos, metadatas=metadatas, embeddings=embeddings)
    after = col.count() if hasattr(col, "count") else before + len(ids)
    indexados = max(0, after - before)
    fallidos = max(0, len(chunks) - indexados)
    return {
        "norma": norma,
        "chunks_indexados": indexados,
        "chunks_fallidos": fallidos,
        "tiempo_seg": round(time.time() - t0, 3),
    }


def indexar_corpus(ruta_corpus: str, ruta_db: str) -> dict:
    """
    Indexa todos los documentos de corpus/.
    """
    t0 = time.time()
    cliente = inicializar_db(ruta_db)
    modelo = _build_embedding_model(MODELO_EMBEDDINGS)

    base = Path(ruta_corpus)
    if not base.exists():
        return {
            "total_docs": 0,
            "total_chunks": 0,
            "docs_fallidos": 0,
            "tiempo_total_seg": round(time.time() - t0, 3),
        }

    docs = 0
    chunks = 0
    fallidos = 0
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in _EXT_OMITIR:
            continue
        if p.suffix.lower() not in {".pdf", ".docx", ".doc", ".md"}:
            continue
        docs += 1
        try:
            norma = p.stem
            res = indexar_documento(str(p), norma, cliente, modelo)
            chunks += int(res.get("chunks_indexados", 0))
        except Exception:
            fallidos += 1
    return {
        "total_docs": docs,
        "total_chunks": chunks,
        "docs_fallidos": fallidos,
        "tiempo_total_seg": round(time.time() - t0, 3),
    }


def estado_indice(ruta_db: str) -> dict:
    """
    Estado actual del indice por coleccion.
    """
    cliente = inicializar_db(ruta_db)
    estado: dict[str, dict[str, Any]] = {}
    for col_name in COLECCIONES:
        col = cliente.get_or_create_collection(col_name)
        data = col.get(include=["metadatas"]) if hasattr(col, "get") else {"metadatas": []}
        metas = data.get("metadatas") or []
        estado[col_name] = {
            "docs_indexados": len({m.get("fuente") for m in metas if isinstance(m, dict)}),
            "chunks_total": col.count() if hasattr(col, "count") else len(metas),
            "ultimo_indexado": metas[-1].get("fecha_indexado") if metas else None,
        }
    return estado
