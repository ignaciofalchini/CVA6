# Plan: restaurar la BootROM normal y ejecutar programas desde DDR

Fecha: 29/10/2026. **Sólo documentación: no se aplicó ningún cambio de este plan.** Se conserva el CVA6 existente, los paquetes de 25/90,9 MHz y el resultado de timing. La automatización operativa nueva verifica/prepara el arranque de la prueba actual; no implementa ni ejecuta este cambio de BootROM ni la carga de programas nuevos.

## Resultado buscado

Separar la prueba de DDR que está en ROM de los programas que queremos ejecutar: ROM de arranque identificada, programa RISC-V cargado en la DDR del PS a una dirección accesible para CVA6, reset liberado sólo después de verificar la carga, y resultado observable. Sin modificar el pipeline, ISA ni RTL interno del procesador. Cualquier cambio futuro queda en firmware, integración de plataforma, selección de ROM, cargador ARM y scripts; aquí se describen sin aplicarlos.

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
