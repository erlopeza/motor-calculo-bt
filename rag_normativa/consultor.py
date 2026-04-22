"""Consultas de normativa sobre indice vectorial local."""

from __future__ import annotations

from pathlib import Path

from .indexador import (
    COLECCIONES,
    MODELO_EMBEDDINGS,
    _build_embedding_model,
    _embed,
    inicializar_db,
)

_MAPEO_PREGUNTAS = {
    ("calculos", "limite_dv"): "limite caida de tension instalacion BT",
    ("conductores", "seccion_minima"): "seccion minima conductor cobre",
    ("transformador", "ukr"): "tension cortocircuito transformador tolerancia",
    ("motores", "dv_arranque"): "caida tension arranque motor",
    ("ups", "autonomia_minima"): "autonomia minima UPS datacenter",
    ("generador", "icc_formula"): "formula corriente cortocircuito generador IEC 60909",
}


def _confidence_from_distance(distance: float) -> float:
    try:
        d = float(distance)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, 1.0 - d))


def _format_cita(meta: dict) -> str:
    norma = meta.get("norma") or meta.get("tipo") or "Norma"
    art = meta.get("articulo") or "s/n"
    if "art" in str(art).lower():
        return f"{norma} {art}"
    return f"{norma} Art. {art}"


def consultar(
    pregunta: str,
    ruta_db: str,
    colecciones: list[str] = None,
    n_resultados: int = 3,
    umbral_confianza: float = 0.5,
) -> dict:
    """
    Consulta semantica con filtro por umbral de confianza.
    """
    try:
        cliente = inicializar_db(ruta_db)
        modelo = _build_embedding_model(MODELO_EMBEDDINGS)
        q_emb = _embed(modelo, [pregunta])[0]
    except Exception as e:
        return {
            "ok": False,
            "respuesta": "",
            "cita": "",
            "norma": "",
            "confianza": 0.0,
            "alternativas": [],
            "error": f"fallo_preparacion: {e}",
        }

    cols = colecciones or list(COLECCIONES.keys())
    candidatos = []
    for col_name in cols:
        try:
            col = cliente.get_or_create_collection(col_name)
            q = col.query(
                query_embeddings=[q_emb],
                n_results=max(1, n_resultados),
                include=["documents", "metadatas", "distances"],
            )
            docs = (q.get("documents") or [[]])[0]
            metas = (q.get("metadatas") or [[]])[0]
            dists = (q.get("distances") or [[]])[0]
            for doc, meta, dist in zip(docs, metas, dists):
                conf = _confidence_from_distance(dist)
                candidatos.append(
                    {
                        "doc": doc,
                        "meta": meta or {},
                        "dist": dist,
                        "conf": conf,
                        "col": col_name,
                    }
                )
        except Exception:
            continue

    if not candidatos:
        return {
            "ok": False,
            "respuesta": "",
            "cita": "",
            "norma": "",
            "confianza": 0.0,
            "alternativas": [],
        }

    candidatos.sort(key=lambda x: x["conf"], reverse=True)
    top = candidatos[0]
    if top["conf"] < umbral_confianza:
        return {
            "ok": False,
            "respuesta": "",
            "cita": _format_cita(top["meta"]),
            "norma": str(top["meta"].get("norma") or top["meta"].get("tipo") or ""),
            "confianza": round(top["conf"], 4),
            "alternativas": [],
        }

    alternativas = []
    for c in candidatos[1:n_resultados]:
        alternativas.append(
            {
                "cita": _format_cita(c["meta"]),
                "confianza": round(c["conf"], 4),
                "resumen": str(c["doc"] or "")[:180],
            }
        )

    return {
        "ok": True,
        "respuesta": str(top["doc"] or ""),
        "cita": _format_cita(top["meta"]),
        "norma": str(top["meta"].get("norma") or top["meta"].get("tipo") or ""),
        "confianza": round(top["conf"], 4),
        "alternativas": alternativas,
    }


def consultar_criterio_calculo(
    modulo: str,
    parametro: str,
) -> dict:
    """
    Traduce criterio tecnico a consulta normativa.
    """
    pregunta = _MAPEO_PREGUNTAS.get((str(modulo).lower(), str(parametro).lower()))
    if not pregunta:
        pregunta = f"criterio normativo para {modulo} {parametro}"
    ruta_default = str((Path(__file__).resolve().parent / "db").resolve())
    return consultar(pregunta=pregunta, ruta_db=ruta_default)

