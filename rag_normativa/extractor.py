"""Extraccion de texto para corpus normativo."""

from __future__ import annotations

from pathlib import Path

import pdfplumber
from docx import Document


def _limpiar_linea_pdf(linea: str) -> str:
    s = (linea or "").strip()
    if not s:
        return ""
    s_norm = s.lower().replace(" ", "")
    if s_norm.isdigit():
        return ""
    if s_norm.startswith("pagina") and any(ch.isdigit() for ch in s_norm):
        return ""
    if s_norm.startswith("page") and any(ch.isdigit() for ch in s_norm):
        return ""
    return s


def extraer_pdf(ruta: str) -> str:
    """
    Extrae texto de PDF usando pdfplumber.
    Retorna texto limpio — sin headers de pagina, sin numeros de pagina sueltos.
    Si el PDF esta escaneado (texto vacio) retorna "" y loguea advertencia.
    """
    textos: list[str] = []
    with pdfplumber.open(ruta) as pdf:
        for page in pdf.pages:
            raw = page.extract_text() or ""
            lineas = [_limpiar_linea_pdf(l) for l in raw.splitlines()]
            limpio = "\n".join([l for l in lineas if l])
            if limpio:
                textos.append(limpio)
    full = "\n\n".join(textos).strip()
    if not full:
        print(f"[rag_normativa] Advertencia: PDF sin texto extraible (escaneado?): {ruta}")
    return full


def extraer_docx(ruta: str) -> str:
    """
    Extrae texto de Word usando python-docx.
    Preserva estructura de parrafos con saltos de linea.
    """
    doc = Document(ruta)
    parrafos = [(p.text or "").strip() for p in doc.paragraphs]
    return "\n".join([p for p in parrafos if p]).strip()


def extraer_documento(ruta: str) -> str:
    """
    Router por extension.
    Soporta: .pdf, .docx, .doc, .md
    """
    path = Path(ruta)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extraer_pdf(str(path))
    if ext in {".docx", ".doc"}:
        return extraer_docx(str(path))
    if ext == ".md":
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    raise ValueError(f"Extension no soportada: {ext}. Soportadas: .pdf, .docx, .doc, .md")

