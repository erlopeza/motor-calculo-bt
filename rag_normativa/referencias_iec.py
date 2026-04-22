"""Corpus sintetico de referencias IEC/TIA/NCh para RAG local."""

from __future__ import annotations

from pathlib import Path

REFERENCIAS = {
    "IEC_60909.md": """
# IEC 60909 - Calculo de corrientes de cortocircuito en CA

## Factores de tension §4.3
- c_max = 1.05 (BT, Vn <= 1kV) / 1.10 (MT)
- c_min = 0.95 (BT) / 1.00 (MT)
- Uso: c_max para Icc maxima (seleccion protecciones)
       c_min para Icc minima (verificacion disparo)

## Corriente subtransitoria trifasica §4.7.1
Ik3'' = c x Vn / (sqrt(3) x |Z1|)
- Ik3'' = corriente subtransitoria - mas alta - para poder de corte
- Ik3'  = corriente transitoria - intermedia
- Ik3   = corriente permanente - para verificar disparo minimo

## Impedancia del transformador §4.3.2
ZT = ukr/100 x Vn^2 / Sn
Relacion RT/XT desde perdidas en cortocircuito Pk

## Generadores sincronos §4.6
Z1 = R1 + j x Xd'' (subtransitoria)
Z0 = R0 + j x X0   (homopolar)
""".strip(),
    "IEC_60947.md": """
# IEC 60947-2 - Interruptores automaticos de baja tension

## Poder de corte ultimo Icu §8.3.3
Icu >= Icc_max en el punto de instalacion
Verificar: Icu >= Ik3''

## Curvas de disparo estandar
Curva C: Im = 5-10 x In - cargas generales
Curva D: Im = 10-20 x In - arranque de motores
Curva B: Im = 3-5 x In - proteccion de personas

## ETU - Unidad de disparo electronica IEC 60947-2 §7.2
Lr (sobrecarga): 0.4-1.0 x In
Im (magnetico):  1.5-15 x In ajustable
tr (retardo):    configurable por banda de selectividad
""".strip(),
    "IEC_62040.md": """
# IEC 62040 - Sistemas de alimentacion ininterrumpida (UPS)

## Clasificacion §5.3 (IEC 62040-3)
VFI: Tension y frecuencia independientes - doble conversion
     Obligatorio para cargas IT criticas
VI:  Line-interactive - solo tension regulada
VFD: Standby - actua solo en falla

## Autonomia minima §6.4 (IEC 62040-4)
- Instalaciones criticas: >= 15 min (TIA-942 Tier III)
- Instalaciones generales: >= 10 min
- Tiempo recarga a 90%: <= 12 horas

## Eficiencia en doble conversion §6.2
eta_ups tipico = 0.92-0.96 para UPS VFI industriales
""".strip(),
    "IEC_60076.md": """
# IEC 60076-1 - Transformadores de potencia

## Tension de cortocircuito ukr §11.4
Tolerancia: +- 7.5% del valor declarado
Impacto: directamente proporcional a impedancia - afecta Icc secundario

## Calculo Icc secundario §12
Icc_sec = In_sec / (ukr/100)
Icc_max = Icc_sec x (1 + tolerancia_ukr/100)
Icc_min = Icc_sec x (1 - tolerancia_ukr/100)

## Factor de uso maximo recomendado
Trafo de distribucion: <= 80% de Sn nominal
Trafo de aislamiento: <= 80% de Sn nominal
""".strip(),
    "TIA_942.md": """
# TIA-942 - Infraestructura de telecomunicaciones para centros de datos

## Niveles de infraestructura (Tier)
Tier I:   basico - sin redundancia
Tier II:  redundancia de componentes
Tier III: mantenimiento concurrente - N+1
Tier IV:  tolerancia a fallos - 2N

## Autonomia UPS §7.4
Tier I/II: >= 10 minutos
Tier III:  >= 15 minutos
Tier IV:   >= 15 minutos + GE online

## Alimentacion electrica §6.2
Tier III: dos caminos de distribucion - solo uno activo
Tier IV:  dos caminos activos simultaneos
""".strip(),
    "NCH_4_2003.md": """
# NCh Elec 4/2003 - Instalaciones de consumo en BT

## Caida de tension §12.28
DeltaV <= 5% desde bornes secundario transformador hasta punto mas alejado
DeltaV circuito final monofasico: <= 3% recomendado

## Seccion minima conductores §12.28 tabla
Circuito de alumbrado: 1.5 mm2 Cu minimo
Circuito de fuerza:    2.5 mm2 Cu minimo
Alimentadores:         segun calculo Icc + capacidad de conduccion

## Arranque de motores §12.28.8
DeltaV arranque <= 15% para motores con arranque directo
DeltaV arranque <= 10% si otros circuitos sensibles comparten alimentador
""".strip(),
}


def generar_referencias_iec(ruta_corpus_iec: str) -> int:
    """
    Escribe referencias sinteticas como .md.
    Retorna numero de archivos escritos.
    """
    destino = Path(ruta_corpus_iec)
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in REFERENCIAS.items():
        (destino / nombre).write_text(contenido + "\n", encoding="utf-8")
    return len(REFERENCIAS)


def listar_referencias() -> list[str]:
    """Retorna nombres de referencias disponibles."""
    return sorted(REFERENCIAS.keys())

