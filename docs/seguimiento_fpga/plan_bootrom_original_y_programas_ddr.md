# Plan: restaurar la BootROM normal y ejecutar programas desde DDR

Fecha: 29/10/2026; actualizado el 6/11/2026. **El análisis original era sólo documentación; ver abajo las decisiones del 6 de noviembre y lo aplicado.** Se conserva el CVA6 existente, los paquetes de 25/90,9 MHz y el resultado de timing. La automatización operativa nueva verifica/prepara el arranque de la prueba actual; no implementa ni ejecuta este cambio de BootROM ni la carga de programas nuevos.

## Resultado buscado

Separar la prueba de DDR que está en ROM de los programas que queremos ejecutar: ROM de arranque identificada, programa RISC-V cargado en la DDR del PS a una dirección accesible para CVA6, reset liberado sólo después de verificar la carga, y resultado observable. Sin modificar el pipeline, ISA ni RTL interno del procesador. Cualquier cambio futuro queda en firmware, integración de plataforma, selección de ROM, cargador ARM y scripts; aquí se describen sin aplicarlos.

## Decisiones tomadas el 6 de noviembre de 2026

Estas decisiones tienen prioridad sobre las secciones siguientes, que conservan el análisis del 29 de octubre.

| Tema | Decisión |
|---|---|
| ROM | Opción B: ROM mínima `corev_apu/bootrom/bootrom.sv`, que salta a `0x80000000`. No es una restauración de `bootrom_64` |
| Cachés del primer bitstream | **Apagadas**, igual que en el cierre actual. Cambia la ROM y no la configuración de cachés |
| Cachés del segundo bitstream | Encendidas, para medir rendimiento |
| Frecuencia | 100 MHz. Si no cierra timing o no funciona en placa, 90,9 MHz |
| Cómo cargar el programa | **Por JTAG**, sin recompilar nada por cada programa. La app ARM queda como alternativa |

**Orden de trabajo** (reemplaza el paso 1 del orden de ejecución futuro):
1. Probar en placa el paquete de 100 MHz que ya existe, con la ROM de test. Si falla, correr la referencia de 25 MHz para separar un problema del flujo de uno de ese paquete.
2. Implementar el diseño nuevo con cachés apagadas a 100 MHz.
3. Probarlo en placa con la prueba de memoria adaptada.
4. Implementar el diseño con cachés encendidas y medir.

**Cambio de orden el 6 de noviembre:** se probó primero el diseño nuevo en la DDR (paso 3), y el paso 1 quedó como plan B, sin ejecutar.

**Criterio:** tocar lo mínimo respecto del proyecto original. Solo los tres registros de la FPU quedan distintos a propósito.

**Cambios respecto del plan original:**
- **Cachés:** como siguen apagadas, el bloque de `ariane_kr260.sv` y `KR260_MEMORY_TEST_BOOTROM` se quedan, con el mismo nombre. El bitstream con cachés encendidas borra los dos.
- **VIO:** no se toca. Hay que evitar usarlo con un programa cargado, o recargar el programa después.

**Aplicado el 6 de noviembre** en la rama `feature/kr260-programas-ddr`: ROM en `ariane_kr260.sv` y en el `.xpr`, scripts de selección y programa en `corev_apu/fpga/software/kr260_ps_boot/programas/`. La implementación corre en `Automatizacion-FPU-100MHz/implementacion_ddr/`; ver `README-DDR.md` en esa carpeta de campaña.

**Resultado de la implementación (6 de noviembre, 02:25): cerró a 100 MHz en el primer intento**, con cachés apagadas y la ROM mínima. WNS/TNS 0,000/0,000 ns y WHS +0,006 ns, con 0 de 96.944 endpoints de setup fallando y 88.690 redes ruteadas sin errores. Se usó implementación incremental desde el DCP de CAST3, que reutilizó el 98,13 % de las celdas; después del ruteo estaba en −0,019 ns y lo cerró la pasada `Explore`. **El margen sigue siendo nulo.** El paquete está en `implementacion_ddr/paquete_ddr_100mhz/`.

