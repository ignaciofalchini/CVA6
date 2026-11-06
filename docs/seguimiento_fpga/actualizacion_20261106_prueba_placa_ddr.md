# Prueba en placa del programa en la DDR a 100 MHz

Corte: **6 de noviembre de 2026, 16:51, hora de Córdoba**. Plataforma KR260, K26 `xck26-sfvc784-2LV-c`, Vivado 2026.1, top `kr260_top`. Continúa el [registro del 5 de noviembre](actualizacion_20261105_paquete_100mhz.md).

**La prueba de memoria dio PASS en la placa, en dos corridas manuales desde `xsdb`.** El CVA6 arrancó desde la ROM mínima, saltó a la DDR del PS, ejecutó el programa desde ahí y dejó el resultado en el buzón. Es la primera ejecución del CVA6 en placa con el reloj configurado a 100 MHz, y la primera en la que ejecuta código desde la DDR.

Evidencia: [resultado completo](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/implementacion_ddr/prueba_placa_20261106/RESULTADO.md), con las lecturas, las dos capturas del ILA y los logs de Vivado. El procedimiento paso a paso está en la [guía del paquete](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/implementacion_ddr/paquete_ddr_100mhz/LEEME.md).

## Qué se probó

El diseño es CAST3 con la ROM mínima y las cachés apagadas: WNS/TNS 0,000/0,000 ns y WHS +0,006 ns. El programa `memory_test_ddr.bin` usa solo instrucciones enteras:

- Escribe y relee 16 KiB seguidos desde `0x80100000`, con un patrón y después con el patrón invertido.
- Escribe y relee direcciones sueltas hasta `0xBFFFFFF8`, para detectar direcciones repetidas.
- Deja el resultado en el buzón `0xBFFFF000`, que el ARM lee en `0x83FFFF000`.

## Resultados

| Corrida | Secuencia | ILA armado | ILA disparado | Buzón |
|---|---|---|---|---|
| Primera | FSBL, FPGA y FSBL otra vez | 16:16:58 | 16:21:46 | PASS |
| Segunda | FPGA y un solo FSBL | 16:47:18 | 16:50:45 | PASS |

**Lecturas después de soltar el CVA6, iguales en las dos corridas:**

| Dirección vista por el ARM | Leído | Qué confirma |
|---|---|---|
| `0x83FFFF000` | `00000001`, `00000000` | PASS |
| `0xFF0A0054` | `80000000` | Reset liberado |
| `0x800100000` | `D5BA55AA`, `55AA55AA`, `2A45AA5D`, `AA55AA55` | El CVA6 escribió la zona de prueba, con los valores calculados de antemano |
| `0x83FFFFFF8` | `EA55AA52`, `55AA55AA` | El CVA6 escribió la última dirección de la ventana |
| `0x83FFFF008` | Seis palabras en `00000000` | Ningún fallo anotado |

En la segunda corrida, `0x83FFFF000`, `0x800100000` y `0x83FFFFFF8` estaban en cero antes de soltar el reset, y `cmp` no mostró diferencias en las 101 palabras del programa. Por eso esos valores son de esa corrida.

**Captura del ILA, con trigger en `m_debug_commit_valid`, muestras de la segunda corrida:**

| Muestra | Qué se ve |
|---|---|
| 0 a 45 | El CVA6 ejecuta la ROM mínima, de `0x10000` a `0x10014` |
| 49 | Pide leer `0x80000000` por AXI |
| 72 | La DDR devuelve `1582829300000297`, las dos primeras instrucciones del programa |
| 80 | El PC llega a `0x80000000` |
| 426 a 510 | Escribe ceros en el buzón |
| Desde 875 | Escribe en `0x80100000` y siguientes: `55AA55AAD5BA55AA`, `55AA55AAD5BA55A2`... |

La captura dura 2048 muestras, unos 20 microsegundos, así que cubre el arranque y no el final del programa. Esto resuelve el riesgo de la caché del A53 anotado en el [plan](plan_bootrom_original_y_programas_ddr.md): las lecturas del CVA6 traen las instrucciones que cargó el ARM.

