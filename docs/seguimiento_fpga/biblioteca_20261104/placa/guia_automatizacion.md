# Automatización CVA6 / KR260

La entrada única es `cva6`. Se instala como un wrapper local en `~/.local/bin/cva6`; utiliza Python 3 estándar y las herramientas de FPGA ya instaladas. Configuración de rutas: `config.json`. Las salidas de operaciones quedan en `../operacion/cva6_ops/`, siempre con nombre nuevo.

## Lo habitual para mañana

```bash
cva6 estado
cva6 verificar
cva6 preparar-manana
```

`estado` consulta disco, operaciones recientes y servicios de esta rutina. `verificar` comprueba SHA256 de los paquetes 25/91, checkpoints de referencia, cambios locales del proyecto, herramientas y rutas reales del proyecto. La única excepción histórica documentada es la autoentrada del manifiesto25, nunca un binario con hash incorrecto. `preparar-manana` añade planes de arranque para las dos frecuencias: no conecta a la placa.

## Prueba con la placa conectada

Primero repetir el conocido bueno25. Los comandos sin `--ejecutar` generan un plan; añadir esa opción conecta por JTAG, reinicia PS, programa PL y ejecuta la prueba DDR existente.

```bash
cva6 ensayo --frecuencia 25
cva6 ensayo --frecuencia 25 --ejecutar
cva6 ensayo --frecuencia 91 --con-ila --ejecutar
```

`91` selecciona el paquete de **90,908180 MHz**, no 91 MHz exactos. Su FSBL ya se generó y compiló desde el XSA91 con reset retenido. El éxito de compilación no es una validación en placa: el resultado hardware se registra al ejecutar estas pruebas.

Con `--con-ila`, el controlador prepara la placa dejando CVA6 en reset, arma la captura, espera la confirmación de esa sesión, libera el procesador y reúne el PASS/FAIL con el CSV. Si la captura no se arma correctamente, no inicia la aplicación. Cada operación conserva hashes, Tcl, logs y JSON. No sobrescribe capturas históricas.

**Es la prueba destructiva de DDR que ya existía:** escribe patrones en DDR y ejecuta la ROM de test. No usarla como cargador de programas propios ni para preservar un programa precargado. El [plan de BootROM y programas en DDR](/home/nachofalchi/data/fpga-work/cva6-equipo/docs/seguimiento_fpga/plan_bootrom_original_y_programas_ddr.md) sólo documenta los cambios futuros; no están implementados por esta rutina.

## Pasos separados de JTAG / ILA

El comando `ensayo` coordina lo habitual. Para diagnóstico, se mantienen `placa` y `captura` separados:

```bash
cva6 placa --frecuencia 25 --fase full
cva6 placa --frecuencia 91 --fase prepare
cva6 captura --help
cva6 placa --help
```

Para ejecutar captura separada hay que pasar `--preparacion CARPETA` de una fase `prepare` que terminó READY. La fase `release` utiliza esa misma preparación y, si corresponde, `--captura-armada CARPETA` del ILA. No resetea ni reprograma la FPGA después de armar ILA. Rechaza sesiones viejas, consumidas o de otra frecuencia. Los comandos anteriores son planes, sin ejecución de hardware.

## FSBL de 90,9 MHz

El FSBL preparado está en `../operacion/cva6_ops/fsbl91/build_20261029_1831/`. `fsbl91_manifest.json` liga ELF, fuentes generadas, parche y XSA; el ELF es AArch64 para el PS. No es el programa RISC-V del CVA6.

Para reproducirlo en otra carpeta nueva:

```bash
cva6 fsbl91 --solo-plan
cva6 fsbl91
```

El segundo comando genera/compila software, sin conectar hardware. Usa HSI local y el parche existente, sin cambiar paquetes congelados, BootROM, CPU ni instalación Xilinx. El build emplea un job y prioridad baja. La configuración FSBL específica debe conservar las rutas canónicas verificadas; se rechazan overrides incompatibles.

## Respaldos

```bash
cva6 respaldo
cva6 respaldo --ejecutar
cva6 respaldo --incluir-placa --ejecutar
```

El primer comando sólo prepara un manifiesto local. El respaldo real usa el SSH conocido `nacho@192.168.86.31`, directorios nuevos bajo `/home/nacho/backups/CVA6`, staging privado y verificación completa por SHA256 antes de publicar. Conserva todos los originales locales. No usa `--delete` ni elimina fuentes.

Por defecto incluye automatización, documentación, entrega actual, estados recientes y el FSBL91 con sus pruebas de generación. `--incluir-placa` añade los paquetes de hardware25/91 y el build FSBL91 completo. No incluye la instalación Xilinx ni todas las campañas históricas; el manifiesto detalla exactamente el alcance.

Para reintentar un respaldo interrumpido, repetir el mismo comando con `--salida CARPETA_ANTERIOR`. El snapshot y manifiesto deben seguir siendo los mismos. Si cambiaron las fuentes, usar una salida nueva. Nunca borrar locks para forzar una segunda ejecución.

## Segundo plano, logout y recuperación

```bash
cva6 verificar --segundo-plano
cva6 respaldo --incluir-placa --ejecutar --segundo-plano
cva6 ensayo --frecuencia 91 --con-ila --ejecutar --segundo-plano
```

Se crea un servicio de usuario con nombre `cva6-ops-...`; la salida muestra unidad, log y carpeta de resultados. Con `linger` habilitado puede continuar después de logout. Suspensión, apagado, pérdida de USB/red, falta de disco u OOM pueden interrumpirlo. Después de reinicio no se reprograma la placa automáticamente: consultar el estado y elegir una operación nueva o reintentar sólo el respaldo inmutable.

```bash
cva6 estado
systemctl --user status NOMBRE.service
journalctl --user -u NOMBRE.service
```

Los logs también están en `operacion/cva6_ops/jobs/NOMBRE/service.log`. `result.json` y los resultados de cada etapa distinguen PASS, FAIL, READY, PLANNED y ERROR. Un plan no equivale a ejecución; un build PASS no equivale a PASS de hardware. Una operación de placa interrumpida se inspecciona antes de volver a programar; no se reintenta sola.

## Límites y documentación

No lanza campañas de timing, no cambia el CPU/BootROM ni carga aplicaciones nuevas en DDR. La programación JTAG sólo sucede con `--ejecutar`. La preparación de FSBL compila exclusivamente software nuevo del PS. Los reportes originales y los paquetes conocidos buenos permanecen donde estaban.

Entrar directamente a `/home/nachofalchi/data/fpga-work/cva6-equipo`. Consultar la guía `../PARA_PLACA_CON_GONZA_20261030.md` y `cva6 plan-bootrom`. Para salida estructurada usar `cva6 --json COMANDO`. Las pruebas offline simulan errores, clocks, identidad de archivos, sesiones, locks y respaldos; no reemplazan la primera prueba con la placa real.
