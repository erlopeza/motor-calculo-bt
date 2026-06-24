# ============================================================
# red_desde_cadena.py
# Responsabilidad: traducir la cadena de coordinación (árbol por
# 'upstream' + Icc por nodo) a un grafo Red de flujo_nodal.
# Normativa: IEC 60909 (Z desde Icc) / IEEE 399 (flujo de carga)
# ============================================================

from __future__ import annotations

import math

from flujo_nodal import Bus, Rama, Red

SLACK_ID = "TRAFO"
C_MAX = 1.05            # IEC 60909
COS_PHI_DEFAULT = 0.9   # cos φ por defecto cuando el circuito no lo trae


def _z_acumulada(icc_kA: float, vn_v: float) -> float:
    """Z acumulada (magnitud, Ω) hasta una barra desde su Icc trifásica."""
    icc_a = float(icc_kA) * 1000.0
    return (C_MAX * vn_v) / (math.sqrt(3.0) * icc_a)


def _potencia_circuito_kW(c: dict) -> float:
    """P del circuito en kW: usa p_kw si existe; si no, √3·V·I·cosφ (3F) o V·I·cosφ (1F).

    Si faltan I_diseno y p_kw, retorna 0.0 (el circuito no aporta carga).
    """
    if c.get("p_kw") is not None:
        return float(c["p_kw"])
    sistema = str(c.get("sistema", "3F")).upper()
    v = 380.0 if sistema == "3F" else 220.0
    f = math.sqrt(3.0) if sistema == "3F" else 1.0
    i = float(c.get("I_diseno") or 0.0)
    cosphi = float(c.get("cos_phi") or COS_PHI_DEFAULT)
    return f * v * i * cosphi / 1000.0


def _reactiva_circuito_kVAR(c: dict) -> float:
    """Q del circuito en kVAR usando su propio cos φ (no el default global)."""
    p = _potencia_circuito_kW(c)
    cosphi = float(c.get("cos_phi") or COS_PHI_DEFAULT)
    cosphi = min(max(cosphi, 0.1), 1.0)  # clamp defensivo
    return p * math.tan(math.acos(cosphi))


def _carga_total_PQ(circuitos: list) -> tuple[float, float]:
    """(P_total kW, Q_total kVAR) del conjunto de circuitos.

    Q se acumula con el cos φ real de cada circuito (no un valor único),
    para no subestimar la potencia reactiva en el flujo de carga.
    """
    items = circuitos or []
    p = sum(_potencia_circuito_kW(c) for c in items)
    q = sum(_reactiva_circuito_kVAR(c) for c in items)
    return p, q


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

    Topología: un bus por dispositivo; la rama va de su 'upstream' (padre)
    a su bus; los dispositivos sin upstream cuelgan del slack TRAFO. El campo
    'nivel' es informativo y NO se consume (la jerarquía se deriva de upstream).

    Impedancia de rama: derivada de la escalera de Icc (ver _z_acumulada),
    Z_rama = Z_acum(nodo) − Z_acum(padre), repartida R+jX con X/R = xr.

    Cargas: P y Q totales de `circuitos` agregadas en nodos hoja (sin hijos),
    repartidas por peso de In_A. Nodos intermedios solo transmiten.

    Nodos sin Icc se excluyen; sus hijos con Icc válida se re-enraízan al
    TRAFO (conservan su Z_acum correcta). La lista de excluidos se adjunta
    como atributo dinámico `red.nodos_excluidos` (leer con getattr; no es un
    campo del dataclass Red de flujo_nodal).

    Lanza ValueError si hay nombres de dispositivo duplicados en la cadena.
    """
    buses: list[Bus] = [Bus(id=SLACK_ID, tipo="slack")]
    ramas: list[Rama] = []

    # 1) Z acumulada por nodo (desde Icc); nodos sin Icc se excluyen.
    z_acum: dict[str, float] = {SLACK_ID: float(trafo_z_ohm)}
    nodos_validos: list[dict] = []
    excluidos: list[str] = []
    vistos: set[str] = set()
    for d in cadena:
        nombre = str(d.get("nombre") or "").strip()
        if not nombre:
            continue
        if nombre in vistos:
            raise ValueError(f"Nombre de dispositivo duplicado en la cadena: {nombre!r}")
        vistos.add(nombre)
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
        if padre == nombre or padre not in z_acum:
            # auto-referencia o padre excluido/ausente → cuelga del slack
            padre = SLACK_ID
        buses.append(Bus(id=nombre, tipo="PQ"))
        z_mag = z_acum[nombre] - z_acum[padre]
        if z_mag <= 0:
            z_mag = 1e-6  # dato sospechoso (Icc hijo ≥ padre)
        r = z_mag / math.sqrt(1.0 + xr * xr)
        x = r * xr
        ramas.append(Rama(from_bus=padre, to_bus=nombre, R_ohm=r, X_ohm=x))

    # 3) Cargas: agregadas en nodos hoja, repartidas por peso de In_A.
    con_hijos = {r.from_bus for r in ramas if r.from_bus != SLACK_ID}
    hojas = [d for d in nodos_validos if str(d["nombre"]).strip() not in con_hijos]
    suma_in = sum(float(d.get("In_A") or 0.0) for d in hojas)
    p_total, q_total = _carga_total_PQ(circuitos)
    bus_por_id = {b.id: b for b in buses}
    if suma_in > 0 and p_total > 0:
        for d in hojas:
            nombre = str(d["nombre"]).strip()
            peso = float(d.get("In_A") or 0.0) / suma_in
            bus = bus_por_id[nombre]
            bus.P_kW = -p_total * peso
            bus.Q_kVAR = -q_total * peso

    red = Red(buses=buses, ramas=ramas, S_base_kVA=s_base_kVA, V_base_kV=vn_v / 1000.0)
    red.nodos_excluidos = excluidos  # type: ignore[attr-defined]
    return red
