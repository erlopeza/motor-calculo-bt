# ============================================================
# flujo_nodal.py
# Responsabilidad: flujo de potencia nodal por Newton-Raphson
# Modelo: bus/rama, matriz Y-bus, solver NR denso (numpy)
# Normativa: IEEE Std 399-1997 / IEC 60909
# Razón para cambiar: migrar a scipy.sparse para redes > 500 buses
#
# Convive con el modo simplificado (calculos.py / icc_punto.py).
# Esta es la vía de análisis de red acoplada (F3).
# ============================================================

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


# ============================================================
# MODELO DE DATOS
# ============================================================

@dataclass
class Bus:
    """Nodo de la red eléctrica.

    Convención de signo: inyección positiva = generación / fuente.
    Cargas se ingresan como P_kW < 0, Q_kVAR < 0.
    """
    id: str
    tipo: str           # "slack" | "PQ"  (PV no soportado, ver Red.__init__)
    P_kW: float = 0.0   # potencia activa inyectada (kW)
    Q_kVAR: float = 0.0 # potencia reactiva inyectada (kVAR)
    V_pu: float = 1.0   # tensión inicial (fijada para slack, estimada para PQ)


@dataclass
class Rama:
    """Rama (cable o transformador simplificado) entre dos buses."""
    from_bus: str
    to_bus: str
    R_ohm: float
    X_ohm: float


class Red:
    """Red eléctrica BT: colección de buses y ramas en per-unit.

    S_base_kVA : potencia base (default 1000 kVA = 1 MVA)
    V_base_kV  : tensión base (default 0.38 kV)
    Z_base     : V_base² / S_base = 0.38² / 1.0 = 0.1444 Ω
    """

    def __init__(
        self,
        buses: list[Bus],
        ramas: list[Rama],
        S_base_kVA: float = 1000.0,
        V_base_kV: float = 0.38,
    ):
        slacks = [b for b in buses if b.tipo == "slack"]
        if len(slacks) != 1:
            raise ValueError(f"La red debe tener exactamente 1 bus slack, tiene {len(slacks)}")

        self.buses = list(buses)
        self.ramas = list(ramas)
        self.S_base_kVA = float(S_base_kVA)
        self.V_base_kV = float(V_base_kV)
        self._idx: dict[str, int] = {b.id: i for i, b in enumerate(buses)}

    @property
    def Z_base_ohm(self) -> float:
        """Z_base = V_base_kV² / S_base_MVA (en Ω)."""
        return (self.V_base_kV ** 2) / (self.S_base_kVA / 1000.0)

    @property
    def I_base_A(self) -> float:
        """I_base = S_base / (√3 × V_base)."""
        return (self.S_base_kVA * 1000.0) / (math.sqrt(3) * self.V_base_kV * 1000.0)

    def indice_bus(self, bus_id: str) -> int:
        return self._idx[bus_id]

    def construir_ybus(self) -> np.ndarray:
        """Construye la matriz de admitancias nodales Y-bus (compleja, n×n)."""
        n = len(self.buses)
        Y = np.zeros((n, n), dtype=complex)
        Z_base = self.Z_base_ohm

        for rama in self.ramas:
            i = self._idx[rama.from_bus]
            j = self._idx[rama.to_bus]
            z_pu = complex(rama.R_ohm, rama.X_ohm) / Z_base
            y_pu = 1.0 / z_pu
            Y[i, i] += y_pu
            Y[j, j] += y_pu
            Y[i, j] -= y_pu
            Y[j, i] -= y_pu

        return Y


# ============================================================
# SOLVER NEWTON-RAPHSON
# ============================================================

