"""Componentes Tkinter reutilizables, estilizados con la paleta Tokyo Night."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui_core.estado import COLORES, Estado, color_de_estado

_ETIQUETA = {
    Estado.SIN_DATOS: "sin datos",
    Estado.LISTO: "listo",
    Estado.CALCULADO: "calculado",
    Estado.ALERTA: "alerta",
}


class BadgeEstado(tk.Label):
    """Punto + etiqueta de estado, coloreado."""

    def __init__(self, master, estado: Estado):
        super().__init__(master, bg=COLORES["panel"])
        self.set_estado(estado)

    def set_estado(self, estado: Estado) -> None:
        self.color = color_de_estado(estado)
        self.configure(text=f"● {_ETIQUETA[estado]}", fg=self.color,
                       bg=COLORES["panel"], font=("Segoe UI", 9))


class BotonAccion(tk.Button):
    """Botón azul relleno; gris cuando se deshabilita."""

    def __init__(self, master, texto: str, comando):
        super().__init__(
            master, text=texto, command=comando,
            bg=COLORES["acento"], fg=COLORES["fondo"], relief="flat",
            activebackground=COLORES["acento"], font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2", bd=0,
        )

    def set_habilitado(self, habilitado: bool) -> None:
        if habilitado:
            self.configure(state="normal", bg=COLORES["acento"], fg=COLORES["fondo"])
        else:
            self.configure(state="disabled", bg=COLORES["borde"], fg=COLORES["texto_tenue"])


class TablaResultados(tk.Frame):
    """Tabla ttk.Treeview con encabezado Tokyo Night."""

    def __init__(self, master, columnas: list[str]):
        super().__init__(master, bg=COLORES["fondo"])
        self.columnas = columnas
        self.tree = ttk.Treeview(self, columns=columnas, show="headings", height=8)
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=110)
        self.tree.pack(fill="both", expand=True)

    def set_filas(self, filas: list[list]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fila in filas:
            self.tree.insert("", "end", values=fila)

    def num_filas(self) -> int:
        return len(self.tree.get_children())
