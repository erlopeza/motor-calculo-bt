import os
import uuid
from pathlib import Path

from graficos import generar_todos
from parser_reporte import parsear_reporte


FIXTURE_TXT = """
============================================================
  REPORTE — LEO-ARICA-M12
  Fecha        : 19/04/2026 19:44
============================================================

============================================================
  TRANSFORMADOR — DATOS Y CORTOCIRCUITO EN BORNES BT
============================================================
  Potencia nominal: 1000.0 kVA
  Icc nominal BT  : 30.39 kA
  Icc máxima      : 36.14 kA
  Icc mínima      : 26.85 kA
============================================================

============================================================
  CIRCUITOS — CAÍDA DE TENSIÓN, Icc Y PROTECCIONES
============================================================
  Circuito  : CRAC Unit 1-A
  Corriente : 63.0A -> OK (cap. 65.0A)
  Caida dV  : 1.436V (0.378%) -> ÓPTIMO
  Icc punto : 10.77 kA  -> ALTO

  Circuito  : Iluminacion HUB
  Corriente : 16.0A -> OK (cap. 24.0A)
  Caida dV  : 13.535V (6.152%) -> FALLA
  Icc punto : 0.26 kA  -> MUY BAJO
============================================================

============================================================
  BALANCE DE CARGA POR TABLERO
============================================================
  Tablero   : MDP
  Fases     : L1=259.77kW  L2=262.52kW  L3=261.09kW
  Desequilib: 1.1% -> EQUILIBRADO
  Uso trafo     : 87.7% -> PRECAUCIÓN
============================================================

============================================================
  DEMANDA MÁXIMA Y DIMENSIONAMIENTO — M6
============================================================
  CRAC Unit 1-A             hvac            1.00   35.24kW   35.24kW
  Iluminacion HUB           iluminacion     1.00    3.52kW    3.52kW
  Demanda total      : 876.7 kVA (783.382 kW)
  Factor crecimiento : ×1.25
  Demanda futura     : 1095.88 kVA
============================================================

============================================================
  COORDINACIÓN TCC — MODO RED
  Icc en punto de falla: 4490.0 A
============================================================
  G0A_3WA1600                   0      0.300 s tiempo_corto
  G1A_3VA630                    1            — verificar_simaris
  C1A_3VA160                    2      0.020 s instantaneo
============================================================
  SELECTIVIDAD GLOBAL : INDETERMINADA
============================================================

============================================================
  MOTORES — CORRIENTE, ARRANQUE Y PROTECCIONES
============================================================
  Motor     : Bomba Principal
  Potencia  : 45.0 kW
  I_plena   : 82.5 A
  I_arranque: 495.0 A
============================================================

============================================================
  STS - TRANSFERENCIA ESTATICA
============================================================
  STS           : STS-LEO-01 (ABB)
  P_carga total : 180.0kVA
  Uso           : 72.0% -> OK
  Uso falla BUS : 95.0% en STS sobreviviente -> REVISAR
  t_transfer    : 120.0 ms
============================================================

============================================================
  UPS - SISTEMA DE ALIMENTACION ININTERRUMPIDA
============================================================
  UPS           : UPS-LEO-01 (Vertiv)
  P nominal     : 250.0kVA | V: 380.0V
  P carga       : 220.0kW (97.778%) -> REVISAR
  Energia total : 81.6kWh
  P en baterias : 234.043kW (eta_ups=0.94)
  Autonomia     : 20.919 min -> OK
  Minimo normado: 15 min (TIA-942)
============================================================

============================================================
  Circuitos OK    : 9
  Circuitos FALLA : 1
  Protecciones OK : 10
  Uso transf.     : 87.7% -> PRECAUCIÓN
============================================================
""".strip()


def _tmp_dir() -> Path:
    base = Path(__file__).resolve().parent / ".tmp_parser_reporte"
    base.mkdir(parents=True, exist_ok=True)
    d = base / uuid.uuid4().hex
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_txt(content: str) -> Path:
    d = _tmp_dir()
    p = d / "REPORTE_TEST.txt"
    p.write_text(content, encoding="utf-8")
    return p


def test_parser_extrae_proyecto_y_fecha():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    assert reporte["proyecto"] == "LEO-ARICA-M12"
    assert reporte["fecha"] == "19/04/2026 19:44"