def calcular_flujo_nodal(
    red: Red,
    max_iter: int = 50,
    tol: float = 1e-6,
) -> dict:
    """Flujo de potencia por Newton-Raphson (formulación polar).

    Referencia: Bergen & Vittal, Power Systems Analysis, Cap. 9
                / Glover, Sarma & Overbye, Cap. 6

    Retorna dict con:
        convergido  : bool
        iteraciones : int
        buses       : {id: {V_pu, delta_deg, V_kV, P_kW, Q_kVAR}}
        perdidas_totales_kW : float
        norma       : str
    """
    n = len(red.buses)
    Y = red.construir_ybus()
    G = Y.real
    B = Y.imag
    S_base_kW = red.S_base_kVA  # 1000 kVA → 1000 kW

    # Índices de buses no-slack (libres para el solver)
    slack_idx = next(i for i, b in enumerate(red.buses) if b.tipo == "slack")
    libre_idx = [i for i in range(n) if i != slack_idx]
    n_libre = len(libre_idx)

    # Potencias programadas en pu
    P_sched = np.array([b.P_kW / S_base_kW for b in red.buses])
    Q_sched = np.array([b.Q_kVAR / S_base_kW for b in red.buses])

    # Estado inicial: V = 1.0 pu, δ = 0 rad
    V = np.array([b.V_pu for b in red.buses], dtype=float)
    delta = np.zeros(n, dtype=float)

    convergio = False
    iteraciones = 0

    for k in range(max_iter):
        # ---- Inyecciones calculadas ----
        theta = delta[:, None] - delta[None, :]  # θ_ij = δ_i - δ_j
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        P_calc = V * np.sum(V * (G * cos_t + B * sin_t), axis=1)
        Q_calc = V * np.sum(V * (G * sin_t - B * cos_t), axis=1)

        # ---- Mismatch (solo buses libres) ----
        dP = (P_sched - P_calc)[libre_idx]
        dQ = (Q_sched - Q_calc)[libre_idx]
        mismatch = np.concatenate([dP, dQ])

        if np.max(np.abs(mismatch)) < tol:
            convergio = True
            break

        # ---- Jacobiano J = [H N; M L] para buses libres ----
        J = np.zeros((2 * n_libre, 2 * n_libre))

        for ii, i in enumerate(libre_idx):
            for jj, j in enumerate(libre_idx):
                t = delta[i] - delta[j]
                if i != j:
                    H = V[i] * V[j] * (-G[i, j] * math.sin(t) + B[i, j] * math.cos(t))
                    N = V[i] * V[j] * ( G[i, j] * math.cos(t) + B[i, j] * math.sin(t))
                    M = V[i] * V[j] * (-G[i, j] * math.cos(t) - B[i, j] * math.sin(t))
                    L = V[i] * V[j] * ( G[i, j] * math.sin(t) - B[i, j] * math.cos(t))
                else:
                    H = -Q_calc[i] - B[i, i] * V[i] ** 2
                    N =  P_calc[i] + G[i, i] * V[i] ** 2
                    M =  P_calc[i] - G[i, i] * V[i] ** 2
                    L =  Q_calc[i] - B[i, i] * V[i] ** 2

                J[ii,          jj         ] = H
                J[ii,          jj + n_libre] = N
                J[ii + n_libre, jj         ] = M
                J[ii + n_libre, jj + n_libre] = L

        # ---- Corrección: J × [Δδ, ΔV/V] = [ΔP, ΔQ] ----
        try:
            dx = np.linalg.solve(J, mismatch)
        except np.linalg.LinAlgError:
            break  # Jacobiano singular → no convergencia

        d_delta = dx[:n_libre]
        d_V_rel = dx[n_libre:]

        for ii, i in enumerate(libre_idx):
            delta[i] += d_delta[ii]
            V[i] *= (1.0 + d_V_rel[ii])

        iteraciones = k + 1

    # ---- Inyecciones finales (incluye slack) ----
    theta = delta[:, None] - delta[None, :]
    P_final = V * np.sum(V * (G * np.cos(theta) + B * np.sin(theta)), axis=1)
    Q_final = V * np.sum(V * (G * np.sin(theta) - B * np.cos(theta)), axis=1)

    # ---- Balance de pérdidas ----
    perdidas_pu = float(np.sum(P_final))   # Σ P_inyectada = pérdidas (suma de gen + cargas)
    perdidas_kW = perdidas_pu * S_base_kW

    # ---- Resultado por bus ----
    buses_res: dict = {}
    for i, bus in enumerate(red.buses):
        buses_res[bus.id] = {
            "V_pu":      round(float(V[i]), 8),
            "delta_deg": round(float(math.degrees(delta[i])), 6),
            "V_kV":      round(float(V[i] * red.V_base_kV), 6),
            "P_kW":      round(float(P_final[i] * S_base_kW), 4),
            "Q_kVAR":    round(float(Q_final[i] * S_base_kW), 4),
        }

    return {
        "convergido":         convergio,
        "iteraciones":        iteraciones,
        "buses":              buses_res,
        "perdidas_totales_kW": round(perdidas_kW, 4),
        "norma":              "Newton-Raphson — IEEE Std 399-1997 / IEC 60909",
    }