## Lo que se aprendió del FSBL

**Por qué hacen falta el FSBL y la FPGA en ese orden.** Al terminar en modo JTAG, el FSBL revisa si la FPGA está programada, y solo entonces quita el aislamiento entre el PS y el PL (`xfsbl_handoff.c`, línea 787). Eso explica la advertencia del [paquete de septiembre](../../corev_apu/fpga/software/kr260_ps_boot/known_good_2026-09-18/README.md). Que el reloj del PL dependa de ese paso es una deducción: coincide con lo observado, pero no se midió.

**Alcanza con una sola corrida.** Programar la FPGA primero y correr el FSBL una vez dio PASS, y Vivado detectó el ILA y el VIO. Así la DDR se entrena una sola vez. La secuencia de dos corridas sigue siendo la de septiembre y la que usa `cva6 programa`.

**El FSBL se puede colgar sin avisar.** En un primer intento, una corrida frenó en `psu_init.c:17857`, durante el entrenamiento de la DDR. La siguiente, con 15 segundos de espera, frenó en el mismo lugar con `PGSR0` en `80C000FF`, es decir con `QSGERR` y `WLAERR`. El bucle espera `80000FFF` y revisa los errores recién después, así que nunca sale.

- Con el FSBL sin terminar, Vivado avisa `debug hub core was not detected`.
- Los registros de reloj, DDR y reset ya dan bien en ese estado, así que no alcanzan para detectarlo. Hay que comprobar que `stop` frene en `0xfffc85f0`, el final normal.
- La causa exacta no se identificó. Se resolvió volviendo a empezar desde `rst -system`, sin cortar el FSBL y con Vivado desconectado hasta terminar. Cambiaron dos cosas a la vez.

## Problemas encontrados en la herramienta

| Dónde | Problema | Estado |
|---|---|---|
| `ila_capture.tcl` | Cambia `CONTROL.TRIGGER_MODE`, que en este ILA es de solo lectura | Sin corregir: `--con-ila` se frena ahí |
| `ila_capture.tcl` | Lee `CORE_STATUS`; la propiedad se llama `STATUS.CORE_STATUS` | Sin corregir |
| `ila_capture.tcl` | Exigía un solo dispositivo, y Vivado lista `xck26_0` y `arm_dap_1` | Corregido antes de la prueba. Vivado confirmó esos dos dispositivos |
| `board_run.tcl` | No comprueba dónde frenó el FSBL y corre dos veces | Sin corregir |
| Proyecto de Vivado | Su Hardware Manager apuntaba al `.bit` y al `.ltx` de 25 MHz y guardaba un trigger en `0x80004000` | Corregido en `hw.xml`, fuera de git. Hay copia en `.hw/backup/` |
| Proyecto de Vivado | No tiene bitstream, y su `psu_init.c` generado sigue en IOPLL/11 | Sin cambios. Del proyecto solo se usa el Hardware Manager |

## Qué no demuestra

- **Repetibilidad amplia:** son dos corridas el mismo día, una con cada secuencia, con margen de timing de 0,000 ns y a temperatura ambiente.
- **Frecuencia medida:** el registro indica IOPLL/10, 99,999 MHz; no se midió con un instrumento.
- **FPU:** el programa no usa instrucciones de punto flotante, así que CAST3 no se ejercitó en placa.
- **Cachés:** están apagadas en este diseño.
- **Toda la DDR:** se probaron 16 KiB seguidos y direcciones sueltas.
- **La automatización:** `cva6 programa` y `cva6 ensayo` no corrieron con la placa.
- **El paquete con ROM de test:** `paquete_100mhz_desde_cast3` sigue sin ejecutarse en placa. Se decidió empezar por la DDR y dejarlo como plan B.

## Próximos pasos

1. Corregir `ila_capture.tcl` y pasar `cva6 programa` a la secuencia de un solo FSBL, con la comprobación de dónde frenó.
2. Repetir la prueba más veces para tener una medida de repetibilidad.
3. Correr programas que usen la FPU, para ejercitar CAST3 en el procesador completo.
4. Implementar y probar el diseño con cachés encendidas, tal como dice el plan.
