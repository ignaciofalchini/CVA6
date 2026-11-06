# Prueba automática de CAST a 100 MHz

El registro unificado del proyecto se actualizó el 4/11/2026 con la
[comparación de CAST2/CAST3 y la prueba de 120 MHz](/home/nachofalchi/data/fpga-work/cva6-equipo/docs/seguimiento_fpga/actualizacion_20261104_cast.md).
Incluye resultados por etapa, decisiones, latencia, reportes y hashes. El corte
de las 16:53:58 deja 120 MHz en implementación, con su resultado final pendiente.

Se compara la versión del viernes con dos registros (entrada/interior/salida
0/1/1) y, solamente si una implementación terminada falla el timing, una variante
con `LAT_CONV=3` (1/1/1). Esta segunda variante añade un ciclo a las conversiones.
Las estrategias de síntesis e implementación se toman del mismo proyecto
congelado. No se hacen barridos de estrategias ni otros cambios de RTL.

El objetivo de esta campaña es STA a **10 ns**. El BD y su PLL conservan la
configuración física de 90,9 MHz. No se generan BIT/XSA ni se programa la placa;
el cierre a 100 MHz deberá trasladarse después a una configuración de reloj
físico compatible y validarse en hardware.

## Estado de preparación

`campana_preparada` contiene una captura de las fuentes actuales, incluida la
modificación local del viernes. La copia CAST2 pasó el preflight real en Vivado
2026.1. Ambas configuraciones pasaron simulación funcional focalizada. La
preparación no ejecuta síntesis ni implementación.

La campaña existente `campana_preparada` se inició el 4/11/2026 mediante el
servicio de usuario `cva6-fpu100-20261104.service`. Se detuvo a las 01:28 por una
comprobación incorrecta del estado general de Vivado después de pedir solamente
`route_design`. La síntesis y el ruteo habían terminado; faltaban la pasada final
post-route y la decisión automática sobre CAST3. El reporte ruteado de CAST2 dio
WNS −0,423 ns y TNS −312,456 ns a 10 ns. CAST3 no se ejecutó durante la noche.

La comprobación de etapa está corregida y tiene 24 pruebas Tcl aprobadas,
incluidos los artefactos reales de anoche. La continuación se inició en
`recuperacion_20261104`, servicio `cva6-fpu100-recuperacion-20261104.service`:
abre una copia verificada del DCP ruteado, aplica la pasada `Explore` que faltaba
y exporta los reportes completos. Si el STA final válido falla, ejecuta CAST3
desde las mismas fuentes congeladas. Consultar `recuperacion_20261104/state.json`
y su `comparison.json` cuando exista. La historia, código y manifiesto de la
campaña nocturna se conservan intactos; `campana_preparada/recovery.json` enlaza
la continuación. No volver a lanzar la campaña nocturna.

**Cambio de alcance solicitado el 4/11:** se canceló por ahora CAST3. La pasada
final de CAST2 terminó correctamente a las 09:24; se guardaron reportes y DCP,
y el coordinador se cerró sin ejecutar la síntesis ni implementación de CAST3.
La política efectiva queda en `recuperacion_20261104/policy_override.json`:
solo CAST2 y sin fallback. Resultado final: WNS −0,239 ns, TNS −109,091 ns,
1030 endpoints de setup negativos; hold +0,004 ns y ruteo completo. Mejoró
respecto del ruteo inicial, pero no cerró a 100 MHz. Consultar
`recuperacion_20261104/state.json` y `comparison.json` para este resultado final.

**Nueva autorización del 4/11, 13:13:** el usuario volvió a solicitar CAST3.
La prueba única de tres registros se inició mediante
`cva6-fpu100-cast3-20261104.service`, con el reparto 1/1/1 a 10 ns y las mismas
estrategias. El snapshot y los resultados finales de CAST2 se conservan.
La autorización vigente está en `recuperacion_20261104/current_policy.json` y
el controlador/servicio en `control_cast3/`. Los reportes nuevos se guardan en
`recuperacion_20261104/cast3/reports`; el estado actual y la comparación final
se consultan en `state.json` y `comparison.json` de esa recuperación. La política
anterior de cancelación se mantiene como registro histórico.

