# Comparar estrategias para mejorar el timing del CVA6

## Política vigente: avanzar al cerrar

El modo predeterminado es `--policy progressive`: en una frecuencia se prueban
combinaciones hasta encontrar la primera que cierre timing; en ese momento se
dejan de probar las restantes y se pasa al siguiente clock. Se intenta primero
la combinación ganadora de la frecuencia anterior. Si fallan las nueve
combinaciones previstas en una frecuencia, el barrido termina ahí y conserva
la mayor frecuencia que cerró. Ese límite corresponde a las estrategias probadas,
no prueba que ninguna otra optimización pueda superarlo.

La lista predeterminada es **100, 125, 150, 175, 200, 225, 250, 275 y 300 MHz**.
Si todas cierran, el resultado indica que se llegó al techo de la lista, no que
300 MHz sea el máximo absoluto. `--policy exhaustive` conserva el modo anterior
para medir todas las combinaciones independientemente del resultado.

Para avanzar no alcanza con WNS positivo: se exige ejecución completa, setup,
hold y pulse width cumplidos, confirmación de signoff en el reporte de timing,
chequeos de restricciones presentes y sin problemas (se permite la categoría
informativa constant_clock), cero nets con errores de routing, y DRC sin Error
ni Critical Warning. Un reporte ambiguo o incompleto detiene la búsqueda con
`needs_review`; no se toma como éxito ni se avanza con restricciones faltantes.

`search_progress.json` registra la combinación ganadora por frecuencia, la mayor
frecuencia cerrada, la primera donde se agotaron las estrategias y si se llegó
al final de la lista. `matrix_summary.csv` conserva todos los intentos ejecutados.

El piloto original continúa sin interrupción. Se inició el servicio
`cva6-timing-a1e958c4166b.service`, con salida en
`/home/nachofalchi/data/fpga-work/archivo/timing-matrix/search_100_300mhz`, para esperar
su finalización y reutilizar sus fuentes congeladas, síntesis y reportes.
No inicia un segundo Vivado mientras espera. Si el piloto falla por un problema
de ejecución, se detiene para revisarlo. Si termina con timing negativo, intenta
las siguientes estrategias a 100 MHz. La copia del piloto debe conservarse,
porque aporta el snapshot de fuentes verificado para toda esta búsqueda.

El barrido completo cruza **frecuencia × síntesis × implementación**. El proyecto
base sigue siendo `corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr`, con las
modificaciones locales vigentes. No modificar RTL entre combinaciones. No se
programa la FPGA ni se genera bitstream.

## Primera etapa predeterminada

| Selección | Estrategia de síntesis |
|---|---|
| `current` | Configuración actual: `Flow_PerfOptimized_high`, con sus opciones guardadas |
| `defaults` | `Vivado Synthesis Defaults` |
| `carry` | `Flow_PerfThresholdCarry` |

| Selección | Estrategia de implementación |
|---|---|
| `current` | Configuración actual: `Performance_ExploreWithRemap`, route `NoTimingRelaxation`, `-tns_cleanup`, physopt post-route |
| `explore_postroute` | `Performance_ExplorePostRoutePhysOpt` |
| `extra_timing` | `Performance_ExtraTimingOpt` |

Las recetas de implementación se obtienen de las propiedades reales de runs de
Vivado: directivas, opciones adicionales y habilitación de physopt pre/post-route.
Por ejemplo, ExtraTimingOpt no habilita physopt post-route; no se lo agrega
artificialmente. Se rechazan pasos de power optimization habilitados que el
coordinador no implementa. Las tres estrategias seleccionadas no los requieren.

Para limitar el primer tramo a **100, 125 y 150 MHz**, usar `--mhz 100 125 150`.
Son como máximo **9 síntesis y 27 routeos**; el modo progresivo salta las
combinaciones restantes en cuanto una cierra.
La síntesis se realiza por cada par (estrategia, frecuencia) y se comparte entre
las tres implementaciones. Se conserva también la posibilidad de recorrer
100, 125, 150, 175, 200, 225, 250, 275 y 300 MHz: **27 síntesis y 81 routeos**.
No se amplía automáticamente la lista durante una corrida.

