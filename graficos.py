import os
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

STYLE = {
    "bg": "#1a1a2e",
    "surface": "#16213e",
    "grid": "#2a2a4a",
    "text": "#e0e0e0",
    "accent": "#00ff88",
    "warning": "#ffaa00",
    "danger": "#ff4444",
    "info": "#4488ff",
    "neutral": "#888888",
}


def _apply_style(fig, ax):
    fig.patch.set_facecolor(STYLE["bg"])
    ax.set_facecolor(STYLE["surface"])
    ax.tick_params(colors=STYLE["text"])
    ax.xaxis.label.set_color(STYLE["text"])
    ax.yaxis.label.set_color(STYLE["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor(STYLE["grid"])
    ax.grid(True, color=STYLE["grid"], linewidth=0.5, linestyle="--")


def _ruta_salida(tipo, ruta_base, proyecto=""):
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    nombre = f"{tipo}_{proyecto}_{ts}.png" if proyecto else f"{tipo}_{ts}.png"
    if ruta_base:
        os.makedirs(ruta_base, exist_ok=True)
        return os.path.join(ruta_base, nombre)
    return nombre


def _color_dv(v):
    if v <= 1.5:
        return STYLE["accent"]
    if v <= 3.0:
        return STYLE["warning"]
    if v <= 5.0:
        return "#ff8800"
    return STYLE["danger"]


def grafico_dv_circuitos(circuitos, titulo="Perfil ΔV por circuito", ruta_salida=None):
    if not circuitos:
        return None
    ids = [c.get("id", str(i)) for i, c in enumerate(circuitos)]
    dvs = [c["dv_pct"] for c in circuitos]
    cols = [_color_dv(v) for v in dvs]
    fig, ax = plt.subplots(figsize=(8, max(3, len(ids) * 0.5)))
    ax.barh(ids, dvs, color=cols, height=0.6)
    for lim, color, label in [
        (1.5, STYLE["accent"], "1.5%"),
        (3.0, STYLE["warning"], "3%"),
        (5.0, "#ff8800", "5%"),
    ]:
        ax.axvline(lim, color=color, linewidth=0.8, linestyle="--", alpha=0.6, label=label)
    ax.set_xlabel("ΔV [%]")
    ax.set_title(titulo, color=STYLE["text"], fontsize=10)
    ax.legend(fontsize=8, facecolor=STYLE["bg"], labelcolor=STYLE["text"])
    _apply_style(fig, ax)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("dv_circuitos", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_decremento_ge(resultado_ge, titulo="Curva de decremento Icc GE", ruta_salida=None):
    ikpp = resultado_ge["Ik3_pp_kA"]
    ikp = resultado_ge["Ik3_p_kA"]
    ik = resultado_ge["Ik3_kA"]
    tpp = resultado_ge.get("T_pp_s", 0.012)
    tp = resultado_ge.get("T_p_s", 0.08)
    ta = resultado_ge.get("Ta_s", 0.018)
    t = np.linspace(0, 0.4, 500)
    sym = (ikpp - ikp) * np.exp(-t / tpp) + (ikp - ik) * np.exp(-t / tp) + ik
    asym = sym + np.sqrt(2) * ikpp * np.exp(-t / ta)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t * 1000, sym, color=STYLE["info"], linewidth=1.5, label="Icc simétrica")
    ax.plot(t * 1000, asym, color=STYLE["warning"], linewidth=1.5, linestyle="--", label="Icc asimétrica")
    for val, lbl, col in [
        (ikpp, "Ik''", STYLE["accent"]),
        (ikp, "Ik'", STYLE["warning"]),
        (ik, "Ik", STYLE["neutral"]),
    ]:
        ax.axhline(val, color=col, linewidth=0.6, linestyle=":", alpha=0.7, label=lbl)
    ax.set_xlabel("t [ms]")
    ax.set_ylabel("Icc [kA]")
    ax.set_title(titulo, color=STYLE["text"], fontsize=10)
    ax.legend(fontsize=8, facecolor=STYLE["bg"], labelcolor=STYLE["text"])
    _apply_style(fig, ax)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("decremento_ge", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_tcc(protecciones, icc_punto_ka, titulo="Curvas TCC", ruta_salida=None):
    if not protecciones:
        return None
    i_vals = np.logspace(0, 4, 500)
    fig, ax = plt.subplots(figsize=(8, 5))
    colores = [STYLE["info"], STYLE["accent"], STYLE["warning"], STYLE["danger"]]
    for idx, prot in enumerate(protecciones):
        in_a = prot["In_A"]
        col = colores[idx % len(colores)]
        mascara = i_vals > 1.3 * in_a
        t_vals = np.where(
            mascara,
            0.14 / (np.power(np.maximum(i_vals / in_a, 1.001), 0.02) - 1),
            np.nan,
        )
        t_vals = np.clip(t_vals, 0.01, 10000)
        ax.loglog(
            i_vals[mascara],
            t_vals[mascara],
            color=col,
            linewidth=1.5,
            label=f"{prot['nombre']} {in_a}A",
        )
    ax.axvline(
        icc_punto_ka * 1000,
        color=STYLE["danger"],
        linewidth=1,
        linestyle="--",
        label=f"Icc={icc_punto_ka:.1f}kA",
    )
    ax.set_xlabel("I [A]")
    ax.set_ylabel("t [s]")
    ax.set_title(titulo, color=STYLE["text"], fontsize=10)
    ax.legend(fontsize=8, facecolor=STYLE["bg"], labelcolor=STYLE["text"])
    _apply_style(fig, ax)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("tcc", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_balance_fases(resultado_balance, titulo="Balance de carga por fase", ruta_salida=None):
    fases = ["L1", "L2", "L3"]
    kw = [resultado_balance[f"L{i + 1}_kW"] for i in range(3)]
    amp = [resultado_balance[f"L{i + 1}_A"] for i in range(3)]
    deseq = resultado_balance.get("desequilibrio_pct", 0)
    if deseq > 25:
        col_deseq = STYLE["danger"]
    elif deseq > 15:
        col_deseq = STYLE["warning"]
    else:
        col_deseq = STYLE["accent"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    for ax, vals, lbl in [(ax1, kw, "kW"), (ax2, amp, "A")]:
        bars = ax.bar(fases, vals, color=STYLE["info"], width=0.5)
        max_val = max(vals) if vals else 0
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max_val * 0.02,
                f"{v:.1f}",
                ha="center",
                color=STYLE["text"],
                fontsize=9,
            )
        ax.set_ylabel(lbl)
        _apply_style(fig, ax)
    ax1.set_title(f"{titulo}  |  deseq: {deseq:.1f}%", color=col_deseq, fontsize=9)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("balance_fases", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_autonomia_ups(resultado_ups, titulo="Curva de autonomía UPS", ruta_salida=None):
    energia = resultado_ups["E_bat_kWh"]
    potencia = resultado_ups["P_bat_kW"]
    t_normado = resultado_ups.get("t_minimo_normado_min", 15)
    if potencia <= 0 or energia <= 0:
        return None
    t_max = energia / potencia * 60
    t = np.linspace(0, t_max, 300)
    soc = 100 - (potencia * t / 60) / energia * 100
    soc = np.clip(soc, 0, 100)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.fill_between(t, soc, 20, where=soc >= 20, color=STYLE["accent"], alpha=0.15)
    ax.fill_between(t, soc, 0, where=soc < 20, color=STYLE["danger"], alpha=0.15)
    ax.plot(t, soc, color=STYLE["accent"], linewidth=2)
    ax.axvline(
        t_normado,
        color=STYLE["warning"],
        linewidth=1,
        linestyle="--",
        label=f"t mín normado: {t_normado}min",
    )
    ax.axhline(20, color=STYLE["danger"], linewidth=0.8, linestyle=":", label="SOC mín 20%")
    ax.set_xlabel("t [min]")
    ax.set_ylabel("SOC [%]")
    ax.set_ylim(0, 105)
    ax.set_title(titulo, color=STYLE["text"], fontsize=10)
    ax.legend(fontsize=8, facecolor=STYLE["bg"], labelcolor=STYLE["text"])
    _apply_style(fig, ax)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("autonomia_ups", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_transferencia_ats(resultado_ats, titulo="Secuencia de transferencia ATS", ruta_salida=None):
    fases = ["detección", "arranque GE", "estabilización", "transferencia"]
    keys = ["t_deteccion_ms", "t_arranque_ge_ms", "t_estabilizacion_ms", "t_paralelo_ms"]
    vals = [resultado_ats.get(k, 0) for k in keys]
    cols = [STYLE["warning"], STYLE["info"], STYLE["neutral"], STYLE["accent"]]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.barh(fases, vals, color=cols, height=0.5)
    max_val = max(vals) if vals else 0
    for i, v in enumerate(vals):
        if v > 0:
            ax.text(v + max_val * 0.01, i, f"{v:.0f}ms", va="center", color=STYLE["text"], fontsize=9)
    t_total = resultado_ats.get("t_total_ms", sum(vals))
    ax.set_xlabel("t [ms]")
    ax.set_title(f"{titulo}  |  t_total: {t_total:.0f}ms", color=STYLE["text"], fontsize=10)
    _apply_style(fig, ax)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("transferencia_ats", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_divergencias_simaris(resultados_sim, titulo="Divergencias Motor BT vs SIMARIS", ruta_salida=None):
    if not resultados_sim:
        return None
    labels = [r["descripcion"] for r in resultados_sim]
    divs = [r["divergencia_pct"] for r in resultados_sim]
    cols = []
    for r in resultados_sim:
        cat = r.get("categoria", "")
        if cat == "ERROR_MOTOR":
            cols.append(STYLE["danger"])
        elif cat == "SUPUESTO_CONSERVADOR":
            cols.append(STYLE["accent"])
        elif cat == "EQUIPO_DISTINTO":
            cols.append(STYLE["warning"])
        else:
            cols.append(STYLE["neutral"])
    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.5)))
    ax.barh(labels, divs, color=cols, height=0.6)
    ax.axvline(0, color=STYLE["text"], linewidth=0.8)
    ax.axvline(5, color=STYLE["warning"], linewidth=0.6, linestyle="--", alpha=0.6, label="+5%")
    ax.axvline(-5, color=STYLE["warning"], linewidth=0.6, linestyle="--", alpha=0.6, label="-5%")
    ax.set_xlabel("divergencia [%]")
    ax.set_title(titulo, color=STYLE["text"], fontsize=10)
    ax.legend(fontsize=8, facecolor=STYLE["bg"], labelcolor=STYLE["text"])
    _apply_style(fig, ax)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("divergencias_simaris", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_commissioning(datos, titulo="Estado commissioning", ruta_salida=None):
    medidos = [d for d in datos if d.get("valor_medido") is not None]
    if not medidos:
        return None
    pruebas = [d["prueba"] + " " + d["circuito"] for d in medidos]
    esperados = [d["valor_esperado"] for d in medidos]
    medidos_v = [d["valor_medido"] for d in medidos]
    cols = [
        STYLE["accent"]
        if d["estado"] == "APROBADO"
        else STYLE["danger"]
        if d["estado"] == "FALLA"
        else STYLE["warning"]
        for d in medidos
    ]
    fig, ax = plt.subplots(figsize=(8, max(3, len(pruebas) * 0.5)))
    y = np.arange(len(pruebas))
    ax.barh(y - 0.2, esperados, height=0.35, color=STYLE["neutral"], alpha=0.5, label="esperado")
    ax.barh(y + 0.2, medidos_v, height=0.35, color=cols, label="medido")
    ax.set_yticks(y)
    ax.set_yticklabels(pruebas, fontsize=8)
    ax.set_title(titulo, color=STYLE["text"], fontsize=10)
    ax.legend(fontsize=8, facecolor=STYLE["bg"], labelcolor=STYLE["text"])
    _apply_style(fig, ax)
    fig.tight_layout()
    ruta = ruta_salida or _ruta_salida("commissioning", None)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def generar_todos(reporte, ruta_salida, prefijo=""):
    """
    Acepta el dict de parsear_reporte() o cualquier dict con las mismas claves.
    Genera solo los gráficos para los que hay datos (clave no None).
    """
    generados = {}
    tcc = reporte.get("tcc")
    tcc_dispositivos = None
    if isinstance(tcc, dict):
        dispositivos = []
        for d in tcc.get("dispositivos") or []:
            in_a = d.get("In_A")
            if in_a is None:
                continue
            dispositivos.append({"nombre": d.get("nombre", "N/A"), "In_A": in_a})
        if dispositivos:
            tcc_dispositivos = dispositivos
    sts = reporte.get("sts") or {}
    transferencia = None
    if isinstance(sts, dict) and sts:
        t_transfer = sts.get("t_transfer_ms")
        if t_transfer is not None:
            transferencia = {
                "t_deteccion_ms": 0.0,
                "t_arranque_ge_ms": 0.0,
                "t_estabilizacion_ms": 0.0,
                "t_paralelo_ms": float(t_transfer),
                "t_total_ms": float(t_transfer),
            }
    mapa = {
        "dv_circuitos": (grafico_dv_circuitos, reporte.get("circuitos")),
        "balance_fases": (grafico_balance_fases, reporte.get("balance")),
        "autonomia_ups": (grafico_autonomia_ups, reporte.get("ups")),
        "transferencia_ats": (grafico_transferencia_ats, transferencia),
        "tcc": (grafico_tcc, tcc_dispositivos),
    }
    for nombre, (fn, datos) in mapa.items():
        if datos is None:
            continue
        try:
            ruta = _ruta_salida(f"{prefijo}{nombre}" if prefijo else nombre, ruta_salida)
            if nombre == "tcc":
                icc_falla_a = (reporte.get("tcc") or {}).get("icc_falla_A")
                icc = None if icc_falla_a is None else float(icc_falla_a) / 1000.0
                if icc is None:
                    generados["tcc_advertencia"] = "Icc_punto_kA no disponible — gráfico TCC omitido"
                    continue
                r = fn(datos, icc, ruta_salida=ruta)
            else:
                r = fn(datos, ruta_salida=ruta)
            if r:
                generados[nombre] = r
        except Exception as e:
            generados[nombre + "_error"] = str(e)
    return generados