## Reportes de timing por etapa

Los reportes post-síntesis a 10 ns de ambas variantes se generaron en modo de
solo lectura desde sus corridas de síntesis completas:

- `recuperacion_20261104/cast2/reports/post_synthesis/timing_summary.rpt`
- `recuperacion_20261104/cast3/reports/post_synthesis/timing_summary.rpt`

Cada carpeta también contiene caminos críticos de setup/hold, relojes,
check_timing, contexto, hash del checkpoint y marcador de finalización. Los
retardos de interconexión son **estimados**. Ambos resúmenes dan WNS −0,421 ns,
TNS −36,999 ns y 292 endpoints negativos de setup. El índice con hashes y
métricas está en `recuperacion_20261104/post_synthesis_comparison.json`.

Los reportes finales de implementación son `castN/reports/timing_summary.rpt`
dentro de la recuperación. CAST2 ya tiene su reporte final (WNS −0,239 ns,
TNS −109,091 ns). CAST3 lo genera automáticamente al terminar la implementación
y la pasada final post-route, también cuando el timing resulta negativo.

El Tcl original actualizado ahora exporta obligatoriamente los reportes
post-síntesis antes de implementar en futuras campañas. No se modificó el
código congelado de la corrida activa: sus reportes de síntesis se obtuvieron
mediante el analizador separado `report_post_synthesis.tcl`, sin relanzar síntesis
ni interrumpir la implementación.

CAST3 terminó el ruteo a las 14:30 con WNS −0,101 ns, TNS −14,427 ns y 311
endpoints de setup negativos; todas las 88.123 redes ruteables están ruteadas.
El reporte de esa etapa está en `cast3/reports/routed_before_final/`.
Una segunda incompatibilidad del estado parcial de Vivado impidió `open_run`
después del ruteo, aunque el DCP estaba completo. Se corrigió el flujo original
para abrir directamente el checkpoint verificado. La continuación de CAST3 se
inició a las 14:44 mediante `cva6-fpu100-cast3-final-20261104.service`, limitada a
la pasada final `Explore` y a exportar reportes. Su controlador, manifiesto y
copias de los estados anteriores están en `control_cast3/finalization_recovery`.
No se repitieron síntesis ni ruteo. Consultar `state.json` y `comparison.json` para
el resultado final cuando termine esta etapa.

## Resultado final confirmado: CAST3 a 100 MHz

La optimización y los reportes finalizaron el 4/11/2026 a las 14:50. CAST3
cumple STA a 10 ns: WNS/TNS 0,000/0,000 ns, cero endpoints negativos de setup;
WHS/THS 0,000/0,000 ns, cero endpoints negativos de hold; pulso +3,500 ns.
Todas las 88.125 redes ruteables están ruteadas, sin errores. Los controles de
restricciones, DRC, metodología y bus skew fueron revalidados; se conserva la
excepción exacta de 75 pines de DMI-JTAG inactivo con reloj constante.

Comparación final: CAST2 WNS −0,239 ns, TNS −109,091 ns y 1030 endpoints de
setup negativos; CAST3 WNS 0,000 ns, TNS 0,000 ns y cero endpoints negativos.
El margen de setup y hold es prácticamente nulo al redondeo del reporte.

Reporte final: `recuperacion_20261104/cast3/reports/timing_summary.rpt`.
Checkpoint ganador: `recuperacion_20261104/cast3/reports/final.dcp`.
Identidad de fuentes, reportes y checkpoint: `winner_manifest.json` en la misma
carpeta. Es un cierre de STA de esta implementación; no se generó bitstream ni
se reconfiguró el reloj físico del PS ni se validó la variante en placa.

## Lanzar la campaña preparada

Desde esta carpeta, en una terminal de la computadora anfitriona:

```bash
bash lanzar.sh "$PWD/campana_preparada"
```

Para una campaña nueva que ya esté en estado `prepared`, el lanzador crea un
servicio persistente con `systemd-run --user`. El servicio ejecuta
`systemd-inhibit` y el coordinador congelado, conserva el HOME normal del usuario
para la licencia instalada y continúa después de cerrar la terminal o terminar
la llamada de Codex. Mantener la sesión de usuario y la computadora encendidas,
con alimentación.

