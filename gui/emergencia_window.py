"""
GUI M9 - Ventana de sistemas de emergencia RIC-N08.
Toplevel no modal. Consume src/sistemas_emergencia.py.
"""
import tkinter as tk
from tkinter import ttk

from src.sistemas_emergencia import (
    CONSUMOS_GRUPO,
    autonomia_requerida,
    clasificar_grupo,
    potencia_generador,
)


BG_MAIN = "#1a1a1a"
BG_PANEL = "#242424"
FG_TEXT = "#d0d0d0"
FG_LABEL = "#00CC44"
FG_VALOR = "#FFFFFF"
FG_ERROR = "#FF4444"
FG_SUCCESS = "#00FF66"
BORDE = "#333333"
FONT_MAIN = ("Consolas", 10)
FONT_TITLE = ("Consolas", 13, "bold")
FONT_LABEL = ("Consolas", 9)


class EmergenciaWindow(tk.Toplevel):
    """
    Ventana Toplevel no modal para sistemas de emergencia RIC-N08.
    Tiene calculos independientes de grupo, autonomia y generador.
    """

    def __init__(self, parent):
        """Inicializa la ventana M9 y construye sus tres secciones."""
        super().__init__(parent)
        self.title("Sistemas de Emergencia RIC-N08 - Motor BT")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self._construir_ui()

    def _construir_ui(self):
        """Construye la interfaz de M9."""
        contenedor = tk.Frame(self, bg=BG_MAIN, padx=18, pady=16)
        contenedor.pack(fill="both", expand=True)
        tk.Label(
            contenedor,
            text="M9 - SISTEMAS DE EMERGENCIA RIC-N08",
            bg=BG_MAIN,
            fg=FG_LABEL,
            font=FONT_TITLE,
        ).pack(anchor="w", pady=(0, 12))

        self._crear_seccion_grupo(contenedor)
        self._crear_seccion_autonomia(contenedor)
        self._crear_seccion_generador(contenedor)

    def _crear_seccion_grupo(self, parent):
        """Crea seccion de clasificacion de grupo."""
        frame = self._panel(parent, "1. Clasificacion de grupo")
        self._combo_tipo_consumo = ttk.Combobox(frame, values=sorted(CONSUMOS_GRUPO.keys()), width=30)
        self._combo_tipo_consumo.set("iluminacion_evacuacion")
        self._combo_tipo_consumo.pack(anchor="w", pady=4)
        self._boton(frame, "CALCULAR GRUPO", self._calcular_grupo).pack(anchor="w", pady=5)
        self._resultado_grupo = self._resultado(frame)

    def _crear_seccion_autonomia(self, parent):
        """Crea seccion de autonomia requerida."""
        frame = self._panel(parent, "2. Autonomia requerida")
        fila = tk.Frame(frame, bg=BG_PANEL)
        fila.pack(fill="x")
        self._entry_grupo = self._entry(fila, "Grupo", "0")
        self._entry_num_pisos = self._entry(fila, "Pisos", "1")
        self._combo_tipo_recinto = ttk.Combobox(frame, values=["general", "asistencial", "educacional", "cine_teatro", "mall", "aeropuerto"], width=30)
        self._combo_tipo_recinto.set("general")
        self._combo_tipo_recinto.pack(anchor="w", pady=4)
        self._boton(frame, "CALCULAR AUTONOMIA", self._calcular_autonomia).pack(anchor="w", pady=5)
        self._resultado_autonomia = self._resultado(frame)

    def _crear_seccion_generador(self, parent):
        """Crea seccion de dimensionamiento de generador."""
        frame = self._panel(parent, "3. Dimensionamiento generador")
        self._entry_cargas = self._entry(frame, "Cargas kW CSV", "10,20,5")
        self._entry_fp = self._entry(frame, "FP", "0.8")
        self._entry_margen = self._entry(frame, "Margen %", "25")
        self._boton(frame, "CALCULAR GENERADOR", self._calcular_generador).pack(anchor="w", pady=5)
        self._resultado_generador = self._resultado(frame)

    def _calcular_grupo(self):
        """Calcula clasificacion de grupo y muestra resultado."""
        try:
            resultado = clasificar_grupo(self._combo_tipo_consumo.get())
            texto = (
                f"Grupo {resultado['grupo']} | {resultado['descripcion']} | "
                f"tmax={resultado['tiempo_max_interrupcion_seg']} s"
            )
            self._set_resultado(self._resultado_grupo, texto)
        except ValueError as error:
            self._set_error(self._resultado_grupo, str(error))

    def _calcular_autonomia(self):
        """Calcula autonomia requerida y muestra resultado."""
        try:
            grupo = int(self._entry_grupo.get())
            pisos = int(self._entry_num_pisos.get())
            resultado = autonomia_requerida(grupo, pisos, self._combo_tipo_recinto.get())
            autonomia = "ilimitada" if resultado["autonomia_min"] == -1 else f"{resultado['autonomia_min']} min"
            texto = f"{autonomia} | fuente={resultado['fuente_recomendada']} | {resultado['articulo_ric']}"
            self._set_resultado(self._resultado_autonomia, texto)
        except ValueError as error:
            self._set_error(self._resultado_autonomia, str(error))

    def _calcular_generador(self):
        """Calcula potencia requerida del generador y muestra resultado."""
        try:
            cargas = [float(valor.strip()) for valor in self._entry_cargas.get().split(",") if valor.strip()]
            fp = float(self._entry_fp.get())
            margen = float(self._entry_margen.get())
            resultado = potencia_generador(cargas, fp, margen)
            texto = (
                f"P={resultado['p_total_kw']:.2f} kW | "
                f"P+margen={resultado['p_con_margen_kw']:.2f} kW | "
                f"S={resultado['s_requerido_kva']:.2f} kVA"
            )
            self._set_resultado(self._resultado_generador, texto)
        except ValueError as error:
            self._set_error(self._resultado_generador, str(error))

    def _panel(self, parent, titulo):
        """Crea un panel con borde y titulo."""
        frame = tk.Frame(parent, bg=BG_PANEL, highlightbackground=BORDE, highlightthickness=1, padx=12, pady=10)
        frame.pack(fill="x", pady=(0, 10))
        tk.Label(frame, text=titulo, bg=BG_PANEL, fg=FG_LABEL, font=FONT_LABEL).pack(anchor="w")
        return frame

    def _entry(self, parent, etiqueta, valor):
        """Crea Entry con etiqueta y valor inicial."""
        fila = tk.Frame(parent, bg=BG_PANEL)
        fila.pack(anchor="w", pady=3)
        tk.Label(fila, text=etiqueta, bg=BG_PANEL, fg=FG_LABEL, font=FONT_LABEL, width=16, anchor="w").pack(side="left")
        entry = tk.Entry(fila, bg=BG_MAIN, fg=FG_TEXT, insertbackground=FG_SUCCESS, relief="flat", font=FONT_MAIN, width=18)
        entry.insert(0, valor)
        entry.pack(side="left")
        return entry

    def _boton(self, parent, texto, comando):
        """Crea boton industrial para calculos M9."""
        return tk.Button(parent, text=texto, command=comando, bg=FG_LABEL, fg=BG_MAIN, activebackground=FG_SUCCESS, activeforeground=BG_MAIN, font=FONT_MAIN, relief="flat", bd=0, padx=10, pady=5, cursor="hand2")

    def _resultado(self, parent):
        """Crea label interno para resultado o error."""
        label = tk.Label(parent, text="", bg=BG_PANEL, fg=FG_VALOR, font=FONT_MAIN, wraplength=520, justify="left")
        label.pack(anchor="w", pady=(4, 0))
        return label

    def _set_resultado(self, label, texto):
        """Muestra un resultado exitoso."""
        label.config(text=texto, fg=FG_VALOR)

    def _set_error(self, label, texto):
        """Muestra un error en rojo dentro de la ventana."""
        label.config(text=texto, fg=FG_ERROR)