**Resultado en placa (6 de noviembre): la prueba de memoria dio PASS en dos corridas manuales.** Ver el [registro de la prueba](actualizacion_20261106_prueba_placa_ddr.md).

### Carga del programa por JTAG

Con esta decisión no hace falta `kr260_load.c` ni cambiar `main.c`. Lo hace `xsdb`, siguiendo la secuencia que `cva6 ensayo` ya usa para preparar la placa:

1. **Preparar:** programar el bitstream y correr el FSBL, con el CVA6 retenido en reset. `check_prepared` ya comprueba reloj, reset, PL, DDR y ancho de HP0.
2. **Limpiar el buzón:** `mwr` en `0x83FFFF000`, cuatro palabras de 64 bits.
3. **Cargar:** `dow -data programa.bin 0x800000000`. Rechazar la imagen si alcanza el buzón.
4. **Verificar:** releer la imagen con `mrd -bin -file` y comparar con el `.bin`.
5. **Liberar:** `mwr 0xff0a002c 0x7fff8000`, la misma escritura que hoy hace `kr260_boot.c`.
6. **Esperar:** leer `0x83FFFF000` hasta que valga 1, -1 o -2, con un tiempo límite y sin reiniciar el CVA6.

**Riesgo a comprobar en la primera prueba:** HP0 no es coherente con el ARM. Si lo escrito por JTAG quedara en la caché del A53, el CVA6 no lo vería y la relectura podría dar bien igual. La preparación reinicia el A53 antes de cargar, lo que debería dejar su caché apagada, pero no se probó en placa. La comprobación real es el ILA: las lecturas del CVA6 en `0x80000000` tienen que traer las instrucciones del programa. Si no, se usa la app ARM, que apaga esa caché de forma explícita.

**Resultado de ese riesgo (6 de noviembre):** en las dos corridas, el ILA muestra que las lecturas del CVA6 en `0x80000000` traen `00000297` y `15828293`, las instrucciones que cargó el ARM. No hizo falta la app ARM.

Esta secuencia se ejecutó a mano desde `xsdb` el 6 de noviembre. También está en el comando `cva6 programa`, cuyas pruebas simulan la placa. Ese comando todavía no se ejecutó con hardware.

### Consecuencia sobre el timing

El cierre a 100 MHz y su paquete corresponden a la ROM de test. Cambiar la ROM cambia el diseño, así que no se puede reutilizar ese checkpoint.

- Hace falta una síntesis e implementación nuevas, con su propio bitstream, XSA y FSBL. Cada corrida tarda cerca de 1,5 horas.
- El cierre anterior tuvo margen 0,000 ns y otra implementación del mismo RTL dio −0,208 ns, así que el diseño nuevo puede no cerrar a 100 MHz. Las cachés encendidas no se implementaron nunca en esta placa.
- Volver a 90,9 MHz también requiere su propia implementación a 11 ns y un FSBL con IOPLL/11. El paquete del 22 de octubre tiene otro RTL y la ROM de test.
- Los scripts de esas corridas están en `Automatizacion-FPU-100MHz/`, fuera del repositorio.

## Lo que encontramos realmente