Esto reemplaza para estos experimentos el uso de una única síntesis fija del
barrido anterior. Cada síntesis recibe el período nominal mediante una restricción
LATE sobre la salida `pl_clk0` del PS, disponible en la frontera de la IP durante
la síntesis del top. Vivado elimina las restricciones de síntesis del checkpoint antes del post-hook;
por eso el verificador recarga explícitamente el XDC nominal, comprueba el período
y escribe `synthesis_clock.rpt`. El log de síntesis conserva la aplicación original
del período durante la optimización. La implementación reaplica el período
al clock primario de la netlist enlazada. La frecuencia física del PS no cambia.
La configuración de las IPs OOC se conserva igual entre experimentos; se varía la
síntesis del top y del RTL del CVA6, no las estrategias internas de cada IP.

## Aislamiento y recuperación

- Se copian las fuentes, headers, constraints, configuración y artefactos de IP
  del proyecto a `source_snapshot/`, preservando sus rutas relativas. Se copian
  `core`, `vendor`, `common`, `config` y `corev_apu`, omitiendo caches, runs,
  software, ejemplos Xilinx, archivos comprimidos y enlaces rotos no utilizados.
- Se comprueban hashes durante la copia. Vivado verifica que todos los archivos
  referenciados existen dentro de la copia y que los include directories son
  locales. Una dependencia excluida o externa hace fallar el preflight.
- Se guardan hashes del snapshot, las recetas y el código. Cambios posteriores
  en el proyecto original no entran a la matriz. Si se modifica el snapshot o
  una receta congelada, se rechaza la recuperación.
- Cada par de síntesis/frecuencia trabaja en otra copia privada. No se resetea ni
  se sintetiza el proyecto original. Una síntesis interrumpida puede repetirse;
  una síntesis exportada y confirmada se reutiliza en la recuperación.
- Cada combinación de implementación usa el runner de recuperación por etapas
  descrito en [timing_sweep.md](timing_sweep.md). No se mezcla un checkpoint entre
  estrategias ni frecuencias. La etapa interrumpida se repite desde el checkpoint
  anterior; no se puede continuar dentro de una llamada `route_design` cortada.
- Un fallo de herramientas detiene la matriz para revisión. Una violación de
  timing es un resultado válido y deja continuar. No hay reintentos infinitos.
- El código de recuperación queda en `code/`. El helper de servicio lo selecciona
  automáticamente al usar `resume`.

## Comandos

Consultar el plan, sin crear snapshots ni lanzar Vivado:

```bash
cd /home/nachofalchi/data/fpga-work/cva6-equipo
python3 corev_apu/fpga/scripts/timing_matrix.py \
  --output /home/nachofalchi/data/fpga-work/timing-matrix/run01 --dry-run
```

Preparar copia, comprobar referencias y exportar las recetas con Vivado,
**sin sintetizar ni implementar**:

```bash
python3 corev_apu/fpga/scripts/timing_matrix.py \
  --output /home/nachofalchi/data/fpga-work/timing-matrix/run01 --preflight-only
```

Para ejecutar mediante servicio, primero habilitar y verificar linger en el host
(ver detalles en `timing_sweep.md`). Luego:

```bash
source /home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/settings64.sh
python3 corev_apu/fpga/scripts/timing_sweep_service.py start --matrix \
  --output /home/nachofalchi/data/fpga-work/timing-matrix/run01
```

Para toda la lista de frecuencias, agregar a `start --matrix`:

```text
--mhz 100 125 150 175 200 225 250 275 300
```

También admite, por ejemplo, `--synthesis current carry --implementation current
extra_timing`. Elegir estrategias y frecuencias antes de iniciar; para cambiarlas,
usar otro directorio de salida. Se recomienda la primera etapa reducida antes
de invertir tiempo en las 81 implementaciones.

Estado y recuperación tras volver a iniciar sesión:

```bash
python3 corev_apu/fpga/scripts/timing_sweep_service.py status \
  --output /home/nachofalchi/data/fpga-work/timing-matrix/run01
python3 corev_apu/fpga/scripts/timing_sweep_service.py resume \
  --output /home/nachofalchi/data/fpga-work/timing-matrix/run01
```

No relanzar si el servicio sigue activo. `stop` conserva lo confirmado.
Linger sigue siendo un requisito: se habilitó el 18/10/2026 y se verificó
`Linger=yes`. Todavía no se ensayó un logout real. Reiniciar no relanza
automáticamente el servicio; usar `resume`.

## Comparar resultados

