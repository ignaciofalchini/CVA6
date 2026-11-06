# Barrido de cierre de timing y recuperación

Para el nuevo barrido que también cambia síntesis e implementación, usar la
[matriz de estrategias](timing_matrix.md). Este documento conserva los detalles
del runner por frecuencia y de su recuperación por etapas.

## Proyecto seleccionado y revisión del 18 de octubre de 2026

Se usa el proyecto vigente, con las modificaciones locales del usuario:

`corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr`

No se utiliza `ariane.xpr`, el ZIP histórico del 11 de septiembre ni los checkpoints
antiguos de `reports/kr260_next_steps`.

- Parte: `xck26-sfvc784-2LV-c`. Top: `kr260_top`.
- Síntesis guardada: `Flow_PerfOptimized_high`. El log confirma
  `PerformanceOptimized`, FSM one-hot, registros equivalentes preservados,
  resource sharing deshabilitado, sin combinación de LUTs y SRL mínimo de 5.
- Implementación guardada: `Performance_ExploreWithRemap`, routeo con
  `-tns_cleanup` y optimización física posterior al routeo. El Tcl aplica
  `ExploreWithRemap` para opt, `Explore` para place y physopt, y
  `NoTimingRelaxation` para route (confirmado consultando Vivado).
- El BD pide **150 MHz**, pero indica **142,855713 MHz efectivos**; el XDC generado
  declara `clk_pl_0` con período de **7 ns**. No tratar esa configuración como una
  implementación exacta de 150 MHz. El barrido impone períodos nominales exactos.
- BD modificado el 16/10 a las 12:15:48; checkpoint de síntesis terminado ese día
  a las 13:11:16; XPR guardado a las 13:11:24 (hora local).
- Se revisaron las 307 referencias directas de `sources_1` y `constrs_1`: todas
  existen y ninguna tiene mtime posterior al checkpoint. Esta es una comprobación
  de archivos. Además, Vivado confirmó `synth_design Complete!` y
  `NEEDS_REFRESH=0` para `synth_1`; `impl_1` figura `Not started`.
- El contenedor ZIP del checkpoint pasó su comprobación CRC.
- Vivado inicialmente informó falta de licencia dentro del sandbox. Al ejecutarlo
  en el host sí inició y permitió auditar el proyecto. No se ejecutó implementación
  real. La auditoría quedó en `reports/timing_sweep_preflight/project_audit.txt`.
- Se probó la exportación real con las IPs enlazadas y terminó correctamente:
  `reports/timing_sweep_preflight/linked_synth.dcp` (22 MB). El reporte
  `baseline_clocks.rpt` confirma `clk_pl_0`, período de 7 ns, duty cycle del 50%.
  El único placeholder restante es `dbg_hub` (`REF_NAME=dbg_hub_CV`), esperado
  antes de implementación. El barrido exige que no quede ninguna caja negra al
  terminar la optimización física post-route.

El checkpoint crudo de `synth_1` depende de tres IPs out-of-context: abierto solo
presenta cajas negras y no contiene el clock. **No sirve directamente para este
barrido**. `prepare_timing_sweep.tcl` abre `synth_1` desde el proyecto, comprueba
que está actualizado y completo, enlaza las IPs, rechaza cajas negras sin resolver
(salvo el `dbg_hub` que Vivado implementa durante la implementación)
y exporta una netlist autónoma. No resetea runs, sintetiza, guarda el proyecto ni
genera bitstream. Opcionalmente `--checkpoint` admite una netlist autónoma ya
enlazada; no pasar el DCP crudo del run.

Al iniciar el runner guarda ese checkpoint enlazado, el código de recuperación y documentos de
procedencia a `inputs/`. Desde ese momento todas las frecuencias y recuperaciones
usan esa netlist fija aunque se vuelva a sintetizar el proyecto original.

## Qué mide

Frecuencias predeterminadas, en orden: **100, 125, 150, 175, 200, 225, 250, 275,
300 MHz**. 100 MHz es el mínimo del barrido. Puede limitarse con `--mhz`.

Se reutiliza una síntesis y se repiten opt, place, physopt, route y physopt
post-route. No se programa la placa ni se genera bitstream. Cambiar la restricción
no modifica el clock físico del PS. Tampoco reproduce el efecto de sintetizar de
nuevo para cada frecuencia. Se conservan las otras restricciones del checkpoint;
verificar clocks derivados y excepciones. Solo se admite clock primario al 50%.

`summary.csv` incluye WNS/TNS, WHS/THS y WPWS/TPWS. `timing=met` significa slacks
reportados no negativos; **no certifica cierre** si hay rutas sin restricciones,
routeo incompleto, DRC o excepciones incorrectas. Revisar los reportes en cada
subdirectorio. Los valores son globales, incluyen otros dominios presentes.
Un fallo de ejecución detiene el barrido; una violación de timing es un resultado
válido y permite continuar a la siguiente frecuencia.

## Preparación y ejecución en el host

Ejecutar desde una terminal del host con Vivado y su licencia disponibles.
Habilitar y verificar linger una sola vez (puede requerir al administrador):

```bash
loginctl enable-linger "$USER"
loginctl show-user "$USER" -p Linger
```

Debe devolver `Linger=yes`. El helper se niega a iniciar si no puede comprobarlo.
No cambia por su cuenta la política de sesiones del equipo.

Comandos concretos para este equipo:

```bash
cd /home/nachofalchi/data/fpga-work/cva6-equipo
source /home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/settings64.sh
python3 corev_apu/fpga/scripts/timing_sweep_service.py start \
  --output /home/nachofalchi/data/fpga-work/timing-sweep/run01
```

