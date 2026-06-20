"""
Tests P1.3 — Refinamiento de coordinación TCC.

Verifica:
- verificar_margen_selectividad(): margen mínimo entre niveles adyacentes
- verificar_proteccion_backup(): disparo de respaldo cuando primario falla
- Integración con verificar_cadena() existente
"""
import pytest
from coordinacion import (
    calcular_tiempo_disparo,
    verificar_margen_selectividad,
    verificar_proteccion_backup,
    verificar_cadena,
)


# ---------------------------------------------------------------------------
# verificar_margen_selectividad
# ---------------------------------------------------------------------------

class TestMargenSelectividad:
    def test_margen_suficiente_ok(self):
        """Margen ≥ 0.3s → CUMPLE (criterio IEC 60947-2 §7.2.2)."""
        res = verificar_margen_selectividad(t_inf_s=0.1, t_sup_s=0.5)
        assert res["cumple"] is True
        assert res["margen_s"] == pytest.approx(0.4, abs=1e-6)

    def test_margen_exactamente_minimo(self):
        """Margen = 0.3s exactamente → CUMPLE (límite incluido)."""
        res = verificar_margen_selectividad(t_inf_s=0.1, t_sup_s=0.4)
        assert res["cumple"] is True

    def test_margen_insuficiente(self):
        """Margen < 0.3s → NO CUMPLE."""
        res = verificar_margen_selectividad(t_inf_s=0.2, t_sup_s=0.35)
        assert res["cumple"] is False
        assert res["margen_s"] == pytest.approx(0.15, abs=1e-6)

    def test_sin_margen_no_cumple(self):
        """Tiempos iguales → margen = 0 → NO CUMPLE."""
        res = verificar_margen_selectividad(t_inf_s=0.1, t_sup_s=0.1)
        assert res["cumple"] is False
        assert res["margen_s"] == pytest.approx(0.0, abs=1e-6)

    def test_t_sup_indeterminado(self):
        """Si superior no dispara (t=None) → margen indeterminado."""
        res = verificar_margen_selectividad(t_inf_s=0.1, t_sup_s=None)
        assert res["cumple"] is None
        assert res["estado"] == "INDETERMINADO"

    def test_t_inf_indeterminado(self):
        res = verificar_margen_selectividad(t_inf_s=None, t_sup_s=0.5)
        assert res["cumple"] is None

    def test_margen_minimo_parametrizable(self):
        """Se puede especificar margen mínimo distinto al default."""
        res = verificar_margen_selectividad(t_inf_s=0.1, t_sup_s=0.25, margen_min_s=0.1)
        assert res["cumple"] is True

    def test_retorna_campos(self):
        res = verificar_margen_selectividad(0.1, 0.5)
        for campo in ("cumple", "margen_s", "margen_min_s", "estado"):
            assert campo in res


# ---------------------------------------------------------------------------
# verificar_proteccion_backup
# ---------------------------------------------------------------------------

class TestProteccionBackup:
    def _disparo(self, **kwargs):
        return calcular_tiempo_disparo(**kwargs)

    def test_backup_dispara_cuando_primario_no_alcanza(self):
        """Si primario no llega a Icc, backup debe disparar."""
        # Primario muy pequeño para la falla
        prim = self._disparo(Icc_A=5000, In_A=63, curva="C")
        # Backup más grande
        back = self._disparo(Icc_A=5000, In_A=250, curva="C")
        res = verificar_proteccion_backup(prim, back)
        # Ambos deben disparar con curva C a 5000A/63A = 79×In y 5000/250=20×In
        assert res["backup_dispara"] is not False

    def test_backup_no_necesario_cuando_primario_dispara(self):
        """Si primario dispara, backup no es requerido (es backup)."""
        prim = self._disparo(Icc_A=2000, In_A=63, curva="C")
        back = self._disparo(Icc_A=2000, In_A=250, curva="C")
        res = verificar_proteccion_backup(prim, back)
        assert res["primario_dispara"] == prim["dispara"]

    def test_retorna_campos(self):
        prim = self._disparo(Icc_A=2000, In_A=63, curva="C")
        back = self._disparo(Icc_A=2000, In_A=250, curva="C")
        res = verificar_proteccion_backup(prim, back)
        for campo in ("primario_dispara", "backup_dispara", "estado", "nota"):
            assert campo in res

    def test_estado_ok_cuando_backup_cubre(self):
        """Si backup dispara cuando primario no, estado = OK."""
        # Forzar: primario no dispara
        prim = {"t_s": None, "region": "no_dispara", "dispara": False, "nota": "..."}
        back = {"t_s": 0.1,  "region": "termico",    "dispara": True,  "nota": "..."}
        res = verificar_proteccion_backup(prim, back)
        assert res["estado"] == "OK"

    def test_estado_fallo_cuando_ambos_no_disparan(self):
        prim = {"t_s": None, "region": "no_dispara", "dispara": False, "nota": "..."}
        back = {"t_s": None, "region": "no_dispara", "dispara": False, "nota": "..."}
        res = verificar_proteccion_backup(prim, back)
        assert res["estado"] == "FALLO"


# ---------------------------------------------------------------------------
# Integración: cadena con análisis de márgenes
# ---------------------------------------------------------------------------

class TestIntegracionCadenaMargenes:
    def test_cadena_con_buena_selectividad(self):
        """Cadena bien dimensionada con márgenes de tiempo adecuados."""
        dispositivos = [
            {"nombre": "Cabecera",  "nivel": 0, "In_A": 400, "curva": "TM",
             "Ir_xIn": 0.9},
            {"nombre": "Secundario","nivel": 1, "In_A": 125, "curva": "C",
             "Ir_xIn": 1.0},
            {"nombre": "Terminal",  "nivel": 2, "In_A": 40,  "curva": "C",
             "Ir_xIn": 1.0},
        ]
        # A 2000 A: 2000/40 = 50×In terminal → instantáneo; 2000/125 = 16×In → inst; etc.
        resultado = verificar_cadena(dispositivos, Icc_A=2000, sistema="3F_380")
        assert "selectividad_global" in resultado
        assert resultado["Icc_A"] == 2000

    def test_margen_entre_pares_usando_tiempos_disparo(self):
        """Verificar margen entre par de protecciones con tiempos conocidos."""
        # Usar corriente en región térmica para obtener tiempos > 0
        # Curva C, In=63A: región térmica entre 63 y 630 A; Icc=120A → ratio=1.9
        t_inf = calcular_tiempo_disparo(Icc_A=120, In_A=63, curva="C")
        # Curva C, In=250A: Icc=120A < 250A → no dispara
        t_sup = calcular_tiempo_disparo(Icc_A=120, In_A=250, curva="C")
        # Superior no dispara → margen indeterminado
        res = verificar_margen_selectividad(t_inf["t_s"], t_sup["t_s"])
        assert res["cumple"] is None  # superior no dispara
