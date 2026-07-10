"""Ventana principal de la GUI por fases (Tokyo Night) sobre gui_core."""
from __future__ import annotations

import traceback
import tkinter as tk
from tkinter import filedialog

from gui_core.estado import COLORES
from gui_core.fases import modulos_de_fase, PRESENTADOR
from gui_core.sesion import SesionProyecto
from gui.componentes import BarraSuperior, RielFases, PanelModulo
from gui.cargador import cargar_excel_a_sesion

# Columnas de la tabla de resultados por módulo (id → (columnas, extractor de fila)).
_COLUMNAS = {
    "dv": (["Circuito", "ΔV (V)", "ΔV (%)", "Estado"],
           lambda f: [f["nombre"], f["dv_v"], f["dv_pct"], f["estado"]]),
    "capacidad": (["Circuito", "I diseño", "Cap (A)", "OK"],
                  lambda f: [f["nombre"], f["I_diseno"], f["cap_A"], f["ok"]]),
    "icc_punto": (["Circuito", "Icc (kA)", "Zt total"],
                  lambda f: [f["nombre"], f["Icc_kA"], f["Zt_total"]]),
    "arc_flash": (["Circuito", "E (cal/cm²)", "Frontera (mm)", "Cat EPP"],
                  lambda f: [f["nombre"], f["E_cal_cm2"], f["D_afb_mm"], f["categoria_ppe"]]),
    "protecciones": (["Circuito", "Estado", "Icc (kA)"],
                     lambda f: [f["nombre"], f["estado"], f["Icc_kA"]]),
    "coordinacion": (["Dispositivo", "t (s)", "Región"],
                     lambda f: [f["nombre"], f["t_s"], f["region"]]),
    "sugerencia": (["Circuito", "Sugerido", "Cap (A)", "ΔV (%)"],
                   lambda f: [f["nombre"], f["sugerido"], f["cap_A"], f["dv_pct"]]),
    "aporte_motores": (["Motor", "P (kW)", "Aporte (A)"],
                       lambda f: [f["nombre"], f["P_kW"], f["I_aporte_A"]]),
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
            resultado = fn(self.sesion)
            self.sesion.registrar(modulo_id, resultado, resultado.get("alertas", []))
        except Exception as e:
            traceback.print_exc()  # detalle completo a consola; el label solo muestra el mensaje
            self.barra.set_info(self.sesion.proyecto, self.sesion.perfil,
                                 estado=f"error en {modulo_id}: {e}", es_error=True)
            return
        # refrescar tabla del panel + badges
        cols = _COLUMNAS.get(modulo_id)
        for panel in self.paneles_actuales:
            if panel.modulo.id == modulo_id and cols and "filas" in resultado:
                columnas, extractor = cols
                panel.mostrar_tabla(columnas, [extractor(f) for f in resultado["filas"]])
            panel.refrescar_estado()
        self.riel.refrescar()


def main():
    AppBT().mainloop()


if __name__ == "__main__":
    main()