1. `corev_apu/fpga/src/ariane_kr260.sv` instancia **incondicionalmente** `bootrom_kr260_memory_test i_bootrom`. El reset PC de CVA6 apunta a `ariane_soc::ROMBase` (`0x00010000`), no directamente a DDR.
2. La ROM normal existe en `corev_apu/fpga/src/bootrom/bootrom_64.sv`, con fuentes `startup.S`, `src/main.c`, `src/uart.c`, SPI/SD/GPT y Makefile en esa misma carpeta. Es la candidata local a “original”; antes de restaurarla se debe fijar commit, binario y hash exactos con Gonza. No asumir que cualquier imagen llamada bootrom_64 es la misma versión.
3. Quitar `KR260_MEMORY_TEST_BOOTROM` **no cambia por sí solo la instancia de ROM**. Ese define también cambia las reglas de cacheabilidad de la configuración de plataforma: con él activo hay cero regiones cacheables. No retirarlo como si fuera solamente un selector de ROM.
4. El crossbar actual sólo tiene DRAM, CLINT, ROM y debug. No hay destino UART/SPI/SD para el CVA6 en esta integración. Las UART del PS tampoco equivalen a la UART MMIO del CVA6 en `0x10000000`.
5. La ROM normal **siempre inicializa y usa UART**, espera actualización por UART y, si no recibe una petición, intenta carga SD/GPT mediante SPI. Sólo salta a `0x80000000` si la carga termina correctamente; en caso contrario queda en un bucle. Por tanto, la ruta SD también requiere resolver los accesos UART iniciales. **Precargar DDR desde el PS no hace que esa ROM salte automáticamente al programa.** Es necesario resolver el contrato de arranque antes de cambiar la ROM.
6. La aplicación ARM actual es una prueba destructiva: escribe patrones en varios puntos de DDR y limpia el mailbox antes de liberar CVA6. Ejecutarla después de cargar un programa puede sobrescribirlo. Además, espera el PASS específico de la ROM de prueba; un programa normal no está obligado a producirlo.

## Decisión de diseño que debemos acordar primero

| Opción | Qué requiere | Relación con “ROM original” |
|---|---|---|
| A. Restaurar exactamente la ROM normal | Restituir su selección y proveer la UART MMIO que usa siempre; añadir SD/SPI si se pretende usar su carga automática en lugar de actualización por UART. Revisar clock, pines, mapa y DTB. Su cargador escribe el programa en DDR. | Mantiene el contenido original si se fija una imagen exacta. Es más trabajo de integración; no basta cambiar el SV de ROM. |
| B. Precargar desde PS/JTAG y usar un bootstrap de plataforma | Nuevo cargador ARM/host y ROM mínima o modo de arranque que espere una señal y salte al entry de DDR. Mantener el CPU interno igual. | Es otra ROM o firmware de arranque: no describirla como restauración exacta de la ROM original. |

**Propuesta de trabajo:** primero decidir si “original” exige mantener el contenido exacto. Si es así, seguir A y presupuestar la integración de periféricos. Si el objetivo principal es ejecutar programas propios desde DDR sin cambiar el CPU, evaluar B explícitamente con Gonza/profe. No ocultar esa diferencia. La alternativa de fijar el PC mediante debug no está disponible de forma automática: el DMI-JTAG propio del CVA6 está inactivo; ILA/BSCAN no lo sustituye.

## Cambios concretos a preparar después de esa decisión

| Archivo o componente | Cambio futuro necesario | Control de aceptación |
|---|---|---|
| `corev_apu/fpga/src/ariane_kr260.sv`, instancia `i_bootrom` | Seleccionar/instanciar ROM normal o bootstrap acordado, conservando su interfaz. | Confirmar módulo y contenido activos en la jerarquía; primer fetch en ROM. |
| XPR, filesets de síntesis/simulación y Tcl de selección | Habilitar la ROM elegida y evitar que scripts de preparación vuelvan a introducir la de test. Revisar AutoDisabled y las definiciones por run. | Una sola selección efectiva, registrada con hash y manifiesto. |
| `KR260_MEMORY_TEST_BOOTROM` y reglas de caché | Separar selección de ROM del comportamiento de caché. Para la primera validación, conservar la configuración efectiva del CPU del resultado conocido; cualquier cambio de caché será una variante distinta a revisar. | No introducir cambios silenciosos de configuración al reemplazar ROM. |
| Fuentes/imagen de ROM normal | Si se recompila: fijar toolchain, flags, frecuencia, DTB, mapa, stack y entry. No usar `make clean` en la carpeta protegida: generar en una copia. `SECOND_CYCLES` está fijado a 50 MHz y debe revisarse si se adapta el firmware; el stack actual usa `0x84000000`. | Correspondencia ELF/BIN/SV y evidencia de clock/mapa. Distinguir imagen original de una adaptación. |
| `corev_apu/fpga/software/kr260_ps_boot/src/kr260_boot.c` y `main.c` | Crear una variante de cargador separada de la prueba destructiva. Inicializar/verificar PS/DDR/HP y mantener reset, cargar/verificar programa, liberar una vez. | Ningún patrón, limpieza de mailbox o reinicialización DDR después de cargar el programa. Conservar el programa ARM de test como referencia. |
| Linker/ELF RISC-V | Fijar RV64/ABI/entry, segmentos de carga, BSS, stack y reservas. | Todos los segmentos y entry dentro de memoria ejecutable accesible; sin solapar firmware ARM, mailbox ni buffers. |
| Scripts host/JTAG | Separar inicialización de plataforma, transferencia de datos, verificación y ejecución. | La ELF RISC-V no se descarga como código ejecutable del A53; el host/cargador interpreta sus segmentos como datos para DDR. |
| Observabilidad | Definir un protocolo de progreso/PASS/FAIL nuevo y capturas ILA. | No confundir ausencia del PASS de la ROM de test con fallo del programa nuevo. |

