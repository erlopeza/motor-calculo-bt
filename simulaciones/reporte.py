"""Generador TXT de informe de divergencias."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "sin_commit"


def _resumen(resultados: list[dict]) -> dict:
    r = {
        "total": len(resultados),
        "sin_div": 0,
        "SUPUESTO_CONSERVADOR": 0,
        "EQUIPO_DISTINTO": 0,
        "VARIABLE_IGNORADA": 0,
        "ERROR_MOTOR": 0,
        "PENDIENTE": 0,
    }
    for x in resultados:
        if abs(float(x.get("divergencia_pct") or 0.0)) < 5.0:
            r["sin_div"] += 1
        cat = x.get("categoria", "PENDIENTE")
        r[cat] = r.get(cat, 0) + 1
    return r


def _bloque(resultado: dict) -> str:
    sid = resultado["id"]
    desc = resultado["descripcion"]
    rm = resultado.get("resultado_motor")
    rs = resultado.get("resultado_simaris")
    d = float(resultado.get("divergencia_pct") or 0.0)
    signo = "MAYOR" if d >= 0 else "MENOR"
    cat = resultado.get("categoria")
    metrica = resultado.get("metrica", "")
    detalle = resultado.get("detalle_motor", {})

    lines = []
    lines.append("-" * 60)
    lines.append(f"{sid} - {desc}")
    lines.append("-" * 60)
    if sid == "S04":
        lines.append(f"  Motor BT @ 20C : {detalle.get('dv_t20_pct')}%")
        lines.append(f"  Motor BT @ 60C : {detalle.get('dv_t60_pct')}%")
    else:
        lines.append(f"  Motor BT   : {rm} ({metrica})")
    lines.append(f"  SIMARIS    : {rs}")
    lines.append(f"  Divergencia: {round(d, 3)}% [{signo} que SIMARIS]")
    lines.append(f"  Categoria  : {cat}")
    lines.append("  Justificacion:")
    lines.append(f"    {resultado.get('justificacion')}")
    nota = (resultado.get("nota_tecnica") or "").strip()
    if nota:
        lines.append("  Nota tecnica:")
        lines.append(f"    {nota}")
    lines.append(f"  Accion     : {resultado.get('accion')}")
    lines.append(f"  Variable   : {resultado.get('variable_analisis')}")
    return "\n".join(lines)


def generar_reporte_divergencias(
    resultados: list[dict],
    nombre_proyecto: str = "ENERQUIMICA / LEO-ARICA",
    ruta_salida: str = None
) -> str:
    """
    Genera reporte TXT completo. Si ruta_salida es None retorna string.
    """
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit = _git_commit()
    r = _resumen(resultados)

    lines = []
    lines.append("=" * 60)
    lines.append("  ANALISIS DE DIVERGENCIAS - Motor BT vs SIMARIS")
    lines.append("  Referencia: ENERQUIMICA Rev02 / SIMARIS Design Advanced 25.1.1")
    lines.append(f"  Proyecto: {nombre_proyecto}")
    lines.append(f"  Fecha: {fecha}")
    lines.append(f"  Motor BT commit: {commit}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("RESUMEN")
    lines.append(f"  Escenarios analizados : {r['total']}")
    lines.append(f"  Sin divergencia (<5%) : {r['sin_div']}")
    lines.append(f"  Supuesto conservador  : {r['SUPUESTO_CONSERVADOR']}")
    lines.append(f"  Equipo distinto       : {r['EQUIPO_DISTINTO']}")
    lines.append(f"  Variable ignorada     : {r['VARIABLE_IGNORADA']}")
    lines.append(f"  Error Motor BT        : {r['ERROR_MOTOR']}")
    lines.append(f"  Pendiente analisis    : {r['PENDIENTE']}")
    lines.append("")

    for x in resultados:
        lines.append(_bloque(x))
        lines.append("")

    lines.append("=" * 60)
    lines.append("  FIN DEL REPORTE")
    lines.append("=" * 60)
    content = "\n".join(lines)

    if ruta_salida:
        path = Path(ruta_salida)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)
    return content
