"""Generador TXT unificado de protocolo commissioning P1-P4."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "sin_commit"


def _lineas_p1(p1: dict) -> list[str]:
    out = []
    out.append("-" * 60)
    out.append("P1 - CONTINUIDAD DE CONDUCTORES")
    out.append(f"Norma: {p1.get('norma')}")
    out.append(f"Instrumento: {p1.get('instrumento')}")
    out.append("-" * 60)
    out.append("  Circuito               Conductor       L(m)   R_max(ohm)  R_medida  Estado")
    for m in p1.get("mediciones", []):
        out.append(
            f"  {str(m.get('circuito'))[:20]:<20} "
            f"{str(m.get('conductor'))[:14]:<14} "
            f"{float(m.get('longitud_m') or 0):>5.1f}   "
            f"{float(m.get('R_max_ohm') or 0):>9.6f}   _______   ______"
        )
    return out


def _lineas_p2(p2: dict) -> list[str]:
    out = []
    out.append("-" * 60)
    out.append("P2 - PRUEBA DE MOTORES")
    out.append(f"Norma: {p2.get('norma')}")
    out.append(f"Instrumento: {p2.get('instrumento')}")
    out.append("-" * 60)
    for pr in p2.get("pruebas", []):
        out.append(f"  Motor: {pr.get('motor')}")
        out.append(f"  I_nominal calculada : {pr.get('I_nominal_A')} A")
        out.append(
            f"  I_arranque esperada : {pr.get('I_arranque_esperada_A')} A +-10% "
            f"-> [{pr.get('I_arranque_min_A')} - {pr.get('I_arranque_max_A')}] A"
        )
        out.append(f"  DeltaV arranque max : {pr.get('dV_arranque_max_pct')}%")
        out.append(f"  t_arranque max      : {pr.get('t_arranque_max_s')} s")
        out.append("  PASOS:")
        out.append("  1. Verificar tension en bornes: ______ V  Estado: ______")
        out.append("  2. Medir I_arranque pico: ______ A  Estado: ______")
        out.append("  3. Medir DeltaV arranque: ______ %  Estado: ______")
        out.append("  4. Medir I operacion: ______ A  Estado: ______")
        out.append("")
    return out


def _lineas_p3(p3: dict) -> list[str]:
    out = []
    out.append("-" * 60)
    out.append("P3 - PRUEBA DE TRANSFERENCIA ATS/STS")
    out.append(f"Norma: {p3.get('norma')}")
    out.append(f"Instrumento: {p3.get('instrumento')}")
    out.append("-" * 60)
    out.append(f"  Equipo: {p3.get('equipo')} - Modo: {str(p3.get('modo')).upper()}")
    vals = p3.get("valores_esperados", {})
    out.append(
        f"  t_total esperado: {vals.get('t_total_ms_esperado')} ms +-"
        f"{vals.get('t_total_ms_tolerancia_pct')}%"
    )
    out.append(f"  V_GE esperado: {vals.get('V_GE_esperado_V')} V (+/-5%)")
    out.append("  f_GE esperado: 50 +/-0.5 Hz")
    out.append("")
    for paso in p3.get("pasos", []):
        out.append(f"  {paso.get('paso')}. {paso.get('accion')}")
        out.append(f"     Criterio: {paso.get('criterio')}")
        out.append("     Medicion: _______  Estado: ______")
    return out


def _lineas_p4(p4: dict) -> list[str]:
    out = []
    out.append("-" * 60)
    out.append("P4 - VERIFICACION Icc EN PUNTO")
    out.append(f"Norma: {p4.get('norma')}")
    out.append(f"Instrumento: {p4.get('instrumento')}")
    out.append("-" * 60)
    out.append("  Punto                    Icc_calc  Rango+-10%        Z_esp(ohm)  Z_medida  Estado")
    for p in p4.get("puntos", []):
        out.append(
            f"  {str(p.get('punto'))[:24]:<24} "
            f"{float(p.get('Icc_calculado_kA') or 0):>7.3f}   "
            f"[{float(p.get('Icc_min_aceptable_kA') or 0):.3f}-{float(p.get('Icc_max_aceptable_kA') or 0):.3f}]   "
            f"{float(p.get('Z_lazo_esperado_ohm') or 0):>9.6f}   _______  ______"
        )
    return out


def generar_protocolo_completo(
    resultado_p1: dict,
    resultado_p2: dict,
    resultado_p3: dict,
    resultado_p4: dict,
    nombre_proyecto: str,
    ejecutante: str,
    ruta_salida: str = None
) -> str:
    """
    Genera protocolo TXT unificado P1-P4.
    """
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit = _git_commit()
    lines = []
    lines.append("=" * 60)
    lines.append("  PROTOCOLO DE COMMISSIONING - P1 a P4")
    lines.append(f"  Proyecto : {nombre_proyecto}")
    lines.append(f"  Ejecutante: {ejecutante}")
    lines.append(f"  Fecha    : {fecha}")
    lines.append(f"  Motor BT commit: {commit}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("INSTRUCCIONES GENERALES")
    lines.append("  - Medicion con instrumento calibrado")
    lines.append("  - Registrar fecha/hora y tecnico por prueba")
    lines.append("  - Adjuntar evidencia fotografica")
    lines.append("  - Si no aprueba: detener y notificar al ingeniero")
    lines.append("")
    lines.extend(_lineas_p1(resultado_p1 or {}))
    lines.append("")
    lines.extend(_lineas_p2(resultado_p2 or {}))
    lines.append("")
    lines.extend(_lineas_p3(resultado_p3 or {}))
    lines.append("")
    lines.extend(_lineas_p4(resultado_p4 or {}))
    lines.append("")
    lines.append("=" * 60)
    lines.append("  FIRMA TECNICO: _________________  FECHA: __________")
    lines.append("  FIRMA INGENIERO: _______________  FECHA: __________")
    lines.append("=" * 60)
    content = "\n".join(lines)

    if ruta_salida:
        p = Path(ruta_salida)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return str(p)
    return content