## Mapa de carga que hay que respetar

Fuente de verdad: `corev_apu/fpga/src/kr260_addr_pkg.sv`. Ventanas de 1 GiB, con fin exclusivo:

| Vista CVA6 | Vista PS/A53 |
|---|---|
| `[0x80000000, 0xC0000000)` | `[0x800000000, 0x840000000)` |
| Base del programa propuesta `0x80000000` | `0x800000000` |
| Mailbox histórico `0x80004000` | `0x800004000` |

Traducción: `addr_PS = 0x800000000 + (addr_CVA6 - 0x80000000)`.
No confundir el número de dígitos: son dos espacios de direcciones distintos. El mailbox histórico a 16 KiB puede solaparse con el programa; no reservarlo por costumbre sin revisar el mapa real. Elegir la reserva definitiva junto con el linker y la pila. Mantener el GiB reservado frente a firmware/OS/DMA del PS; el segmento del BD no reserva memoria por sí solo.

Si el cargador admite ELF, deberá validar arquitectura/clase/endian, PT_LOAD, relación entre direcciones físicas y virtuales, `filesz <= memsz`, tamaños reales de archivo, límites y solapamientos; cargar bytes y poner a cero BSS. Comprobar que el entry esté en un segmento ejecutable. Para BIN, exigir base, tamaño y entry explícitos: no inferirlos del nombre. Estos son requisitos del cargador futuro, no funciones implementadas ahora.

## Script de linker del programa RISC-V

Agregado el 6 de noviembre de 2026, para la opción B con la ROM mínima `corev_apu/bootrom/bootrom.sv`. Esa ROM salta siempre a `0x80000000`, así que `_start` tiene que quedar exactamente en esa dirección.

```
ENTRY(_start)
SECTIONS
{
    . = 0x80000000;
    .text.init : { KEEP(*(.text.init)) }
    .text      : { *(.text*) }
    .rodata    : { *(.rodata*) *(.srodata*) }
    .data      : { *(.data*) *(.sdata*) }
    .bss (NOLOAD) : { __bss_start = .; *(.sbss*) *(.bss*) *(COMMON); __bss_end = .; }
    /DISCARD/ : { *(.note*) *(.comment) *(.riscv.attributes) *(.eh_frame*) }
}
```

- **`/DISCARD/` es obligatorio.** Sin esa línea, el compilador de Vitis agrega `.note.gnu.build-id` y el linker la deja en `0x80000000`. `_start` queda en `0x80000030` y el procesador intenta ejecutar datos que no son código.
- **`.sdata` y `.sbss`:** el compilador pone ahí variables chicas. Están incluidas para que `_start` limpie toda la zona entre `__bss_start` y `__bss_end`.
- **Compilación:** usar `-mcmodel=medany`. Sin esa opción, el enlace falla porque `0x80000000` queda fuera de alcance.
- **Comprobación:** antes de cargar un programa, confirmar que `_start` esté en `0x80000000` con `riscv64-unknown-elf-nm programa.elf`.