`matrix_summary.csv` tiene una fila por combinación, con frecuencia, síntesis,
implementación, WNS/TNS, WHS/THS, WPWS/TPWS y estado de ejecución. Comparar
estrategias **a la misma frecuencia**; un mayor WNS de una frecuencia menor no
implica por sí solo una estrategia mejor. Se considera candidato ganador al que
cierra a mayor frecuencia, con restricciones correctas y recursos aceptables.
Si hay empate, comparar margen, utilización y duración.

Los reportes de recursos y restricciones quedan dentro de cada experimento.
`timing=met` no certifica cierre si hay caminos sin restricciones, routeo
incompleto, excepciones incorrectas o DRC. La optimización no garantiza mejorar:
los resultados post-route decidirán si una combinación supera la actual.

El log anterior de síntesis tardó aproximadamente diez minutos. Nueve síntesis
podrían representar alrededor de hora y media con tiempos similares, **más los
27 routeos**, cuyas duraciones todavía no están medidas. Algunas estrategias
pueden tardar bastante más. Se ejecuta una herramienta por vez y se conservan
copias/checkpoints, por lo que hay que prever espacio para fuentes, runs y etapas.

## Validación

- Se consultaron las estrategias disponibles en el Vivado 2026.1 instalado.
- Se ejecutó un preflight real del snapshot y las tres recetas, sin síntesis ni
  routeo, en `reports/timing_matrix_preflight/matrix_ready/`.
- Las pruebas con herramientas simuladas verifican separación de las ocho
  combinaciones de una matriz de prueba, recuperación después de un fallo,
  reutilización de síntesis terminadas, uso del RTL original congelado tras
  editar el original, ejecución desde código congelado y rechazo de recetas
  alteradas. Se mantienen las pruebas anteriores de interrupción y checkpoints.
- **No se ejecutaron nuevas síntesis ni implementaciones** de esta matriz. Falta
  validar con una corrida real el override del clock en síntesis y el post-hook;
  ambos hacen fallar la corrida si el clock no es el esperado. No hay resultados
  nuevos que prueben mejora de timing.

Actualización de ejecución del 18/10/2026: se inició el piloto a 100 MHz, con
síntesis e implementación `current`, en
`/home/nachofalchi/data/fpga-work/archivo/timing-matrix/pilot_100mhz`.
Servicio: `cva6-timing-3cfce9f4dc89.service`. La matriz completa se deja para
después de validar ese piloto. Consultar `state.json`, el servicio y los reportes
para saber el estado actual; este registro de inicio no implica timing cerrado.

```bash
python3 -m unittest discover -s corev_apu/fpga/tests \
  -p 'test_timing*recovery.py' -v
```

Referencias: [estrategias y opciones en flujos de Vivado](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/config_flows)
y catálogo local `Xilinx/2026.1/Vivado/strategies/{VDS2026,VDI2026}.psg`.

## Recuperación del piloto: 18/10/2026

La síntesis terminó y escribió el DCP, pero el primer post-hook buscó un clock
que Vivado había retirado junto con las restricciones de síntesis, por lo que
marcó el run como fallido. No fue un resultado de timing ni un error de la
síntesis del RTL. El log demuestra el override nominal de 10 ns.

Se recuperó el DCP sin repetir síntesis usando `read_checkpoint` junto con
`read_ip` para las tres IPs y `link_design`. Se verificó el clock primario a
100 MHz y se exportó un checkpoint autónomo. El intento de enlazar solo los
DCP de IP no restauró el clock, por lo que no se usó ese resultado. Los logs y
scripts de recuperación permanecen en `pilot_100mhz/recovery/`.

Se confirmó la síntesis recuperada mediante SHA-256 y CRC, dejando constancia
en `synthesis/current/100MHz/synthesis.json`. El código congelado del piloto no
fue modificado; el coordinador reutiliza la síntesis confirmada. La preparación
de la búsqueda progresiva, que todavía no tenía manifest ni resultados, recibió
el verificador corregido y archivó su versión anterior en
`search_100_300mhz/recovery_before_clock_fix/`. Ambos servicios se reanudaron.

La corrección evita comandos Tcl no compatibles dentro del XDC y aplica el
período nominal también a la netlist enlazada antes de exportar y reportar.
La regresión `test_synthesis_clock_recovery.py` reproduce la retirada de clocks
antes del post-hook y verifica la recarga y el período de 10 ns.
