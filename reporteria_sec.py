"""Generacion de reporteria SEC desde resultados ya calculados."""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from persistencia import inicializar_db, obtener_circuitos, obtener_ejecuciones


def _sanitize(value) -> str:
    if value is None:
        return "NA"
    return str(value).strip().replace(" ", "_")


def _marca_archivo() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


def _asegurar_carpeta(ruta_salida: str) -> Path:
    carpeta = Path(ruta_salida).resolve()
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def _ruta_memoria(datos_run: dict, ruta_salida: str) -> Path:
    carpeta = _asegurar_carpeta(ruta_salida)
    nombre = (
        f"MEMORIA_{_sanitize(datos_run.get('project_id'))}_"
        f"{_sanitize(datos_run.get('revision'))}_{_marca_archivo()}.docx"
    )
    return carpeta / nombre


def _ruta_reporte(datos_run: dict, ruta_salida: str) -> Path:
    carpeta = _asegurar_carpeta(ruta_salida)
    nombre = (
        f"REPORTE_{_sanitize(datos_run.get('project_id'))}_"
        f"{_sanitize(datos_run.get('revision'))}_{_marca_archivo()}.pdf"
    )
    return carpeta / nombre


def generar_memoria_docx(
    datos_run: dict,
    circuitos: list,
    ruta_salida: str
) -> str:
    ruta_docx = _ruta_memoria(datos_run, ruta_salida)

    doc = Document()
    doc.add_heading("Memoria Explicativa - Motor BT", level=0)

    doc.add_heading("Portada", level=1)
    doc.add_paragraph(f"Proyecto: {datos_run.get('project_id')}")
    doc.add_paragraph(f"Revision: {datos_run.get('revision')}")
    doc.add_paragraph(f"Fecha: {datos_run.get('timestamp')}")
    doc.add_paragraph(f"Norma: {datos_run.get('norma')}")
    doc.add_paragraph(f"Perfil: {datos_run.get('perfil')}")

    doc.add_heading("Antecedentes", level=1)
    doc.add_paragraph("Sistema de referencia: 380V / 3F / 50Hz")
    doc.add_paragraph(f"Norma aplicada: {datos_run.get('norma')}")

    doc.add_heading("Cuadro de cargas", level=1)
    tabla_cargas = doc.add_table(rows=1, cols=4)
    tabla_cargas.rows[0].cells[0].text = "Circuito"
    tabla_cargas.rows[0].cells[1].text = "Conductor"
    tabla_cargas.rows[0].cells[2].text = "I_diseno (A)"
    tabla_cargas.rows[0].cells[3].text = "Potencia estimada (W)"
    for c in circuitos:
        row = tabla_cargas.add_row().cells
        row[0].text = str(c.get("nombre", ""))
        row[1].text = str(c.get("conductor", ""))
        i_dis = c.get("I_diseno") or 0
        cos_phi = c.get("cos_phi") or 0
        potencia = round(float(i_dis) * 380.0 * float(cos_phi), 2)
        row[2].text = str(i_dis)
        row[3].text = str(potencia)

    doc.add_heading("Calculo DeltaV", level=1)
    tabla_dv = doc.add_table(rows=1, cols=6)
    tabla_dv.rows[0].cells[0].text = "Circuito"
    tabla_dv.rows[0].cells[1].text = "L_m"
    tabla_dv.rows[0].cells[2].text = "S_mm2"
    tabla_dv.rows[0].cells[3].text = "dv_v"
    tabla_dv.rows[0].cells[4].text = "dv_pct"
    tabla_dv.rows[0].cells[5].text = "estado"
    for c in circuitos:
        row = tabla_dv.add_row().cells
        row[0].text = str(c.get("nombre", ""))
        row[1].text = str(c.get("L_m", ""))
        row[2].text = str(c.get("S_mm2", ""))
        row[3].text = str(c.get("dv_v", ""))
        row[4].text = str(c.get("dv_pct", ""))
        row[5].text = str(c.get("estado", ""))

    doc.add_heading("Calculo Icc", level=1)
    tabla_icc = doc.add_table(rows=1, cols=4)
    tabla_icc.rows[0].cells[0].text = "Circuito"
    tabla_icc.rows[0].cells[1].text = "icc_ka"
    tabla_icc.rows[0].cells[2].text = "I_max"
    tabla_icc.rows[0].cells[3].text = "estado proteccion"
    for c in circuitos:
        row = tabla_icc.add_row().cells
        row[0].text = str(c.get("nombre", ""))
        row[1].text = str(c.get("icc_ka", ""))
        row[2].text = str(c.get("I_max", ""))
        row[3].text = str(c.get("estado", ""))

    doc.add_heading("Conclusion", level=1)
    doc.add_paragraph(f"n_ok: {datos_run.get('n_ok')}")
    doc.add_paragraph(f"n_fallas: {datos_run.get('n_fallas')}")
    doc.add_paragraph(f"max_dv_pct: {datos_run.get('max_dv_pct')}")
    doc.add_paragraph(f"max_icc_ka: {datos_run.get('max_icc_ka')}")
    doc.add_paragraph(f"status: {datos_run.get('status')}")

    doc.save(str(ruta_docx))
    return str(ruta_docx)