Se probó en QEMU (`virt`, con la memoria en `0x80000000`): sin `/DISCARD/` da instrucción ilegal en `0x80000000`, y con esa línea `_start` queda en esa dirección. Todavía no se ejecutó en el CVA6.

## Cómo leer el resultado del programa

Agregado el 6 de noviembre de 2026. El CVA6 no tiene UART en esta integración, así que el programa informa su resultado escribiendo en la DDR, y el PS lo lee.

| Vista CVA6 | Vista PS/A53 | Contenido |
|---|---|---|
| `0xBFFFF000` | `0x83FFFF000` | 0 en curso, 1 PASS, -1 fallo de memoria, -2 excepción |
| `0xBFFFF008` | `0x83FFFF008` | Dirección del fallo (`mepc` si hubo excepción) |
| `0xBFFFF010` | `0x83FFFF010` | Valor esperado (`mcause` si hubo excepción) |
| `0xBFFFF018` | `0x83FFFF018` | Valor leído (`mtval` si hubo excepción) |

Este formato es el de la prueba actual, con el agregado de la excepción. La dirección es una propuesta. `0x80004000` queda descartada porque un programa de más de 16 KiB la pisaría.

- **Programa:** escribe el resultado al terminar y ejecuta `fence iorw, iorw` antes y después de escribir el estado.
- **Cargador del PS:** limita el tamaño para no alcanzar el buzón y lo limpia antes de liberar el reset. Después espera el resultado con un tiempo límite. Si vence, informa TIMEOUT y no reinicia el CVA6.
- **`cva6 programa`:** lee esta dirección. `cva6 ensayo` sigue esperando el PASS de la ROM de test en `0x800004000`.

## Primer programa: la prueba de memoria en DDR

El primer programa propuesto es una adaptación de `memory_test.S`, que ya se ejecutó en placa desde la ROM y da un PASS claro. **No se puede cargar sin cambios:** escribe patrones desde `0x80000000`, donde quedaría su propio código, y se borra a sí misma. Se comprobó en QEMU: la primera instrucción terminó sobrescrita con `0xd5aa55aa`.

`memory_test.S` queda sin cambios, como referencia de la ROM de test. La versión nueva es `corev_apu/fpga/software/kr260_ps_boot/programas/memory_test_ddr.S`.

| Qué | Prueba en la ROM | Prueba en DDR |
|---|---|---|
| Código | `0x00010000` | `0x80000000` |
| Zona densa de 16 KiB | `0x80000000` a `0x80004000` | `0x80100000` a `0x80104000` |
| Sondas dispersas | `0x80000000` más cada desplazamiento | `0x80100000` más los mismos desplazamientos |
| Sonda final | `0xBFFFFFF8` | `0xBFFFFFF8`, sin cambios |
| Buzón | `0x80004000` | `0xBFFFF000` |
| Excepciones | Sin tratamiento | `mtvec` propio; informa -2 en el buzón |