Para empezar solo con 100 y 125, agregar `--mhz 100 125` a `start`.
La lista queda fijada al crear la corrida. Para cambiarla, usar otro directorio.

Ver estado y resultados (el helper también muestra la última etapa guardada):

```bash
python3 corev_apu/fpga/scripts/timing_sweep_service.py status \
  --output /home/nachofalchi/data/fpga-work/timing-sweep/run01
```

Tras volver a iniciar sesión, primero consultar `status`. **Si sigue activo, no
hay que relanzarlo**. Si se detuvo, recuperar así, también después de un reboot:

```bash
python3 corev_apu/fpga/scripts/timing_sweep_service.py resume \
  --output /home/nachofalchi/data/fpga-work/timing-sweep/run01
```

`resume` usa `launch.json`, la lista original, el checkpoint fijo y el código
copiado en `inputs/`; no agrega frecuencias ni toma una síntesis nueva. No mover el
directorio ni cambiar la instalación de Vivado durante el barrido.

Detenerlo conservando lo guardado:

```bash
python3 corev_apu/fpga/scripts/timing_sweep_service.py stop \
  --output /home/nachofalchi/data/fpga-work/timing-sweep/run01
```

## Cómo se recupera

1. El servicio de usuario `systemd`, con linger verificado, se ejecuta separado de
   la sesión gráfica/SSH. Cerrar terminal, Codex o hacer logout no debería matarlo.
   Sigue siendo necesario probar un logout real en este host antes del barrido.
2. Se guardan etapas: `constrained`, `optimized`, `placed`, `physopt`, `routed` y
   `final` (physopt post-route). Cada checkpoint se escribe con nombre temporal y
   luego se confirma con rename y un marcador `.ok`.
3. Si el proceso muere, la etapa que estaba ejecutándose se repite. No se puede
   continuar dentro de una llamada `route_design` interrumpida. Por ejemplo,
   una interrupción durante routeo retoma desde `physopt.dcp` y repite el routeo.
4. Se abre la etapa confirmada más avanzada. Si Vivado rechaza ese archivo, se
   intenta la anterior. Los `.partial` se ignoran.
5. Las frecuencias completas con sus reportes presentes se saltean. Si solo faltan
   reportes, se regeneran desde `final.dcp`. Los logs previos quedan en `attempts/`.
6. El SHA-256 del checkpoint fijo y las versiones del código se comprueban al
   retomar. Si no coinciden, se detiene para evitar mezclar resultados. Un lock
   impide dos runners simultáneos en el mismo directorio.
7. `state.json`, `result.json`, `manifest.json` y `summary.csv` se actualizan
   mediante archivos temporales y rename. Si `state.json` dice running tras un
   SIGKILL/reboot, consultar también el servicio: ese estado puede ser anterior
   a la interrupción.

Suspender pausa el avance. Reiniciar/apagar mata la ejecución activa: **no hay
reinicio automático al arrancar**; usar `resume`. Ante un corte de energía la última
escritura puede perderse o dañarse; los checkpoints anteriores permiten recuperar
si siguen legibles. Guardar seis checkpoints por frecuencia requiere espacio
adicional. No borrar `inputs/`, marcadores ni checkpoints mientras corre la suite.

## Validación realizada y pendiente

Se verificó en Vivado la exportación de síntesis enlazada y el clock base. Además,
se ejecutaron pruebas sin licencia con interrupción por SIGTERM, rechazo de un
runner concurrente, recuperación con la netlist original después de cambiar la
fuente, salto de frecuencias terminadas, uso del código congelado en `inputs/`,
rechazo de snapshot alterado, recuperación
real de la lógica Tcl desde physopt y fallback al checkpoint anterior si el último
es ilegible. No equivalen a un ensayo de implementación real ni a un logout real.

```bash
python3 -m unittest discover -s corev_apu/fpga/tests \
  -p test_timing_sweep_recovery.py -v
```

Pendiente antes del barrido largo: verificar un logout real con un servicio corto
y validar una implementación completa. Las consultas al bus fallaron dentro del
sandbox; fuera de él se confirmó que el gestor de usuario está `running` y que
**Linger=no** durante la preparación. Después se habilitó y verificó
**Linger=yes** el 18/10/2026, y se inició el piloto de la matriz de estrategias.
El helper exige `Linger=yes` antes de aceptar start/resume.

## Evidencia histórica

- `/home/nachofalchi/vivado_26456.backup.log:352`: `kr260_top`, `Synthesized`,
  `clk_pl_0` de 3,333 ns (~300 MHz). Un reporte del peor camino de setup muestra
  slack −6,698 ns y delay de datos 9,827 ns. No es post-route.
- El log referencia `backups/timing_300mhz/kr260_top_300mhz.dcp`, pero ese directorio
  estaba vacío durante la revisión.
- `/home/nachofalchi/vivado_281617.backup.log:698` muestra `Physopt postRoute` con
  clock de 20 ns (50 MHz). El reporte solicitado en `/tmp` no se conservó.
- No se localizó reporte verificable de 150 MHz en los logs superiores de Vivado,
  proyecto activo, reportes de fpga-work, backups sin comprimir y `/tmp`. No se
  inspeccionaron archivos comprimidos históricos. El BD actual sí demuestra el
  cambio solicitado a 150 MHz, con frecuencia efectiva distinta.

No se importan esos antecedentes como puntos completos de esta corrida: faltan
reportes post-route comparables e identidad de netlist. No inferir Fmax post-route
a partir del slack de síntesis.
