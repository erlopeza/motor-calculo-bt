import os
import re
from typing import Any


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_float(text: str) -> float | None:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return _to_float(match.group(0))


def _extract_in_a_from_name(nombre: str) -> float | None:
    match = re.search(r"(\d+)$", str(nombre or "").strip())
    if not match:
        return None
    return _to_float(match.group(1))


def parsear_reporte(ruta_txt: str) -> dict[str, Any]:
    """
    Lee un REPORTE_*.txt y retorna dict estructurado.
    Si una sección no existe en el TXT -> su clave vale None.
    Nunca lanza excepción; errores de parseo se agregan en dict["errores"].
    """
    data: dict[str, Any] = {
        "proyecto": "",
        "fecha": "",
        "circuitos": [],
        "balance": None,
        "demanda": None,
        "tcc": None,
        "ups": None,
        "sts": None,
        "motor": None,
        "transformador": None,
        "resumen": {
            "circuitos_ok": 0,
            "circuitos_falla": 0,
            "protecciones_ok": 0,
        },
        "errores": [],
    }

    try:
        with open(ruta_txt, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except Exception as exc:
        data["errores"].append(f"No se pudo leer archivo: {exc}")
        return data

    lines = text.splitlines()
    if not lines:
        data["errores"].append("TXT vacío")
        return data

    # Header principal.
    for line in lines:
        if "REPORTE" in line and "—" in line:
            m = re.search(r"REPORTE\s+—\s+(.+)$", line)
            if m:
                data["proyecto"] = m.group(1).strip()
            break
    for line in lines:
        if "Fecha" in line and ":" in line:
            data["fecha"] = line.split(":", 1)[1].strip()
            break

    # Transformador.
    trafo: dict[str, Any] = {}
    for line in lines:
        if "Potencia nominal" in line and "kVA" in line:
            v = _first_float(line)
            if v is not None:
                trafo["P_kVA"] = v
        elif "Icc nominal BT" in line and "kA" in line:
            v = _first_float(line)
            if v is not None:
                trafo["icc_nominal_kA"] = v
        elif "Icc máxima" in line and "kA" in line:
            v = _first_float(line)
            if v is not None:
                trafo["icc_max_kA"] = v
        elif "Icc mínima" in line and "kA" in line:
            v = _first_float(line)
            if v is not None:
                trafo["icc_min_kA"] = v
        elif "Uso transf." in line and "%" in line:
            v = _first_float(line)
            if v is not None:
                trafo["uso_pct"] = v
    if trafo:
        data["transformador"] = trafo

    # Circuitos.
    circuitos: list[dict[str, Any]] = []
    actual: dict[str, Any] | None = None
    for line in lines:
        if re.match(r"^\s*Circuito\s*:", line):
            if actual:
                circuitos.append(actual)
            actual = {
                "id": line.split(":", 1)[1].strip(),
                "dv_pct": None,
                "estado": None,
                "icc_kA": None,
                "I_A": None,
                "cap_A": None,
            }
            continue
        if not actual:
            continue
        if "Corriente" in line and "cap." in line:
            m = re.search(r"Corriente\s*:\s*([-+]?\d+(?:\.\d+)?)A.*\(cap\.\s*([-+]?\d+(?:\.\d+)?)A\)", line)
            if m:
                actual["I_A"] = _to_float(m.group(1))
                actual["cap_A"] = _to_float(m.group(2))
        elif "Caida dV" in line and "->" in line:
            m = re.search(r"\(([-+]?\d+(?:\.\d+)?)%\)\s*->\s*(.+)$", line)
            if m:
                actual["dv_pct"] = _to_float(m.group(1))
                actual["estado"] = m.group(2).strip()
        elif "Icc punto" in line and "kA" in line:
            m = re.search(r"Icc punto\s*:\s*([-+]?\d+(?:\.\d+)?)\s*kA", line)
            if m:
                actual["icc_kA"] = _to_float(m.group(1))
    if actual:
        circuitos.append(actual)
    data["circuitos"] = [c for c in circuitos if c.get("id")]

    # Balance.
    if any("BALANCE DE CARGA" in l for l in lines):
        balance: dict[str, Any] = {
            "tablero": "",
            "L1_kW": None,
            "L2_kW": None,
            "L3_kW": None,
            "desequilibrio_pct": None,
            "uso_pct": None,
        }
        for line in lines:
            if "Tablero" in line and ":" in line:
                balance["tablero"] = line.split(":", 1)[1].strip()
            elif "Fases" in line and "L1=" in line:
                m = re.search(r"L1=([-+]?\d+(?:\.\d+)?)kW\s+L2=([-+]?\d+(?:\.\d+)?)kW\s+L3=([-+]?\d+(?:\.\d+)?)kW", line)
                if m:
                    balance["L1_kW"] = _to_float(m.group(1))
                    balance["L2_kW"] = _to_float(m.group(2))
                    balance["L3_kW"] = _to_float(m.group(3))
            elif "Desequilib" in line and "%" in line:
                balance["desequilibrio_pct"] = _first_float(line)
            elif "Uso trafo" in line and "%" in line:
                balance["uso_pct"] = _first_float(line)
            elif "Uso       :" in line and "%" in line and balance.get("uso_pct") is None:
                balance["uso_pct"] = _first_float(line)
        data["balance"] = balance

    # Demanda.
    if any("DEMANDA" in l for l in lines):
        demanda: dict[str, Any] = {
            "total_kVA": None,
            "total_kW": None,
            "factor_crecimiento": None,
            "futura_kVA": None,
            "circuitos": [],
        }
        for line in lines:
            if "Demanda total" in line and "kVA" in line and "kW" in line:
                m = re.search(r"Demanda total\s*:\s*([-+]?\d+(?:\.\d+)?)\s*kVA\s*\(([-+]?\d+(?:\.\d+)?)\s*kW\)", line)
                if m:
                    demanda["total_kVA"] = _to_float(m.group(1))
                    demanda["total_kW"] = _to_float(m.group(2))
            elif "Factor crecimiento" in line:
                demanda["factor_crecimiento"] = _first_float(line)
            elif "Demanda futura" in line and "kVA" in line:
                demanda["futura_kVA"] = _first_float(line)
            else:
                m = re.search(
                    r"^\s{2}(.+?)\s{2,}([a-zA-Z_]+)\s+([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)kW\s+([-+]?\d+(?:\.\d+)?)kW",
                    line,
                )
                if m:
                    demanda["circuitos"].append(
                        {
                            "nombre": m.group(1).strip(),
                            "tipo": m.group(2).strip(),
                            "Fd": _to_float(m.group(3)),
                            "P_inst_kW": _to_float(m.group(4)),
                            "P_dem_kW": _to_float(m.group(5)),
                        }
                    )
        data["demanda"] = demanda

    # TCC (primer modo encontrado).
    tcc_mode_started = False
    tcc: dict[str, Any] | None = None
    for idx, line in enumerate(lines):
        if "COORDINACI" in line and "MODO" in line:
            if tcc_mode_started:
                break
            tcc_mode_started = True
            tcc = {
                "modo": "",
                "icc_falla_A": None,
                "dispositivos": [],
                "selectividad_global": "",
            }
            m = re.search(r"MODO\s+(.+)$", line)
            if m:
                tcc["modo"] = m.group(1).strip()
            continue
        if not tcc_mode_started or tcc is None:
            continue
        if "Icc en punto de falla" in line and "A" in line:
            tcc["icc_falla_A"] = _first_float(line)
        elif line.strip().startswith("SELECTIVIDAD GLOBAL") and ":" in line:
            tcc["selectividad_global"] = line.split(":", 1)[1].strip()
            break
        else:
            m = re.search(r"^\s{2}([A-Za-z0-9_\-]+)\s+(\d+)\s+([0-9.]+|—)\s*(?:s)?\s+([A-Za-z_]+)", line)
            if m:
                t_disparo = None if m.group(3) == "—" else _to_float(m.group(3))
                nombre = m.group(1).strip()
                tcc["dispositivos"].append(
                    {
                        "nombre": nombre,
                        "nivel": _to_int(m.group(2)),
                        "t_disparo_s": t_disparo,
                        "region": m.group(4).strip(),
                        "In_A": _extract_in_a_from_name(nombre),
                    }
                )
    data["tcc"] = tcc

    # UPS.
    if any("UPS - SISTEMA" in l for l in lines):
        ups: dict[str, Any] = {
            "nombre": "",
            "P_nominal_kVA": None,
            "P_carga_kW": None,
            "E_bat_kWh": None,
            "P_bat_kW": None,
            "t_autonomia_min": None,
            "t_minimo_normado_min": None,
            "uso_pct": None,
        }
        for line in lines:
            if line.strip().startswith("UPS") and ":" in line and "(" in line:
                ups["nombre"] = line.split(":", 1)[1].split("(", 1)[0].strip()
            elif "P nominal" in line and "P carga" in line:
                m = re.search(r"P nominal\s*:\s*([-+]?\d+(?:\.\d+)?)kVA.*P carga\s*:\s*([-+]?\d+(?:\.\d+)?)kW\s*\(([-+]?\d+(?:\.\d+)?)%\)", line)
                if m:
                    ups["P_nominal_kVA"] = _to_float(m.group(1))
                    ups["P_carga_kW"] = _to_float(m.group(2))
                    ups["uso_pct"] = _to_float(m.group(3))
            elif "Energia total" in line and "kWh" in line:
                ups["E_bat_kWh"] = _first_float(line)
            elif "P en baterias" in line and "kW" in line:
                ups["P_bat_kW"] = _first_float(line)
            elif "Autonomia" in line and "min" in line and "Minimo" not in line:
                ups["t_autonomia_min"] = _first_float(line)
            elif "Minimo normado" in line and "min" in line:
                ups["t_minimo_normado_min"] = _first_float(line)
        data["ups"] = ups

    # STS.
    if any("STS - TRANSFERENCIA" in l for l in lines):
        sts: dict[str, Any] = {
            "nombre": "",
            "t_transfer_ms": None,
            "uso_pct": None,
            "uso_falla_pct": None,
            "P_carga_kVA": None,
        }
        for line in lines:
            if line.strip().startswith("STS") and ":" in line and "(" in line:
                sts["nombre"] = line.split(":", 1)[1].split("(", 1)[0].strip()
            elif "P_carga total" in line and "kVA" in line:
                sts["P_carga_kVA"] = _first_float(line)
            elif "t_transfer" in line and "ms" in line:
                sts["t_transfer_ms"] = _first_float(line)
            elif "Uso           :" in line and "%" in line:
                sts["uso_pct"] = _first_float(line)
            elif "Uso falla BUS" in line and "%" in line:
                sts["uso_falla_pct"] = _first_float(line)
        data["sts"] = sts

    # Motor (primero).
    if any("MOTORES" in l for l in lines):
        motor: dict[str, Any] = {
            "nombre": "",
            "I_plena_A": None,
            "I_arranque_A": None,
            "P_kW": None,
        }
        in_motores = False
        for line in lines:
            if "MOTORES" in line:
                in_motores = True
                continue
            if not in_motores:
                continue
            if line.strip().startswith("Motor") and ":" in line:
                motor["nombre"] = line.split(":", 1)[1].strip()
            elif "Potencia" in line and "kW" in line:
                motor["P_kW"] = _first_float(line)
            elif "I_plena" in line and "A" in line:
                motor["I_plena_A"] = _first_float(line)
            elif "I_arranque" in line and "A" in line:
                motor["I_arranque_A"] = _first_float(line)
                break
        data["motor"] = motor

    # Resumen final.
    for line in lines:
        if "Circuitos OK" in line:
            data["resumen"]["circuitos_ok"] = int(_first_float(line) or 0)
        elif "Circuitos FALLA" in line:
            data["resumen"]["circuitos_falla"] = int(_first_float(line) or 0)
        elif "Protecciones OK" in line:
            data["resumen"]["protecciones_ok"] = int(_first_float(line) or 0)

    return data