def generar_reporte_pdf(
    datos_run: dict,
    circuitos: list,
    ruta_salida: str
) -> str:
    ruta_pdf = _ruta_reporte(datos_run, ruta_salida)

    c = canvas.Canvas(str(ruta_pdf), pagesize=A4)
    w, h = A4

    y = h - 2 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "Reporte Cliente - Motor BT")

    y -= 1 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Proyecto: {datos_run.get('project_id')} | Revision: {datos_run.get('revision')}")
    y -= 0.6 * cm
    c.drawString(2 * cm, y, f"Fecha: {datos_run.get('timestamp')}")

    y -= 1.0 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Cuadro de cargas resumido")

    y -= 0.7 * cm
    c.setFont("Helvetica", 9)
    c.drawString(2 * cm, y, "Circuito")
    c.drawString(8 * cm, y, "Conductor")
    c.drawString(12 * cm, y, "dv_pct")
    c.drawString(15 * cm, y, "Estado")

    y -= 0.3 * cm
    c.line(2 * cm, y, 19 * cm, y)

    for circuito in circuitos:
        y -= 0.5 * cm
        if y < 2 * cm:
            c.showPage()
            y = h - 2 * cm
            c.setFont("Helvetica", 9)
        c.drawString(2 * cm, y, str(circuito.get("nombre", ""))[:35])
        c.drawString(8 * cm, y, str(circuito.get("conductor", ""))[:20])
        c.drawString(12 * cm, y, str(circuito.get("dv_pct", ""))[:10])
        c.drawString(15 * cm, y, str(circuito.get("estado", ""))[:20])

    y -= 1 * cm
    if y < 3 * cm:
        c.showPage()
        y = h - 2 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Conclusion")
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Status final: {datos_run.get('status')}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Circuitos OK: {datos_run.get('n_ok')} | Fallas: {datos_run.get('n_fallas')}")

    c.save()
    return str(ruta_pdf)


def _registrar_ruta_reporte(run_id: str, report_type: str, file_path: str, ruta_db: str) -> None:
    try:
        inicializar_db(ruta_db)
        with sqlite3.connect(ruta_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                INSERT INTO run_reports (report_id, run_id, report_type, file_path)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(run_id, report_type)
                DO UPDATE SET file_path=excluded.file_path
                """,
                (str(uuid.uuid4()), run_id, report_type, file_path),
            )
            conn.commit()
    except Exception:
        print("[reporteria_sec] No se pudo registrar ruta en run_reports")


def generar_desde_run_id(
    run_id: str,
    ruta_db: str = "motor_bt.db"
) -> Tuple[str, str]:
    try:
        runs = obtener_ejecuciones(ruta_db=ruta_db)
        datos_run = next((r for r in runs if r.get("run_id") == run_id), None)
        if not datos_run:
            return ("", "")

        circuitos = obtener_circuitos(run_id=run_id, ruta_db=ruta_db)
        if not circuitos:
            return ("", "")

        ruta_base = os.getcwd()
        ruta_docx = generar_memoria_docx(datos_run, circuitos, ruta_base)
        ruta_pdf = generar_reporte_pdf(datos_run, circuitos, ruta_base)

        _registrar_ruta_reporte(run_id, "DOCX", ruta_docx, ruta_db)
        _registrar_ruta_reporte(run_id, "PDF", ruta_pdf, ruta_db)
        return (ruta_docx, ruta_pdf)
    except Exception as e:
        print(f"[reporteria_sec] Error regenerando reportes: {e}")
        return ("", "")
