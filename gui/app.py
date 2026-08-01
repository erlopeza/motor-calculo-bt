"""Ventana principal de la GUI por fases (Tokyo Night) sobre gui_core."""
from __future__ import annotations

import os
import traceback
import tkinter as tk
from tkinter import filedialog

from gui_core.estado import COLORES
from gui_core.fases import modulos_de_fase, PRESENTADOR
from gui_core.sesion import SesionProyecto
from gui.componentes import BarraSuperior, RielFases, PanelModulo
from gui.cargador import cargar_excel_a_sesion


def _fmt(v, dec: int = 2) -> str:
    """Formato seguro de número; '—' si None, str crudo si no es numérico."""
    if v is None:
        return "—"
    try:
        return f"{float(v):.{dec}f}"
    except (TypeError, ValueError):
        return str(v)


def _abrir_carpeta(carpeta: str) -> None:
    try:
        os.startfile(carpeta)  # solo Windows; no-op controlado si no existe
    except Exception:
        pass


def _tabla(columnas, extractor):
    """Fábrica de adaptador tabular: renderiza resultado['filas'] como tabla."""
    def adaptador(panel, resultado):
        panel.mostrar_tabla(columnas, [extractor(f) for f in resultado.get("filas", [])])
    return adaptador


def _render_icc_trafo(panel, r):
    panel.mostrar_fichas([
        ("Icc (kA)", _fmt(r.get("Icc_kA")), None),
        ("Zt (Ω)", _fmt(r.get("Zt_ohm"), 5), None),
    ])


def _render_flujo_nodal(panel, r):
    conv = bool(r.get("convergido"))
    panel.mostrar_fichas([
        ("Convergió", "sí" if conv else "no", "ok" if conv else "alerta"),
        ("Pérdidas (kW)", _fmt(r.get("perdidas_kW"), 3), None),
    ])
    buses = r.get("buses", [])
    if buses:
        panel.mostrar_tabla(
            ["Barra", "V (pu)", "V (kV)", "P (kW)"],
            [[b.get("id"), _fmt(b.get("V_pu"), 4), _fmt(b.get("V_kV"), 4), _fmt(b.get("P_kW"))]
             for b in buses],
        )


def _render_balance(panel, r):
    tableros = r.get("tableros", {})
    panel.mostrar_tabla(
        ["Tablero", "S dem (kVA)", "Uso %", "Deseq. %", "Estado"],
        [[nombre, _fmt(t.get("S_total_kva")), _fmt(t.get("uso_pct"), 1),
          _fmt(t.get("desequilibrio_pct"), 1), t.get("estado", "—")]
         for nombre, t in tableros.items()],
    )
    res = r.get("resultado", {})
    estado_tr = res.get("estado_trafo", "")
    rol = "alerta" if str(estado_tr).upper() not in ("OK", "") else "ok"
    panel.mostrar_fichas([
        ("Uso trafo %", _fmt(res.get("uso_trafo_pct"), 1), None),
        ("Estado trafo", estado_tr or "—", rol),
    ])


def _render_demanda(panel, r):
    res = r.get("resultado") or {}
    panel.mostrar_fichas([
        ("Tipo instalación", res.get("tipo_instalacion", "—"), None),
        ("P total (kW)", _fmt(res.get("P_total_kw")), None),
        ("S total (kVA)", _fmt(res.get("S_total_kva")), None),
        ("I alim (A)", _fmt(res.get("I_alim_A"), 1), None),
        ("Factor crecimiento", _fmt(res.get("factor_crecimiento")), None),
    ])


def _render_reporte(panel, r, carpeta_reportes):
    nivel = r.get("nivel", "—")
    rol = {"FINAL": "ok", "BORRADOR": "precaucion", "INCOMPLETO": "alerta"}.get(nivel)
    fichas = [("Nivel emisión", nivel, rol)]
    for etq, key in [("DOCX", "ruta_docx"), ("PDF", "ruta_pdf"), ("JSON", "ruta_json")]:
        ruta = r.get(key) or ""
        fichas.append((etq, os.path.basename(ruta) if ruta else "—", None))
    panel.mostrar_fichas(fichas)
    panel.agregar_accion("Abrir carpeta", lambda c=carpeta_reportes: _abrir_carpeta(c))