```asm
.section .text.init
.option norvc
.align 3
.globl _start
_start:
  la t0, trap
  csrw mtvec, t0
  li s0, 0x80100000          // inicio de la zona de prueba
  li s5, 0x80104000          // fin de la zona densa (16 KiB)
  li s1, 0xBFFFF000          // buzon
  sd zero, 0(s1)
  sd zero, 8(s1)
  sd zero, 16(s1)
  sd zero, 24(s1)
  fence iorw, iorw
  li s2, 0x55aa55aa55aa55aa
  li s3, 2
write_pass:
  mv t0, s0
write_loop:
  xor t1, t0, s2
  sd t1, 0(t0)
  addi t0, t0, 8
  bne t0, s5, write_loop
  fence iorw, iorw
  mv t0, s0
read_loop:
  xor t1, t0, s2
  ld t2, 0(t0)
  bne t1, t2, test_fail
  addi t0, t0, 8
  bne t0, s5, read_loop
  not s2, s2
  addi s3, s3, -1
  bnez s3, write_pass
  // Primero se escriben todas las sondas, para detectar direcciones repetidas.
  mv t0, s0
  jal ra, write_probe
  li s4, 0x2000
sparse_write:
  add t0, s0, s4
  jal ra, write_probe
  slli s4, s4, 1
  li t3, 0x40000000
  bltu s4, t3, sparse_write
  li t0, 0xbffffff8
  jal ra, write_probe
  fence iorw, iorw
  mv t0, s0
  jal ra, read_probe
  li s4, 0x2000
sparse_read:
  add t0, s0, s4
  jal ra, read_probe
  slli s4, s4, 1
  li t3, 0x40000000
  bltu s4, t3, sparse_read
  li t0, 0xbffffff8
  jal ra, read_probe
  fence iorw, iorw
  li t1, 1
  sd t1, 0(s1)
  fence iorw, iorw
test_pass:
  j test_pass
write_probe:
  xor t1, t0, s2
  sd t1, 0(t0)
  ret
read_probe:
  xor t1, t0, s2
  ld t2, 0(t0)
  bne t1, t2, test_fail
  ret
test_fail:
  sd t0, 8(s1)
  sd t1, 16(s1)
  sd t2, 24(s1)
  fence iorw, iorw
  li t3, -1
  sd t3, 0(s1)
  fence iorw, iorw
fail_halt:
  j fail_halt
.align 2
trap:
  li s1, 0xBFFFF000
  csrr t0, mepc
  csrr t1, mcause
  csrr t2, mtval
  sd t0, 8(s1)
  sd t1, 16(s1)
  sd t2, 24(s1)
  fence iorw, iorw
  li t3, -2
  sd t3, 0(s1)
  fence iorw, iorw
trap_halt:
  j trap_halt
```

Se compila con el script de linker de este plan y las opciones que ya usa la ROM de test. Ocupa 404 bytes, muy por debajo del inicio de la zona de prueba.

```bash
riscv64-unknown-elf-gcc -static -nostdlib -nostartfiles -march=rv64im_zicsr -mabi=lp64 -mcmodel=medany -mexplicit-relocs -T programa.ld memory_test_ddr.S -o memory_test_ddr.elf
```

```bash
riscv64-unknown-elf-objcopy -O binary memory_test_ddr.elf memory_test_ddr.bin
```

**Probado en QEMU**, cargando el `.bin` en `0x80000000` con 1 GiB de memoria:

| Caso | Buzón | Terminó en |
|---|---|---|
| Normal | 1 | `test_pass`, con el código intacto |
| Fallo inyectado en la comparación | -1, dirección `0x80100000`, esperado y leído correctos | `fail_halt` |
| Instrucción ilegal inyectada | -2, `mepc` `0x8000000C`, `mcause` 2 | `trap_halt` |

QEMU comprueba la lógica del programa, no el CVA6, HP0 ni la DDR real.

**Criterio en placa:** el ILA ve el PC en `0x80000000` y el buzón termina en 1. Además, las lecturas de `0x80000000` en adelante tienen que aparecer en AXI, porque desde la ROM nunca se ejecutó código en DDR. **Se cumplió el 6 de noviembre.**

**Límites de esta prueba:**
- El primer MiB no se prueba con patrones. Lo cubre la verificación del cargador, que relee la imagen antes de liberar el reset, y solo en los bytes que ocupa el programa.
- Con cachés encendidas, las lecturas pueden salir de la caché y no probar la DDR. Por eso conviene correrla primero con las cachés apagadas.

## Orden de ejecución futuro

