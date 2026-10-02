"""
BT-ICC-REG-001 — Verificacion de factor de tension en Icc y poder de corte.

Caso de regresion dedicado para calcular_icc_punto() aplicando c_max (IEC 60909
4.3.1) y su propagacion hacia verificacion de poder de corte y reporteria.

Adaptacion respecto al brief original: el escenario pide Vn=400V, pero
calcular_icc_punto() no recibe Vn como parametro -- para sistema="3F" usa
siempre TENSION_SISTEMA["3F"]=380V (conductores.py). Agregar un Vn explicito
seria un cambio de API no solicitado (el brief pide explicitamente no tocar
la API publica sin necesidad demostrada), asi que el escenario se adapta a
380V, el unico valor real que el sistema "3F" soporta. c_max=1.10 y
|Z_total|=0.040 ohm se mantienen exactos: se logran con un cable de longitud
L_m=0 (impedancia de cable nula) y Zt_trafo_ohm=0.040, dejando Z_total
puramente igual a Zt_trafo.
"""
import math

import pytest
from docx import Document

import generador
import transformador
from icc_punto import C_MAX_IEC60909, calcular_icc_punto
from protecciones import verificar_circuito_completo, verificar_poder_de_corte
from reporteria_sec import generar_memoria_docx
from transformador import C_MAX, calcular_icc_transformador

VN_3F = 380.0          # TENSION_SISTEMA["3F"] -- 400V del brief no soportado sin tocar API
Z_TOTAL_OHM = 0.040
C_MAX_CASO = 1.10
PODER_CORTE_KA = 6.0


def _zt_trafo_para_z_total_exacta(z_total_ohm: float):
    """L_m=0 => Z_cable=complex(0,0) exacto => Z_total = Zt_trafo."""
    return z_total_ohm, 0, 10.0, 1  # Zt_trafo_ohm, L_m, S_mm2, paralelos


# ---------------------------------------------------------------------------
# Test 1 -- calculo unitario de Icc, valor esperado independiente
# ---------------------------------------------------------------------------

def test_1_icc_punto_valor_esperado_independiente():
    """El valor esperado se calcula aqui con la ecuacion del modelo, no se
    toma del resultado de produccion como unica fuente."""
    zt_trafo, l_m, s_mm2, paralelos = _zt_trafo_para_z_total_exacta(Z_TOTAL_OHM)

    icc_kA, zt_total, _ = calcular_icc_punto(
        zt_trafo, l_m, s_mm2, paralelos, "3F", c_max=C_MAX_CASO
    )

    # Valor esperado, derivado de forma independiente de calcular_icc_punto:
    # Icc = c_max x Vn / (sqrt(3) x |Z_total|)
    icc_a_esperado = C_MAX_CASO * VN_3F / (math.sqrt(3) * Z_TOTAL_OHM)
    icc_kA_esperado = round(icc_a_esperado / 1000.0, 2)

    assert zt_total == pytest.approx(Z_TOTAL_OHM, abs=1e-9)
    assert icc_kA == pytest.approx(icc_kA_esperado, abs=0.01)
    assert icc_kA == pytest.approx(6.03, abs=0.01)  # valor numerico fijado para este caso


# ---------------------------------------------------------------------------
# Test 2 -- regresion contra comportamiento anterior (c implicitamente 1.0)
# ---------------------------------------------------------------------------

def test_2_regresion_c_max_no_debe_volver_a_ser_unitario():
    """Si una regresion futura elimina la aplicacion de c_max (equivalente a
    c=1.0 siempre), este test debe fallar: exige que c_max=1.10 de un
    resultado mayor y distinto de c=1.0 en el mismo escenario."""
    zt_trafo, l_m, s_mm2, paralelos = _zt_trafo_para_z_total_exacta(Z_TOTAL_OHM)

    icc_con_c_max, _, _ = calcular_icc_punto(
        zt_trafo, l_m, s_mm2, paralelos, "3F", c_max=C_MAX_CASO
    )
    icc_c_unitario, _, _ = calcular_icc_punto(
        zt_trafo, l_m, s_mm2, paralelos, "3F", c_max=1.0
    )

    assert icc_con_c_max != icc_c_unitario
    assert icc_con_c_max > icc_c_unitario
    assert icc_con_c_max == pytest.approx(6.03, abs=0.01)
    assert icc_c_unitario == pytest.approx(5.48, abs=0.01)

    # El default de la funcion (sin pasar c_max) tampoco debe ser c=1.0:
    icc_default, _, _ = calcular_icc_punto(zt_trafo, l_m, s_mm2, paralelos, "3F")
    assert icc_default != icc_c_unitario
    assert icc_default == pytest.approx(C_MAX_IEC60909 * VN_3F / (math.sqrt(3) * Z_TOTAL_OHM) / 1000.0, abs=0.01)


# ---------------------------------------------------------------------------
# Test 3 -- integracion con verificacion de poder de corte
# ---------------------------------------------------------------------------

