"""Utilidad para tests de Tkinter: detecta si hay display disponible."""
from __future__ import annotations


def hay_display() -> bool:
    """True si se puede crear una raíz Tk (hay display). En CI headless → False."""
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.destroy()
        return True
    except Exception:
        return False
