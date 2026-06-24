# ============================================================
# red_desde_cadena.py
# Responsabilidad: traducir la cadena de coordinación (árbol
# upstream/nivel + Icc por nodo) a un grafo Red de flujo_nodal.
# Normativa: IEC 60909 (Z desde Icc) / IEEE 399 (flujo de carga)
# ============================================================

from __future__ import annotations

import math

from flujo_nodal import Bus, Rama, Red

SLACK_ID = "TRAFO"
C_MAX = 1.05            # IEC 60909
COS_PHI_DEFAULT = 0.9   # para Q de las cargas


def _z_acumulada(icc_kA: float, vn_v: float) -> float:
    """Z acumulada (magnitud, Ω) hasta una barra desde su Icc trifásica."""
    icc_a = float(icc_kA) * 1000.0
    return (C_MAX * vn_v) / (math.sqrt(3.0) * icc_a)


def _potencia_circuito_kW(c: dict) -> float:
    """P del circuito en kW: usa p_kw si existe; si no, √3·V·I·cosφ (3F) o V·I·cosφ (1F)."""
    if c.get("p_kw") is not None:
        return float(c["p_kw"])
    sistema = str(c.get("sistema", "3F")).upper()
    v = 380.0 if sistema == "3F" else 220.0
    f = math.sqrt(3.0) if sistema == "3F" else 1.0
    i = float(c.get("I_diseno") or 0.0)
    cosphi = float(c.get("cos_phi") or COS_PHI_DEFAULT)
    return f * v * i * cosphi / 1000.0


def _carga_total_kW(circuitos: list) -> float:
    return sum(_potencia_circuito_kW(c) for c in (circuitos or []))


def construir_red(
    cadena: list,
    trafo_z_ohm: float,
    circuitos: list,
    *,
    xr: float = 0.1,
    vn_v: float = 380.0,
    s_base_kVA: float = 1000.0,
) -> Red:
    """Construye un Red de flujo_nodal desde la cadena de coordinación.

    Topología: un bus por dispositivo; rama de upstream→dispositivo;
    nivel 0 cuelga del slack TRAFO.
    Impedancia de rama: derivada de la escalera de Icc (ver _z_acumulada),
    repartida R+jX con relación X/R = xr.
    Cargas: agregadas en nodos hoja por peso de In_A; total = Σ P de circuitos.
    """
    buses: list[Bus] = [Bus(id=SLACK_ID, tipo="slack")]
    ramas: list[Rama] = []

    # 1) Z acumulada por nodo (desde Icc); nodos sin Icc se excluyen.
    z_acum: dict[str, float] = {SLACK_ID: float(trafo_z_ohm)}
    nodos_validos: list[dict] = []
    excluidos: list[str] = []
    for d in cadena:
        nombre = str(d.get("nombre") or "").strip()
        if not nombre:
            continue
        icc = d.get("Icc_kA")
        if icc is None or float(icc) <= 0:
            excluidos.append(nombre)
            continue
        z_acum[nombre] = _z_acumulada(float(icc), vn_v)
        nodos_validos.append(d)

    # 2) Buses + ramas (rama = Z_acum(nodo) − Z_acum(padre), repartida R/X).
    for d in nodos_validos:
        nombre = str(d["nombre"]).strip()
        padre = str(d.get("upstream") or "").strip() or SLACK_ID
        if padre not in z_acum:
            padre = SLACK_ID  # padre excluido/ausente → cuelga del slack
        buses.append(Bus(id=nombre, tipo="PQ"))
        z_mag = z_acum[nombre] - z_acum.get(padre, 0.0)
        if z_mag <= 0:
            z_mag = 1e-6  # dato sospechoso (Icc hijo ≥ padre)
        r = z_mag / math.sqrt(1.0 + xr * xr)
        x = r * xr
        ramas.append(Rama(from_bus=padre, to_bus=nombre, R_ohm=r, X_ohm=x))

    # 3) Cargas: agregadas en nodos hoja, repartidas por peso de In_A.
    hijos = {r.from_bus for r in ramas}
    hojas = [d for d in nodos_validos if str(d["nombre"]).strip() not in hijos]
    suma_in = sum(float(d.get("In_A") or 0.0) for d in hojas)
    p_total = _carga_total_kW(circuitos)
    tan_phi = math.tan(math.acos(COS_PHI_DEFAULT))
    bus_por_id = {b.id: b for b in buses}
    if suma_in > 0 and p_total > 0:
        for d in hojas:
            nombre = str(d["nombre"]).strip()
            peso = float(d.get("In_A") or 0.0) / suma_in
            p_hoja = p_total * peso
            bus = bus_por_id[nombre]
            bus.P_kW = -p_hoja
            bus.Q_kVAR = -p_hoja * tan_phi

    red = Red(buses=buses, ramas=ramas, S_base_kVA=s_base_kVA, V_base_kV=vn_v / 1000.0)
    red.nodos_excluidos = excluidos  # type: ignore[attr-defined]
    return red