def test_3_proteccion_consume_icc_corregida_sin_recalculo_propio():
    """La Icc que usa protecciones.py debe ser exactamente la que entrega el
    flujo corregido -- sin recalculo independiente ni factor de tension
    distinto dentro de proteccion."""
    zt_trafo, l_m, s_mm2, paralelos = _zt_trafo_para_z_total_exacta(Z_TOTAL_OHM)

    icc_kA, _, _ = calcular_icc_punto(
        zt_trafo, l_m, s_mm2, paralelos, "3F", c_max=C_MAX_CASO
    )

    es_suficiente, margen_kA = verificar_poder_de_corte(icc_kA, PODER_CORTE_KA)

    # poder_corte_kA=6.0 < Icc=6.03 kA con c_max=1.10 -> el breaker queda
    # insuficiente. protecciones.py no recalcula Icc ni aplica su propio c.
    assert icc_kA == pytest.approx(6.03, abs=0.01)
    assert es_suficiente is False
    assert margen_kA == pytest.approx(PODER_CORTE_KA - icc_kA, abs=0.01)

    resultado = verificar_circuito_completo(
        "BT-ICC-REG-001", In_A=40, curva="C",
        poder_corte_kA=PODER_CORTE_KA, Icc_punto_kA=icc_kA, Vn=VN_3F,
    )
    assert resultado["Icc_punto_kA"] == icc_kA
    assert resultado["poder_ok"] is False
    assert "FALLA PODER CORTE" in resultado["estado"]

    # Contraste: con c=1.0 (comportamiento previo al fix), el MISMO breaker
    # de 6.0 kA habria quedado aprobado -- la consecuencia real del bug.
    icc_sin_c, _, _ = calcular_icc_punto(zt_trafo, l_m, s_mm2, paralelos, "3F", c_max=1.0)
    resultado_bug = verificar_circuito_completo(
        "BT-ICC-REG-001 (sin c_max, comportamiento previo)", In_A=40, curva="C",
        poder_corte_kA=PODER_CORTE_KA, Icc_punto_kA=icc_sin_c, Vn=VN_3F,
    )
    assert resultado_bug["poder_ok"] is True
    assert resultado_bug["estado"] == "OK"


# ---------------------------------------------------------------------------
# Test 4 -- consistencia de politica de c_max entre modulos
# ---------------------------------------------------------------------------

def test_4_c_max_bt_consistente_entre_modulos():
    """transformador.py, icc_punto.py y generador.py deben declarar el mismo
    c_max BT (IEC 60909 4.3.1 = 1.05) -- sin constantes duplicadas
    incompatibles entre modulos."""
    assert C_MAX_IEC60909 == transformador.C_MAX == generador.C_MAX_BT == 1.05

    # El calculo real de icc_punto en produccion (sin override explicito de
    # c_max) debe usar la misma fuente que transformador.py para bornes BT.
    zt_trafo, l_m, s_mm2, paralelos = _zt_trafo_para_z_total_exacta(Z_TOTAL_OHM)
    icc_default, _, _ = calcular_icc_punto(zt_trafo, l_m, s_mm2, paralelos, "3F")
    icc_con_c_max_explicito, _, _ = calcular_icc_punto(
        zt_trafo, l_m, s_mm2, paralelos, "3F", c_max=transformador.C_MAX
    )
    assert icc_default == icc_con_c_max_explicito


# ---------------------------------------------------------------------------
# Test 5 -- consistencia con reporteria
# ---------------------------------------------------------------------------

def test_5_memoria_declara_el_c_max_realmente_usado(tmp_path):
    """La memoria no debe declarar un c_max distinto al usado por el calculo,
    y la Icc maxima presentada debe ser la misma que alimentaria la
    verificacion de poder de corte."""
    kVA, Vn_BT, Ucc_pct = 1000, 380, 5.0
    icc_nom_kA, _, info = calcular_icc_transformador(kVA, Vn_BT, Ucc_pct)

    datos_run = {
        "project_id": "BT-ICC-REG-001",
        "revision": "REG",
        "timestamp": "2026-10-02T00:00:00+00:00",
        "perfil": "industrial",
        "norma": "AWG",
        "n_ok": 1,
        "n_fallas": 0,
        "max_dv_pct": 1.0,
        "max_icc_ka": icc_nom_kA,
        "status": "OK",
        "transformador": {
            "kVA": kVA, "Vn_BT": Vn_BT, "Ucc_pct": Ucc_pct,
            "Icc_nom_kA": icc_nom_kA,
            "Icc_max_kA": info["Icc_max_kA"],
            "Icc_min_kA": info["Icc_min_kA"],
        },
    }
    circuitos = [{
        "nombre": "C-01", "conductor": "6AWG", "S_mm2": 13.3,
        "I_diseno": 40.0, "I_max": 65.0, "cos_phi": 0.9, "L_m": 10.0,
        "paralelos": 1, "sistema": "3F", "dv_v": 1.0, "dv_pct": 0.3,
        "icc_ka": 5.0, "estado": "OK", "norma": "AWG", "observaciones": "",
    }]

    ruta = generar_memoria_docx(datos_run, circuitos, str(tmp_path))
    doc = Document(ruta)
    texto = "\n".join(p.text for p in doc.paragraphs)

    # La memoria debe mostrar la MISMA Icc_max_kA que calculo el transformador
    # real (no un valor hardcodeado/recalculado aparte en reporteria_sec.py).
    assert f"maxima={info['Icc_max_kA']} kA" in texto

    # El c_max citado en el texto fijo de la memoria debe coincidir con la
    # constante realmente usada por transformador.py.
    assert f"c_max = {C_MAX}" in texto

    # NOTA (hallazgo, no corregido aqui -- fuera de alcance de este caso):
    # la cita de c_max en reporteria_sec.py es texto ESTATICO, no derivado
    # programaticamente de transformador.C_MAX. Hoy coinciden (1.05 == 1.05)
    # porque este mismo caso de regresion corrigio ambos a la vez, pero nada
    # impide que vuelvan a divergir si C_MAX cambia sin tocar el texto fijo.