1. Repetir primero la referencia conocida y registrar identidad de BIT/LTX/XSA/FSBL/app. Conservar el cierre de 90,9 MHz sin sobrescribirlo.
2. Preparar la variante de arranque en una copia de proyecto/salida nueva. No lanzar aquí síntesis ni implementación.
3. Inicializar PS/DDR/HP, programar PL y ejecutar el FSBL parcheado después de programar PL, manteniendo CVA6 en reset. Todo debe corresponder al mismo XSA y frecuencia.
4. Mantener reset mientras se carga/verifica el programa. Si la opción A delega la carga en la ROM por UART/SD, liberar sólo cuando PS/DDR y los periféricos estén listos y usar ese protocolo. Para B, precargar segmentos desde PS/JTAG y verificar antes de liberar.
5. HP0 es no coherente: aplicar la política de caché/barreras del cargador ARM. La aplicación de referencia deshabilita la D-cache del A53; no asumir coherencia automática. Si cambian cachés del CVA6, revisar también visibilidad de instrucciones/datos como variante separada.
6. Armar ILA, liberar reset y observar PC/AXI. La ROM debe alcanzar el entry acordado y leer instrucciones desde DDR. Registrar progreso y terminación con timeout; no resetear/reintentar automáticamente durante tráfico AXI.
7. Una ROM distinta modifica el diseño de plataforma. El cierre previo no certifica el nuevo bitstream: volver a revisar implementación, timing y correspondencia de todos los artefactos antes de declararlo cerrado.

## Pruebas de aceptación propuestas

- Programa mínimo: escribir un identificador y terminar en un bucle conocido, con instrucciones fetch desde DDR verificadas por ILA.
- Programa con datos inicializados y BSS: validar copia de segmentos, ceros, stack y resultado.
- Carga rechazada: imagen fuera de ventana, solapamiento con reservas, ELF de otra arquitectura o archivo truncado; CVA6 permanece en reset.
- Transferencia: comparar hash/readback de los bytes cargados antes de ejecutar.
- Repetición: repetir arranque frío y segunda carga controlada sin borrar el programa con el test ARM antiguo.
- Regresión: conservar acceso al bitstream/prueba de DDR anteriores y resultados de timing separados.

## Entregables y orden para la próxima sesión

1. Acordar A/B y la imagen exacta que llamaremos original.
2. Diseñar el contrato ROM–cargador–programa: entry, mapa, mailbox y salida.
3. Preparar diff propuesto de integración y scripts/software en una rama o copia nueva; revisar que no modifique el CPU interno.
4. Validar estáticamente/simular la selección y carga antes de generar un bitstream nuevo.
5. Ejecutar la prueba mínima en placa y registrar evidencia; sólo después ampliar a aplicaciones.

**Estado al entregar este documento:** no se restauró ninguna ROM, no se implementó un cargador DDR y no se ejecutaron estos pasos. La automatización de la prueba actual no debe interpretarse como implementación de este plan.

## Fuentes locales revisadas

Rutas anteriores relativas al repositorio `cva6-equipo`. Ver `auditorias/bootrom_y_carga_ddr_20261029.json` para hashes del corte. Se revisaron también `docs/kr260_ddr_integration.md` y el XPR activo. La documentación antigua que dice que quitar un define cambia la ROM queda superada por la instancia incondicional observada en el RTL actual.

Comprobaciones directas: [instancia de ROM, configuración de caché y crossbar](../../corev_apu/fpga/src/ariane_kr260.sv), [flujo UART/SD y salto condicionado al éxito](../../corev_apu/fpga/src/bootrom/src/main.c), [startup, stack y entry](../../corev_apu/fpga/src/bootrom/startup.S), [prueba ARM destructiva y liberación de reset](../../corev_apu/fpga/software/kr260_ps_boot/src/kr260_boot.c) y [política de caché del cargador ARM](../../corev_apu/fpga/software/kr260_ps_boot/src/main.c).

Referencia de herramienta: [AMD UG1400, comando dow](https://docs.amd.com/r/2023.1-English/ug1400-vitis-embedded/dow) distingue la descarga ELF al target activo de la transferencia de datos binarios a una dirección. La futura carga RISC-V desde el PS debe respetar esa separación y el mapa local descrito; este documento no ejecuta ninguna descarga.
