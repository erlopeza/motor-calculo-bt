import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARCAS = (
    "stamford",
    "vertiv",
    "schneider",
    "abb",
    "siemens",
    "leroy",
    "caterpillar",
    "cummins",
    "perkins",
)
DEUDA_MARCAS_EXTERNAS_CICLO_0 = {
    Path("coordinacion.py"),
    Path("simulaciones/analizador.py"),
    Path("sugerencias.py"),
}
DIRS_EXCLUIDOS_GLOBAL = {
    ".claude",  # worktrees de sesiones (checkouts completos del repo) — no es código productivo
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "presets",
    "tests",
}


def _contiene_marca(texto: str, marca: str) -> bool:
    return re.search(rf"(?<![a-z]){re.escape(marca)}(?![a-z])", texto) is not None


def _py_productivos():
    archivos = []
    archivos.extend(
        p for p in ROOT.glob("*.py")
        if not p.name.startswith("test_")
    )
    for carpeta in ("src", "gui"):
        base = ROOT / carpeta
        if base.exists():
            archivos.extend(base.rglob("*.py"))
    return archivos


def test_ningun_modulo_productivo_referencia_marca_comercial():
    hallazgos = []
    for path in _py_productivos():
        if path.relative_to(ROOT) in DEUDA_MARCAS_EXTERNAS_CICLO_0:
            continue
        texto = path.read_text(encoding="utf-8", errors="ignore").lower()
        for marca in MARCAS:
            if _contiene_marca(texto, marca):
                hallazgos.append(f"{path.relative_to(ROOT)} contiene {marca}")

    assert hallazgos == []


def test_modulos_blindados_exponen_usa_defaults():
    from ats import calcular_ats
    from generador import calcular_generador
    from motores import calcular_motor
    from ups import calcular_ups

    resultados = [
        calcular_generador(
            nombre="GE-TEST",
            modelo_ge="GENERICO",
            P_ge_kVA_prime=650,
            P_ge_kVA_emergencia=715,
            cos_phi_ge=0.8,
            V_nominal=400,
            regimen_uso="prime",
            P_demanda_kW=250,
            P_motor_max_kW=30,
            factor_arranque_motor=6.0,
            altitud_msnm=0,
        ),
        calcular_ats(
            nombre="ATS-TEST",
            modelo_ats="GENERICO",
            I_nominal_A=630,
            V_nominal_V=400,
            modo_transferencia="open",
            I_carga_A=420,
            Sn_ge_kVA=650,
        ),
        calcular_ups(
            nombre="UPS-TEST",
            modelo_ups="GENERICO",
            tipo_ups="VFI",
            P_ups_kVA=250,
            V_nominal=380,
            P_carga_kW=180,
            cos_phi_carga=0.9,
            tipo_carga="it",
            nivel_infraestructura="critico",
            n_baterias_serie=40,
            V_bat_unitaria=12,
            Ah_bat=100,
            n_strings=2,
        ),
        calcular_motor(
            nombre="M-TEST",
            P_kW=11,
            V_nominal=380,
            cos_phi=0.86,
            rendimiento=0.93,
            sistema="3F",
            tipo_arranque="directo",
            regimen="permanente",
            periodo_min=60,
            L_m=25,
        ),
    ]

    for resultado in resultados:
        assert isinstance(resultado["usa_defaults"], bool)
        assert isinstance(resultado["defaults_aplicados"], list)


def test_stamford_solo_en_presets():
    permitidos = {
        Path("presets/alternadores/stamford_hci544d.py"),
    }
    for rel in permitidos:
        assert (ROOT / rel).exists()
        assert "stamford" in (ROOT / rel).read_text(encoding="utf-8", errors="ignore").lower()

    hallazgos = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        partes = set(rel.parts)
        if rel.name.startswith("test_"):
            continue
        if partes & DIRS_EXCLUIDOS_GLOBAL:
            continue
        if rel in DEUDA_MARCAS_EXTERNAS_CICLO_0:
            continue
        if not _contiene_marca(
            path.read_text(encoding="utf-8", errors="ignore").lower(), "stamford"
        ):
            continue
        if rel not in permitidos:
            hallazgos.append(str(rel))

    assert hallazgos == []


def test_presets_no_son_importados_en_runtime_productivo():
    for nombre in ("generador.py", "ats.py", "ups.py", "motores.py"):
        texto = (ROOT / nombre).read_text(encoding="utf-8", errors="ignore")
        assert "from presets import" not in texto
        assert "import presets" not in texto