El nombre del servicio deriva de un hash de la ruta de salida. `service.json`
registra la unidad, su InvocationID y el PID inicial; `driver.log` recibe stdout
y stderr. El lanzador exige estado `prepared`, serializa intentos simultáneos y
rechaza una unidad o un registro de lanzamiento existentes. El coordinador es
el único que escribe `state.json`.

Consultar estado:

```bash
python3 campaign.py status --output "$PWD/campana_preparada"
tail -f campana_preparada/driver.log
```

Consultar el servicio registrado sin reiniciarlo:

```bash
unit=$(python3 -c 'import json; print(json.load(open("campana_preparada/service.json"))["unit"])')
systemctl --user status "$unit" --no-pager
journalctl --user -u "$unit" --no-pager -n 40
```

Los mensajes del coordinador y Vivado están en `driver.log` y en los logs de cada
variante; el journal permite revisar el inicio y la salida del servicio. El
intento inicial con `nohup` no persistió en el entorno de ejecución de Codex y
fue reemplazado por el servicio indicado arriba. `launcher.pid` pertenece a ese
intento anterior; para la corrida activa usar `service.json`.

También se puede ejecutar en primer plano:

```bash
python3 campana_preparada/code/campaign.py run --output "$PWD/campana_preparada"
```

La ejecución requiere que Vivado vea la identidad/licencia de la computadora.
En Codex, el entorno restringido dio un error de licencia; el probe fuera de ese
entorno y el preflight posterior funcionaron con la licencia instalada.

## Criterio y resultados

El coordinador clasifica cada variante así:

- `timing_passed`: termina la campaña y registra la variante ganadora.
- `timing_failed`: la ejecución y los reportes son válidos, pero hay violaciones
  de setup, hold, pulse width o bus skew. CAST2 habilita entonces la prueba CAST3.
- `invalid`: error de herramienta, licencia, restricciones, ruteo incompleto o
  evidencia faltante. Se detiene con `needs_review` y conserva el diagnóstico.

Se comprueban el período de 10 ns, todas las métricas de timing, ruteo completo,
DRC, metodología y las cuatro restricciones de bus skew. Los 75 pines de DMI-JTAG
inactivo se aceptan solamente si coinciden exactamente con el inventario auditado
y el reporte los atribuye a reloj constante; no se toleran endpoints activos sin
restricción.

Los resultados quedan en `comparison.json` y `state.json`; cada variante tiene
`reports/result.json`, reportes completos, logs y `final.dcp`. `variant.json`
identifica el reparto de registros y los hashes de las entradas. El proyecto
original y los paquetes conocidos buenos se conservan en su ubicación.

Los estados terminales son `complete` (cierre), `complete_without_closure`
(ambas variantes válidas fallaron) y `needs_review` (error o evidencia inválida).
Los códigos de salida son 0, 3 y 2, respectivamente; una interrupción devuelve130.
No se reutilizan corridas incompletas: conservar esa carpeta y preparar otra.

La prueba puede ocupar varias horas. Hay como máximo dos síntesis y dos
implementaciones, secuenciales, con un job por vez, dos threads en síntesis y
cuatro en implementación. El número de etapas de CAST no modifica los límites
independientes que puedan quedar en FMA, PMP u otras unidades.

## Crear otra campaña

```bash
python3 campaign.py plan --output "$PWD/otra_campana"
python3 campaign.py prepare --output "$PWD/otra_campana"
```

`prepare` crea el snapshot, simula ambas configuraciones y abre solamente el
proyecto privado en Vivado. No inicia síntesis ni implementación. `run` ejecuta
las corridas con el código y las fuentes congeladas. Si cambian las fuentes o
el código congelado, se rechaza la ejecución para evitar mezclar resultados.

Pruebas del programa:

```bash
python3 -m unittest -q test_campaign.py test_timing_result.py
```

La simulación focalizada cubre 23 valores esperados, redondeos, límites enteros,
NaN/Inf, stalls, reset y flush en vuelo; no sustituye una regresión completa del
core ni una prueba IEEE exhaustiva. Si se adopta CAST3, reflejar el ciclo añadido
en las comparaciones de rendimiento y en el modelo gem5 correspondiente.
