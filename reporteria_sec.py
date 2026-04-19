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


def _fecha_formateada(datos_run: dict) -> str:
    raw = datos_run.get("timestamp", "")
    try:
        return datetime.fromisoformat(str(raw)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(raw) or "Sin fecha"


def _norma_display(datos_run: dict) -> str:
    return (
        "RIC N°04 / IEC 60228 — Conductores AWG"
        if datos_run.get("norma") == "AWG"
        else "RIC N°04 / IEC 60228 — Conductores MM2"
    )


def _potencia_activa(circuito: dict) -> float:
    i_dis = circuito.get("I_diseno") or 0
    cos_phi = circuito.get("cos_phi") or 0
    return round(float(i_dis) * 380.0 * float(cos_phi), 2)


def _valor_icc(icc) -> float:
    try:
        return float(icc or 0)
    except Exception:
        return 0.0


def _hay_icc_declarado(circuitos: list) -> bool:
    return any(_valor_icc(c.get("icc_ka")) > 0 for c in circuitos)


def _circuitos_en_falla(circuitos: list) -> list:
    en_falla = []
    for c in circuitos:
        estado = str(c.get("estado") or "").upper()
        dv_pct = c.get("dv_pct")
        try:
            dv_val = float(dv_pct)
        except Exception:
            dv_val = 0.0
        if "FALLA" in estado or dv_val > 5.0:
            en_falla.append(str(c.get("nombre") or "SIN_NOMBRE"))
    return en_falla


def generar_memoria_docx(
    datos_run: dict,
    circuitos: list,
    ruta_salida: str
) -> str:
    ruta_docx = _ruta_memoria(datos_run, ruta_salida)
    fecha = _fecha_formateada(datos_run)

    doc = Document()
    titulo = (
        "MEMORIA EXPLICATIVA DE CÁLCULO\n"
        f"Instalación Eléctrica Interior — {datos_run.get('project_id')}\n"
        f"Revisión: {datos_run.get('revision')}"
    )
    doc.add_heading(titulo, level=0)

    doc.add_heading("Portada", level=1)
    doc.add_paragraph(f"Proyecto: {datos_run.get('project_id')}")
    doc.add_paragraph(f"Revision: {datos_run.get('revision')}")
    doc.add_paragraph(f"Fecha: {fecha}")
    doc.add_paragraph(f"Norma: {datos_run.get('norma')}")
    doc.add_paragraph(f"Perfil: {datos_run.get('perfil')}")

    doc.add_heading("Antecedentes", level=1)
    doc.add_paragraph("Sistema de referencia: 380V / 3F / 50Hz")
    doc.add_paragraph(f"Norma aplicada: {_norma_display(datos_run)}")

    transformador = datos_run.get("transformador") or {}
    if transformador:
        doc.add_heading("Transformador", level=1)
        doc.add_paragraph(f"Potencia nominal: {transformador.get('kVA')} kVA")
        doc.add_paragraph(f"Tension BT: {transformador.get('Vn_BT')} V")
        doc.add_paragraph(f"Ucc%: {transformador.get('Ucc_pct')} %")
        doc.add_paragraph(
            "Icc bornes BT: "
            f"nominal={transformador.get('Icc_nom_kA')} kA, "
            f"maxima={transformador.get('Icc_max_kA')} kA, "
            f"minima={transformador.get('Icc_min_kA')} kA"
        )

    doc.add_heading("Cuadro de cargas", level=1)
    tabla_cargas = doc.add_table(rows=1, cols=4)
    tabla_cargas.rows[0].cells[0].text = "Circuito"
    tabla_cargas.rows[0].cells[1].text = "Conductor"
    tabla_cargas.rows[0].cells[2].text = "I_diseno (A)"
    tabla_cargas.rows[0].cells[3].text = "Potencia Activa (W)"
    for c in circuitos:
        row = tabla_cargas.add_row().cells
        row[0].text = str(c.get("nombre", ""))
        row[1].text = str(c.get("conductor", ""))
        row[2].text = str(c.get("I_diseno") or 0)
        row[3].text = str(_potencia_activa(c))

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

    if _hay_icc_declarado(circuitos):
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
    else:
        doc.add_paragraph(
            "Cálculo de cortocircuito: no declarado en este proyecto.\n"
            "Verificar con herramienta SIMARIS si aplica."
        )

    balance_demanda = datos_run.get("balance_demanda") or {}
    if balance_demanda:
        doc.add_heading("Balance y Demanda", level=1)
        balance = balance_demanda.get("balance") or {}
        demanda = balance_demanda.get("demanda") or {}
        if balance:
            doc.add_paragraph(
                "Balance: "
                f"Demanda total={balance.get('S_total_kva')} kVA, "
                f"Uso transformador={balance.get('uso_trafo_pct')}%"
            )
        if demanda:
            doc.add_paragraph(
                "Demanda: "
                f"{demanda.get('S_total_kva')} kVA / {demanda.get('P_total_kw')} kW, "
                f"Factor crecimiento={demanda.get('factor_crecimiento')}, "
                f"Demanda futura={demanda.get('S_futuro_kva')} kVA"
            )

    doc.add_heading("Conclusion", level=1)
    icc_str = (
        f"{datos_run['max_icc_ka']} kA"
        if datos_run.get("max_icc_ka") and datos_run["max_icc_ka"] > 0
        else "No calculado"
    )
    doc.add_paragraph(f"n_ok: {datos_run.get('n_ok')}")
    doc.add_paragraph(f"n_fallas: {datos_run.get('n_fallas')}")
    doc.add_paragraph(f"max_dv_pct: {datos_run.get('max_dv_pct')}")
    doc.add_paragraph(f"max_icc_ka: {icc_str}")
    doc.add_paragraph(f"status: {datos_run.get('status')}")

    n_fallas = int(datos_run.get("n_fallas") or 0)
    if n_fallas > 0:
        doc.add_paragraph(
            f"ATENCIÓN: {n_fallas} circuito(s) presentan caída de tensión superior\n"
            "al límite normativo (ΔV > 5%, RIC N°10).\n"
            "Acción requerida: redimensionar conductor antes de declarar\n"
            "ante SEC."
        )
        en_falla = _circuitos_en_falla(circuitos)
        if en_falla:
            doc.add_paragraph("Circuitos en falla: " + ", ".join(en_falla))

    doc.save(str(ruta_docx))
    return str(ruta_docx)


def generar_reporte_pdf(
    datos_run: dict,
    circuitos: list,
    ruta_salida: str
) -> str:
    ruta_pdf = _ruta_reporte(datos_run, ruta_salida)
    fecha = _fecha_formateada(datos_run)

    c = canvas.Canvas(str(ruta_pdf), pagesize=A4)
    _, h = A4

    y = h - 2 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "MEMORIA EXPLICATIVA DE CÁLCULO")
    y -= 0.7 * cm
    c.drawString(2 * cm, y, f"Instalación Eléctrica Interior — {datos_run.get('project_id')}")
    y -= 0.7 * cm
    c.drawString(2 * cm, y, f"Revisión: {datos_run.get('revision')}")

    y -= 0.8 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Fecha: {fecha}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Norma aplicada: {_norma_display(datos_run)}")

    y -= 1.0 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Cuadro de cargas resumido")

    y -= 0.7 * cm
    c.setFont("Helvetica", 9)
    c.drawString(2 * cm, y, "Circuito")
    c.drawString(7.8 * cm, y, "Conductor")
    c.drawString(11.0 * cm, y, "Potencia Activa (W)")
    c.drawString(15.0 * cm, y, "dv_pct")
    c.drawString(17.0 * cm, y, "Estado")

    y -= 0.3 * cm
    c.line(2 * cm, y, 19 * cm, y)

    for circuito in circuitos:
        y -= 0.5 * cm
        if y < 2 * cm:
            c.showPage()
            y = h - 2 * cm
            c.setFont("Helvetica", 9)
        c.drawString(2 * cm, y, str(circuito.get("nombre", ""))[:28])
        c.drawString(7.8 * cm, y, str(circuito.get("conductor", ""))[:15])
        c.drawString(11.0 * cm, y, str(_potencia_activa(circuito))[:16])
        c.drawString(15.0 * cm, y, str(circuito.get("dv_pct", ""))[:8])
        c.drawString(17.0 * cm, y, str(circuito.get("estado", ""))[:12])

    y -= 1.0 * cm
    if y < 3 * cm:
        c.showPage()
        y = h - 2 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Conclusion")
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)

    icc_str = (
        f"{datos_run['max_icc_ka']} kA"
        if datos_run.get("max_icc_ka") and datos_run["max_icc_ka"] > 0
        else "No calculado"
    )
    c.drawString(2 * cm, y, f"Status final: {datos_run.get('status')}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Circuitos OK: {datos_run.get('n_ok')} | Fallas: {datos_run.get('n_fallas')}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Icc máximo: {icc_str}")

    n_fallas = int(datos_run.get("n_fallas") or 0)
    if n_fallas > 0:
        y -= 0.6 * cm
        c.drawString(2 * cm, y, f"ATENCIÓN: {n_fallas} circuito(s) superan ΔV > 5% (RIC N°10).")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, "Acción requerida: redimensionar conductor antes de declarar ante SEC.")
        en_falla = _circuitos_en_falla(circuitos)
        if en_falla:
            y -= 0.5 * cm
            c.drawString(2 * cm, y, "Circuitos en falla: " + ", ".join(en_falla)[:110])

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