RENDER = {
    "dv": _tabla(["Circuito", "ΔV (V)", "ΔV (%)", "Estado"],
                 lambda f: [f["nombre"], f["dv_v"], f["dv_pct"], f["estado"]]),
    "capacidad": _tabla(["Circuito", "I diseño", "Cap (A)", "OK"],
                        lambda f: [f["nombre"], f["I_diseno"], f["cap_A"], f["ok"]]),
    "sugerencia": _tabla(["Circuito", "Sugerido", "Cap (A)", "ΔV (%)"],
                         lambda f: [f["nombre"], f["sugerido"], f["cap_A"], f["dv_pct"]]),
    "icc_punto": _tabla(["Circuito", "Icc (kA)", "Zt total"],
                        lambda f: [f["nombre"], f["Icc_kA"], f["Zt_total"]]),
    "aporte_motores": _tabla(["Motor", "P (kW)", "Aporte (A)"],
                             lambda f: [f["nombre"], f["P_kW"], f["I_aporte_A"]]),
    "protecciones": _tabla(["Circuito", "Estado", "Icc (kA)"],
                           lambda f: [f["nombre"], f["estado"], f["Icc_kA"]]),
    "coordinacion": _tabla(["Dispositivo", "t (s)", "Región"],
                           lambda f: [f["nombre"], f["t_s"], f["region"]]),
    "arc_flash": _tabla(["Circuito", "E (cal/cm²)", "Frontera (mm)", "Cat EPP"],
                        lambda f: [f["nombre"], f["E_cal_cm2"], f["D_afb_mm"], f["categoria_ppe"]]),
    "icc_trafo": _render_icc_trafo,
    "flujo_nodal": _render_flujo_nodal,
    "balance": _render_balance,
    "demanda": _render_demanda,
    "reporte": _render_reporte,
}


class AppBT(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Motor de Cálculo BT")
        self.configure(bg=COLORES["fondo"])
        self.geometry("1000x640")
        self.sesion = SesionProyecto()
        self.fase_actual = 0
        self.paneles_actuales: list[PanelModulo] = []
        self.carpeta_reportes = os.path.join(os.getcwd(), "salida_reportes")

        self.barra = BarraSuperior(self, on_cargar=self._cargar_excel)
        self.barra.pack(fill="x")
        cuerpo = tk.Frame(self, bg=COLORES["fondo"]); cuerpo.pack(fill="both", expand=True)
        self.riel = RielFases(cuerpo, self.sesion, on_seleccion=self.mostrar_fase)
        self.riel.pack(side="left", fill="y")
        self.area = tk.Frame(cuerpo, bg=COLORES["fondo"]); self.area.pack(side="right", fill="both", expand=True)
        self.mostrar_fase(0)

    def _cargar_excel(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not ruta:
            return
        resumen = cargar_excel_a_sesion(ruta, self.sesion)
        error = resumen["error"]
        estado = f"{resumen['hojas']} hojas" if not error else str(error)[:120]
        self.barra.set_info(self.sesion.proyecto, self.sesion.perfil, estado, es_error=bool(error))
        self.riel.refrescar()
        self.mostrar_fase(self.fase_actual)

    def mostrar_fase(self, fase: int):
        self.fase_actual = fase
        for w in self.area.winfo_children():
            w.destroy()
        self.paneles_actuales = []
        for m in modulos_de_fase(fase):
            panel = PanelModulo(self.area, m, self.sesion, on_calcular=self.ejecutar_modulo)
            panel.pack(fill="x", pady=6)
            self.paneles_actuales.append(panel)

    def ejecutar_modulo(self, modulo_id: str):
        fn = PRESENTADOR.get(modulo_id)
        if fn is None:
            return
        try:
            if modulo_id == "reporte":
                os.makedirs(self.carpeta_reportes, exist_ok=True)
                resultado = fn(self.sesion, carpeta_salida=self.carpeta_reportes)
            else:
                resultado = fn(self.sesion)
            self.sesion.registrar(modulo_id, resultado, resultado.get("alertas", []))
        except Exception as e:
            traceback.print_exc()
            self.barra.set_info(self.sesion.proyecto, self.sesion.perfil,
                                 estado=f"error en {modulo_id}: {e}", es_error=True)
            return
        adaptador = RENDER.get(modulo_id)
        for panel in self.paneles_actuales:
            if panel.modulo.id == modulo_id and adaptador is not None:
                try:
                    panel.limpiar_resultados()
                    if modulo_id == "reporte":
                        adaptador(panel, resultado, self.carpeta_reportes)
                    else:
                        adaptador(panel, resultado)
                except Exception as e:
                    traceback.print_exc()
                    self.barra.set_info(self.sesion.proyecto, self.sesion.perfil,
                                         estado=f"error al renderizar {modulo_id}: {e}", es_error=True)
            panel.refrescar_estado()
        self.riel.refrescar()


def main():
    AppBT().mainloop()


if __name__ == "__main__":
    main()