def test_parser_extrae_circuitos_con_dv():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    assert len(reporte["circuitos"]) >= 2
    assert reporte["circuitos"][0]["dv_pct"] == 0.378


def test_parser_circuito_falla_tiene_estado_falla():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    falla = next(c for c in reporte["circuitos"] if c["id"] == "Iluminacion HUB")
    assert "FALLA" in (falla["estado"] or "")


def test_parser_extrae_balance_3_fases():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    bal = reporte["balance"]
    assert bal["L1_kW"] == 259.77
    assert bal["L2_kW"] == 262.52
    assert bal["L3_kW"] == 261.09


def test_parser_extrae_ups_autonomia():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    ups = reporte["ups"]
    assert ups["E_bat_kWh"] == 81.6
    assert ups["t_autonomia_min"] == 20.919


def test_parser_extrae_sts_transferencia():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    sts = reporte["sts"]
    assert sts["t_transfer_ms"] == 120.0
    assert sts["uso_pct"] == 72.0


def test_parser_extrae_motor_corrientes():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    motor = reporte["motor"]
    assert motor["I_plena_A"] == 82.5
    assert motor["I_arranque_A"] == 495.0


def test_parser_extrae_transformador_icc():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    trafo = reporte["transformador"]
    assert trafo["P_kVA"] == 1000.0
    assert trafo["icc_nominal_kA"] == 30.39


def test_parser_extrae_tcc_dispositivos():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    tcc = reporte["tcc"]
    assert tcc["modo"] == "RED"
    assert tcc["icc_falla_A"] == 4490.0
    assert len(tcc["dispositivos"]) == 3


def test_parser_seccion_ausente_retorna_none():
    txt = FIXTURE_TXT.replace("UPS - SISTEMA DE ALIMENTACION ININTERRUMPIDA", "UPS REMOVIDO")
    reporte = parsear_reporte(str(_write_txt(txt)))
    assert reporte["ups"] is None


def test_parser_reporte_sin_sts_retorna_none_sts():
    txt = FIXTURE_TXT.replace("STS - TRANSFERENCIA ESTATICA", "STS REMOVIDO")
    reporte = parsear_reporte(str(_write_txt(txt)))
    assert reporte["sts"] is None


def test_parser_nunca_lanza_excepcion_con_txt_vacio():
    p = _write_txt("")
    reporte = parsear_reporte(str(p))
    assert isinstance(reporte, dict)
    assert isinstance(reporte["errores"], list)


def test_generar_todos_desde_parser_genera_png():
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    out = _tmp_dir()
    generados = generar_todos(reporte, str(out), prefijo="TST_")
    assert len(generados) > 0
    assert "dv_circuitos" in generados
    assert os.path.exists(generados["dv_circuitos"])


def test_generar_todos_omite_graficos_sin_datos():
    reporte = {
        "circuitos": None,
        "balance": None,
        "ups": None,
        "sts": None,
        "tcc": None,
    }
    out = _tmp_dir()
    generados = generar_todos(reporte, str(out))
    assert generados == {}


def test_contrato_parser_campos_criticos():
    """
    Valida contrato critico para graficos sobre salida de parser.
    """
    reporte = parsear_reporte(str(_write_txt(FIXTURE_TXT)))
    campos_criticos = {
        "circuitos": reporte.get("circuitos"),
        "balance_fases": reporte.get("balance"),
        "ups": reporte.get("ups"),
        "ats": reporte.get("sts"),
        "protecciones": (reporte.get("tcc") or {}).get("dispositivos"),
    }
    faltantes = [k for k, v in campos_criticos.items() if not v]
    assert not faltantes, f"Parser sin campos criticos para graficos: {faltantes}"


def test_parser_acumula_error_si_seccion_falta():
    """
    Si el TXT carece de estructura util, el parser debe dejar diagnostico en errores.
    """
    reporte = parsear_reporte(str(_write_txt("")))
    assert len(reporte.get("errores", [])) > 0


def test_parser_alerta_si_campos_criticos_vacios():
    """
    Si no hay campos criticos, el parser debe devolver advertencia de formato.
    """
    reporte = parsear_reporte(str(_write_txt("")))
    assert "TXT vacío" in " ".join(reporte.get("errores", []))
