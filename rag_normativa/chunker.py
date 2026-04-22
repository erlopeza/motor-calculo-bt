"""Chunking normativo orientado a articulos/secciones."""

from __future__ import annotations

import re
from pathlib import Path

PATRON_RIC = r"(Art[íi]culo\s+N[°o]?\s*\d+[\w\.\-]*)"
PATRON_NCH = r"(\d+\.\d+(?:\.\d+)*\s+[A-ZÁÉÍÓÚÑ][^\n]{5,})"
PATRON_NSEG = r"((?:Art\.|Artículo)\s*\d+[°\.]?\s*[-—]?\s*[A-ZÁÉÍÓÚÑ])"

_PATRONES = {
    "ric": PATRON_RIC,
    "nch": PATRON_NCH,
    "nseg": PATRON_NSEG,
    "sec": PATRON_NSEG,
    "iec_ref": r"(^##\s+[^\n]+)",
}


def _token_count(texto: str) -> int:
    return len((texto or "").split())


def _normalizar_norma(norma: str) -> str:
    if not norma:
        return "sec"
    s = norma.strip().lower()
    if s in {"ric", "nch", "nseg", "sec", "iec_ref"}:
        return s
    return detectar_tipo_norma(s)


def detectar_tipo_norma(nombre_archivo: str) -> str:
    """
    Infiere tipo desde nombre de archivo.
    """
    s = Path(nombre_archivo).name.lower()
    if s.endswith(".md") and ("iec" in s or "tia" in s):
        return "iec_ref"
    if s.startswith("ric") or "ric-" in s:
        return "ric"
    if s.startswith("nch"):
        return "nch"
    if s.startswith("nseg"):
        return "nseg"
    if s.startswith(("ds", "re", "res")):
        return "sec"
    return "sec"


def _chunks_fallback(texto: str, tipo: str, norma: str) -> list[dict]:
    words = texto.split()
    if not words:
        return []
    out: list[dict] = []
    size = 800
    overlap = 100
    step = max(1, size - overlap)
    for i in range(0, len(words), step):
        fragment = " ".join(words[i:i + size]).strip()
        if not fragment:
            continue
        titulo = fragment.splitlines()[0][:120]
        out.append(
            {
                "texto": fragment,
                "norma": norma,
                "articulo": f"chunk-{len(out) + 1}",
                "titulo": titulo,
                "tipo": tipo,
                "longitud_tokens": _token_count(fragment),
            }
        )
        if i + size >= len(words):
            break
    return out


def _split_por_patron(texto: str, patron: str) -> list[tuple[str, str]]:
    regex = re.compile(patron, flags=re.MULTILINE)
    matches = list(regex.finditer(texto))
    if not matches:
        return []
    partes: list[tuple[str, str]] = []
    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(texto)
        head = m.group(0).strip()
        body = texto[start:end].strip()
        partes.append((head, body))
    return partes


def _normalizar_articulo(header: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)*)", header or "")
    if m:
        return m.group(1)
    return (header or "").strip()[:40] or "s/n"


def chunk_normativo(texto: str, norma: str) -> list[dict]:
    """
    Divide texto en chunks por articulo/seccion.
    Si no detecta estructura normativa, usa fallback de 800 tokens.
    """
    contenido = (texto or "").strip()
    if not contenido:
        return []

    tipo = _normalizar_norma(norma)
    patron = _PATRONES.get(tipo)
    if not patron:
        return _chunks_fallback(contenido, tipo, norma)

    partes = _split_por_patron(contenido, patron)
    if not partes:
        return _chunks_fallback(contenido, tipo, norma)

    chunks: list[dict] = []
    for header, body in partes:
        titulo = (body.splitlines()[0] if body else header).strip()[:150]
        chunks.append(
            {
                "texto": body,
                "norma": norma,
                "articulo": _normalizar_articulo(header),
                "titulo": titulo,
                "tipo": tipo,
                "longitud_tokens": _token_count(body),
            }
        )
    return chunks
