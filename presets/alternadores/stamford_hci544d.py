"""Preset de validacion para alternador Stamford HCI544D W14."""

PARAMETROS_POR_VOLTAGE = {
    380: {"Xd_pp": 0.12, "Xd_p": 0.17, "Xd": 3.51, "X2": 0.23, "X0": 0.11, "Rs_ohm": 0.0041, "Sn_base_kVA": 625},
    400: {"Xd_pp": 0.11, "Xd_p": 0.15, "Xd": 3.17, "X2": 0.20, "X0": 0.10, "Rs_ohm": 0.0041, "Sn_base_kVA": 625},
    416: {"Xd_pp": 0.10, "Xd_p": 0.14, "Xd": 2.93, "X2": 0.19, "X0": 0.09, "Rs_ohm": 0.0041, "Sn_base_kVA": 625},
}


def get_parametros(Vn_V: float, Sn_kVA: float = None) -> dict:
    vn = float(Vn_V)
    voltajes = sorted(PARAMETROS_POR_VOLTAGE.keys())

    if vn <= voltajes[0]:
        base = PARAMETROS_POR_VOLTAGE[voltajes[0]].copy()
    elif vn >= voltajes[-1]:
        base = PARAMETROS_POR_VOLTAGE[voltajes[-1]].copy()
    else:
        v0, v1 = voltajes[0], voltajes[-1]
        for i in range(len(voltajes) - 1):
            if voltajes[i] <= vn <= voltajes[i + 1]:
                v0, v1 = voltajes[i], voltajes[i + 1]
                break
        d0 = PARAMETROS_POR_VOLTAGE[v0]
        d1 = PARAMETROS_POR_VOLTAGE[v1]
        frac = (vn - v0) / (v1 - v0)
        base = {
            "Xd_pp": d0["Xd_pp"] + (d1["Xd_pp"] - d0["Xd_pp"]) * frac,
            "Xd_p": d0["Xd_p"] + (d1["Xd_p"] - d0["Xd_p"]) * frac,
            "Xd": d0["Xd"] + (d1["Xd"] - d0["Xd"]) * frac,
            "X2": d0["X2"] + (d1["X2"] - d0["X2"]) * frac,
            "X0": d0["X0"] + (d1["X0"] - d0["X0"]) * frac,
            "Rs_ohm": d0["Rs_ohm"] + (d1["Rs_ohm"] - d0["Rs_ohm"]) * frac,
            "Sn_base_kVA": d0["Sn_base_kVA"],
        }

    sn_base = float(base["Sn_base_kVA"])
    sn = sn_base if Sn_kVA is None else max(float(Sn_kVA), 1e-9)
    escala = sn_base / sn
    return {
        "Xd_pp_pct": round(base["Xd_pp"], 6),
        "Xd_p_pct": round(base["Xd_p"], 6),
        "Xd_pct": round(base["Xd"], 6),
        "R1_pct": None,
        "X0_pct": round(base["X0"], 6),
        "Xd_pp": round(base["Xd_pp"], 6),
        "Xd_p": round(base["Xd_p"], 6),
        "Xd": round(base["Xd"], 6),
        "X2": round(base["X2"], 6),
        "X0": round(base["X0"], 6),
        "Rs_ohm": round(base["Rs_ohm"], 6),
        "Sn_base_kVA": sn_base,
        "factor_escala": round(escala, 6),
        "modelo": "HCI544D_W14",
        "usa_defaults": False,
        "defaults_aplicados": [],
    }
