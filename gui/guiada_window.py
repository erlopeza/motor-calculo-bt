"""
GUI guiada v1 para usuarios sin experiencia.

Modulos prohibidos en esta ventana v1:
calculos.py, conductores.py, transformador.py, icc_punto.py.
Solo consume sugerencias.py; no ejecuta calculos electricos completos.
"""
import tkinter as tk
from tkinter import ttk

from sugerencias import (
    listar_perfiles,
    sugerir_carga_por_nombre,
    sugerir_parametros_por_perfil,
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


class GuiadaWindow(tk.Toplevel):
    """Asistente v1 basado solo en sugerencias de perfil y carga."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Asistente guiado - Motor BT")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self._construir_ui()
        self._actualizar_perfil()

    def _construir_ui(self):
        contenedor = tk.Frame(self, bg=BG_MAIN, padx=18, pady=16)
        contenedor.pack(fill="both", expand=True)

        tk.Label(
            contenedor,
            text="ASISTENTE GUIADO V1",
            bg=BG_MAIN,
            fg=FG_LABEL,
            font=FONT_TITLE,
        ).pack(anchor="w", pady=(0, 12))

        frame_inputs = tk.Frame(
            contenedor,
            bg=BG_PANEL,
            highlightbackground=BORDE,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        frame_inputs.pack(fill="x")

        self._combo_perfil = self._crear_combo(frame_inputs, "Perfil", listar_perfiles())
        self._combo_perfil.bind("<<ComboboxSelected>>", lambda _event: self._actualizar_perfil())
        self._entry_carga = self._crear_fila_input(frame_inputs, "Carga / equipo", "")
        self._entry_potencia = self._crear_fila_input(frame_inputs, "Potencia conocida (W)", "")
        self._entry_cantidad = self._crear_fila_input(frame_inputs, "Cantidad", "1")

        tk.Button(
            contenedor,
            text="SUGERIR",
            command=self._sugerir,
            bg=FG_LABEL,
            fg=BG_MAIN,
            activebackground=FG_SUCCESS,
            activeforeground=BG_MAIN,
            font=FONT_MAIN,
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
        ).pack(fill="x", pady=12)

        self._frame_resultados = tk.Frame(
            contenedor,
            bg=BG_PANEL,
            highlightbackground=BORDE,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        self._frame_resultados.pack(fill="x")
        self._resultado_texto = tk.Label(
            self._frame_resultados,
            text="",
            bg=BG_PANEL,
            fg=FG_VALOR,
            font=FONT_MAIN,
            justify="left",
            anchor="w",
            wraplength=440,
        )
        self._resultado_texto.pack(anchor="w", fill="x")

    def _actualizar_perfil(self):
        perfil = self._combo_perfil.get()
        try:
            parametros = sugerir_parametros_por_perfil(perfil)
        except ValueError as error:
            self._mostrar_error(str(error))
            return
        self._mostrar_resultado(
            "Perfil base\n"
            f"Perfil: {perfil}\n"
            f"gi: {parametros['gi']}\n"
            f"cos_phi_base: {parametros['cos_phi_base']}\n"
            f"Vn: {parametros['Vn_V']} V / {parametros['sistema']}\n"
            f"Fuente: {parametros['fuente']}"
        )

    def _sugerir(self):
        perfil = self._combo_perfil.get()
        nombre_carga = self._entry_carga.get().strip()
        if not nombre_carga:
            self._mostrar_error("Ingrese una carga o equipo para sugerir.")
            return

        try:
            parametros = sugerir_parametros_por_perfil(perfil)
            cantidad = max(float(self._entry_cantidad.get() or 1), 0.0)
            potencia_usuario = self._leer_potencia_usuario()
        except ValueError as error:
            self._mostrar_error(str(error))
            return

        carga = sugerir_carga_por_nombre(nombre_carga, perfil=perfil)
        if not carga:
            self._mostrar_error("No se encontro una sugerencia para esa carga.")
            return

        potencia_base = potencia_usuario if potencia_usuario is not None else float(carga["P_W"])
        potencia_total = potencia_base * cantidad
        origen_potencia = "usuario" if potencia_usuario is not None else "sugerida"
        faltantes = []
        if potencia_usuario is None:
            faltantes.append("confirmar potencia real de placa/ficha tecnica")

        self._mostrar_resultado(
            "Resultado guiado\n"
            f"Perfil: {perfil}\n"
            f"Carga sugerida: {carga['nombre']}\n"
            f"Potencia base ({origen_potencia}): {potencia_base:.1f} W\n"
            f"Cantidad: {cantidad:g}\n"
            f"Potencia estimada total: {potencia_total:.1f} W\n"
            f"cos_phi: {carga['cos_phi']}\n"
            f"Vn: {parametros['Vn_V']} V / {parametros['sistema']}\n"
            f"gi: {parametros['gi']}\n"
            f"Fuente carga: {carga['fuente']}\n"
            f"Fuente perfil: {parametros['fuente']}\n"
            f"Datos faltantes: {', '.join(faltantes) if faltantes else 'sin faltantes para v1'}"
        )

    def _leer_potencia_usuario(self):
        raw = self._entry_potencia.get().strip()
        if not raw:
            return None
        valor = float(raw)
        if valor <= 0:
            raise ValueError("La potencia debe ser mayor que cero.")
        return valor

    def _crear_combo(self, parent, etiqueta: str, valores: list[str]):
        fila = tk.Frame(parent, bg=BG_PANEL)
        fila.pack(fill="x", pady=4)
        tk.Label(
            fila,
            text=etiqueta,
            bg=BG_PANEL,
            fg=FG_LABEL,
            font=FONT_LABEL,
            width=24,
            anchor="w",
        ).pack(side="left")
        combo = ttk.Combobox(fila, values=valores, state="readonly", width=18)
        combo.set(valores[0])
        combo.pack(side="right")
        return combo

    def _crear_fila_input(self, parent, etiqueta: str, valor_default: str):
        fila = tk.Frame(parent, bg=BG_PANEL)
        fila.pack(fill="x", pady=4)
        tk.Label(
            fila,
            text=etiqueta,
            bg=BG_PANEL,
            fg=FG_LABEL,
            font=FONT_LABEL,
            width=24,
            anchor="w",
        ).pack(side="left")
        entry = tk.Entry(
            fila,
            bg=BG_MAIN,
            fg=FG_TEXT,
            insertbackground=FG_SUCCESS,
            relief="flat",
            font=FONT_MAIN,
            width=20,
        )
        entry.insert(0, valor_default)
        entry.pack(side="right")
        return entry

    def _mostrar_resultado(self, mensaje: str):
        self._resultado_texto.config(text=mensaje, fg=FG_VALOR)

    def _mostrar_error(self, mensaje: str):
        self._resultado_texto.config(text=mensaje, fg=FG_ERROR)