# ============================================================
# PÉRDIDAS POR RAMA
# ============================================================

def calcular_perdidas_rama(red: Red, resultado: dict) -> dict:
    """Calcula flujo de potencia y pérdidas en cada rama.

    Retorna {rama_id: {P_entrada_kW, P_salida_kW, perdidas_kW, I_A}}.
    """
    if not resultado.get("convergido"):
        return {}

    Z_base = red.Z_base_ohm
    I_base = red.I_base_A
    S_base_kW = red.S_base_kVA

    # Voltajes complejos en pu
    V_complex = {}
    for bus in red.buses:
        bres = resultado["buses"][bus.id]
        ang = math.radians(bres["delta_deg"])
        V_complex[bus.id] = bres["V_pu"] * complex(math.cos(ang), math.sin(ang))

    perdidas: dict = {}
    for rama in red.ramas:
        rama_id = f"{rama.from_bus}-{rama.to_bus}"
        z_pu = complex(rama.R_ohm, rama.X_ohm) / Z_base

        Vi = V_complex[rama.from_bus]
        Vj = V_complex[rama.to_bus]
        I_ij_pu = (Vi - Vj) / z_pu    # corriente de from hacia to (pu)

        I_ij_A = abs(I_ij_pu) * I_base
        P_loss_pu = (abs(I_ij_pu) ** 2) * rama.R_ohm / Z_base
        P_loss_kW = P_loss_pu * S_base_kW

        # Flujo de potencia en bornes de entrada
        S_entrada_pu = Vi * I_ij_pu.conjugate()
        P_entrada_kW = S_entrada_pu.real * S_base_kW
        P_salida_kW = P_entrada_kW - P_loss_kW

        perdidas[rama_id] = {
            "P_entrada_kW": round(P_entrada_kW, 4),
            "P_salida_kW":  round(P_salida_kW,  4),
            "perdidas_kW":  round(P_loss_kW,    4),
            "I_A":          round(I_ij_A,        3),
        }

    return perdidas


# ============================================================
# REPORTE
# ============================================================

def reporte_flujo_nodal(resultado: dict) -> list[str]:
    """Genera reporte de texto del flujo nodal. Retorna lista de strings."""
    lineas = []
    estado = "CONVERGIDO" if resultado["convergido"] else "NO CONVERGIÓ"

    lineas.append("=" * 62)
    lineas.append("  FLUJO DE POTENCIA NODAL (Newton-Raphson)")
    lineas.append(f"  {resultado['norma']}")
    lineas.append("=" * 62)
    lineas.append(f"  Estado     : {estado}  ({resultado['iteraciones']} iteraciones)")
    lineas.append(f"  Pérdidas   : {resultado['perdidas_totales_kW']:.3f} kW")
    lineas.append("")
    lineas.append("  TENSIONES Y POTENCIAS POR BUS")
    lineas.append("-" * 62)
    lineas.append(
        f"  {'Bus':<10} {'V (pu)':>8} {'V (kV)':>8} {'δ (°)':>8} "
        f"{'P (kW)':>10} {'Q (kVAR)':>10}"
    )
    lineas.append("-" * 62)

    for bus_id, res in resultado["buses"].items():
        lineas.append(
            f"  {bus_id:<10} {res['V_pu']:>8.5f} {res['V_kV']:>8.5f} "
            f"{res['delta_deg']:>8.3f} {res['P_kW']:>10.3f} {res['Q_kVAR']:>10.3f}"
        )

    lineas.append("=" * 62)
    return lineas
