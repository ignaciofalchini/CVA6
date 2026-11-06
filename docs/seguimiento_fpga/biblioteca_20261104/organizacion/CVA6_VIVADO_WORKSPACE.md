# CVA6 Vivado Workspace

## 1. Objetivo

Preparar una copia separada del repo CVA6 para ejecutar mas adelante el flujo FPGA oficial con `BOARD=genesys2`, usando la particion ext4 `/home/nachofalchi/data`.

## 2. Estado del repo original

- Ruta: `/home/nachofalchi/cva6-work/cva6`
- Commit: `d1b0237f8e28a16d5c761159dea903129ec8c3f7`
- Estado git: limpio
- Toolchain RISC-V: `/home/nachofalchi/cva6-work/riscv-toolchain`
- Verilator custom: `/home/nachofalchi/cva6-work/cva6/tools/verilator`
- Spike custom: `/home/nachofalchi/cva6-work/cva6/tools/spike`

## 3. Estado del repo copiado

- Ruta: `/home/nachofalchi/data/fpga-work/cva6-vivado`
- La carpeta ya existia y fue verificada; no se sobrescribio.
- Rama: `master`
- Commit: `d1b0237f8e28a16d5c761159dea903129ec8c3f7`
- Estado git: limpio
- Submodulos: presentes segun `git submodule status --recursive`
- Tamano de la copia: `7.9G`

## 4. Particion y espacio disponible

- Montaje: `/home/nachofalchi/data`
- Dispositivo: `/dev/nvme0n1p6`
- Tipo: `ext4`
- UUID: `617f9838-2df0-4642-b0b4-ba80b9d67c51`
- Espacio reportado por `df -hT`: `73G` totales, `7.9G` usados, `61G` libres, `12%` usado
- Permisos: escritura y borrado probados correctamente en `/home/nachofalchi/data/fpga-work`

## 5. Entorno reutilizable

Archivo creado:

```bash
/home/nachofalchi/data/fpga-work/cva6-vivado-env.sh
```

Uso:

```bash
source /home/nachofalchi/data/fpga-work/cva6-vivado-env.sh
```

Variables principales:

- `CVA6_REPO=/home/nachofalchi/data/fpga-work/cva6-vivado`
- `CVA6_ORIGINAL_REPO=/home/nachofalchi/cva6-work/cva6`
- `RISCV=/home/nachofalchi/cva6-work/riscv-toolchain`
- `NUM_JOBS=4`
- `VERILATOR_INSTALL_DIR=/home/nachofalchi/cva6-work/cva6/tools/verilator`
- `SPIKE_INSTALL_DIR=/home/nachofalchi/cva6-work/cva6/tools/spike`
- `CVA6_FPGA_WORK=/home/nachofalchi/data/fpga-work`

Prueba de entorno:

- `RISCV_CC=/home/nachofalchi/cva6-work/riscv-toolchain/bin/riscv-none-elf-gcc`
- `which verilator=/home/nachofalchi/cva6-work/cva6/tools/verilator/bin/verilator`
- `verilator --version`: `Verilator 5.008 2023-03-04 rev v5.008 (mod)`

## 6. Target FPGA elegido

- BOARD: `genesys2`
- XILINX_PART: `xc7k325tffg900-2`
- XILINX_BOARD: `digilentinc.com:genesys2:part0:1.1`
- CLK_PERIOD_NS: `20`
- Constraints: `corev_apu/fpga/constraints/genesys-2.xdc`
- Header: `corev_apu/fpga/src/genesysii.svh`
- Top-level: `ariane_xilinx`

Referencias verificadas:

- `Makefile`: define `BOARD ?= genesys2`
- `corev_apu/fpga/scripts/run.tcl`: agrega `constraints/genesys-2.xdc` y lee `src/genesysii.svh` cuando `BOARD=genesys2`
- `corev_apu/fpga/src/ariane_xilinx.sv`: contiene `module ariane_xilinx`

## 7. Estado de Vivado

- Vivado no esta en `PATH`.
- `vivado -version` devuelve `command not found`.
- Falta instalar/configurar Vivado.
- Ruta futura recomendada de instalacion: `/home/nachofalchi/data/fpga-work/Xilinx`
- Workspace futuro de build: `/home/nachofalchi/data/fpga-work/cva6-vivado`

## 8. Dry-run de Makefile

Log:

```bash
/home/nachofalchi/data/fpga-work/logs/fpga_genesys2_make_dryrun.log
```

Resultado:

- Un primer intento sin entorno fallo porque `RISCV` no estaba exportado.
- El dry-run con `source /home/nachofalchi/data/fpga-work/cva6-vivado-env.sh` completo correctamente.
- No se ejecuto `make fpga` real.
- No se ejecuto Vivado.
- El dry-run muestra que el flujo futuro generaria bootrom, fuentes FPGA, IPs Xilinx y luego invocaria:
  - `vivado -nojournal -mode batch -source scripts/prologue.tcl -source scripts/run.tcl`
  - `vivado -nojournal -mode batch -source scripts/prologue.tcl -source scripts/write_cfgmem.tcl`

## 9. Proximo paso

Cuando Vivado este instalado y haya espacio suficiente:

```bash
source /home/nachofalchi/data/fpga-work/cva6-vivado-env.sh
cd /home/nachofalchi/data/fpga-work/cva6-vivado
make fpga BOARD=genesys2
```

No ejecutar todavia.
## 8. Intento FPGA oficial Genesys2

### Vivado

- Versión: `vivado v2026.1 (64-bit)`
- Ruta: `/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado`
- Espacio inicial: `/home/nachofalchi/data` está montado en `/`, `/dev/nvme0n1p5 ext4`, `187G` totales, `134G` usados, `43G` libres, `76%` usado
- Espacio final: `43G` libres; no se lanzó build real ni se generaron archivos grandes

### Target

- BOARD: `genesys2`
- XILINX_PART: `xc7k325tffg900-2`
- XILINX_BOARD: `digilentinc.com:genesys2:part0:1.1`
- Constraints: `corev_apu/fpga/constraints/genesys-2.xdc`
- Header: `corev_apu/fpga/src/genesysii.svh`
- Top-level: `ariane_xilinx`

### Dry-run

No ejecutado en esta fase. La precondición falló antes del dry-run: no existe el workspace indicado `/home/nachofalchi/data/fpga-work/cva6-vivado`.

### Comando real

No ejecutado.

Comando previsto:

```bash
time make fpga BOARD=genesys2 2>&1 | tee /home/nachofalchi/data/fpga-work/logs/fpga_genesys2_build_$(date +%Y%m%d-%H%M%S).log
```

### Resultado

Bloqueado antes de lanzar el flujo FPGA oficial.

Verificaciones realizadas:

- `df -hT /home/nachofalchi/data`: `43G` libres
- `df -hT /`: `43G` libres
- `source /home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/settings64.sh && which vivado && vivado -version`: OK
- `/home/nachofalchi/data/fpga-work/cva6-vivado-env.sh`: no existe
- `/home/nachofalchi/data/fpga-work/cva6-vivado`: no existe
- `/home/nachofalchi/data/fpga-work/vivado-env.sh`: existe, pero solo carga `settings64.sh`

### Outputs generados

No se generaron `.bit`, `.mcs`, reportes de síntesis/implementación ni logs de build.

### Logs relevantes

No se generó `fpga_genesys2_make_dryrun_after_vivado.log` ni `fpga_genesys2_build_*.log`, porque no se alcanzó la etapa de `make`.

### Errores, si hubo

Primer error real:

```text
/bin/bash: line 1: /home/nachofalchi/data/fpga-work/cva6-vivado-env.sh: No such file or directory
```

Además, el sandbox de comandos volvió a fallar en varias lecturas con:

```text
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

Las lecturas necesarias se repitieron fuera del sandbox.

### Conclusión

Vivado 2026.1 está instalado y ejecuta correctamente, pero el workspace Vivado indicado para esta fase no está presente en `/home/nachofalchi/data/fpga-work`. Por eso no corresponde correr `make -n fpga BOARD=genesys2` ni `make fpga BOARD=genesys2` todavía.

No parece un problema de RTL, constraints, Zynq, licencia, board files, Vivado 2026.1 o IP/MIG DDR3 en esta etapa. La causa probable es que el workspace y el archivo `cva6-vivado-env.sh` quedaron fuera de `data/fpga-work` después de la reorganización/backup.

Se encontró una copia limpia del workspace en:

```text
/home/nachofalchi/Downloads/backup-p6-data-20260709-163638/fpga-work/cva6-vivado
```

Esa copia está en commit `d1b0237f8e28a16d5c761159dea903129ec8c3f7`, con `git status --short` limpio, y contiene:

- `Makefile`
- `corev_apu/fpga/constraints/genesys-2.xdc`
- `corev_apu/fpga/src/genesysii.svh`

### Próximo paso

Restaurar o recrear `/home/nachofalchi/data/fpga-work/cva6-vivado` y `/home/nachofalchi/data/fpga-work/cva6-vivado-env.sh` antes de repetir la Fase 8. Con 43 GB libres, copiar el workspace de backup de alrededor de `7.9G` debería dejar margen suficiente para un dry-run, pero el build real de Vivado puede necesitar bastante más espacio; mantener el corte en `15G` libres.
### Reintento posterior a restauración del workspace

Fecha/hora del intento: `2026-07-09 22:20` hora local del sistema.

Precondiciones verificadas:

- Vivado: `/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/vivado`
- Versión: `vivado v2026.1 (64-bit)`
- Workspace: `/home/nachofalchi/data/fpga-work/cva6-vivado`
- Env: `/home/nachofalchi/data/fpga-work/cva6-vivado-env.sh`
- `CVA6_REPO=/home/nachofalchi/data/fpga-work/cva6-vivado`
- `RISCV=/home/nachofalchi/cva6-work/riscv-toolchain`
- `RISCV_CC=/home/nachofalchi/cva6-work/riscv-toolchain/bin/riscv-none-elf-gcc`
- HEAD: `d1b0237f8e28a16d5c761159dea903129ec8c3f7`
- Estado git inicial: limpio
- Espacio inicial: `43G` libres en `/home/nachofalchi/data`

Dry-run ejecutado:

```bash
make -n fpga BOARD=genesys2 | tee /home/nachofalchi/data/fpga-work/logs/fpga_genesys2_make_dryrun_after_restore.log
```

Resultado del dry-run: OK, código 0.

Log:

```text
/home/nachofalchi/data/fpga-work/logs/fpga_genesys2_make_dryrun_after_restore.log
```

Comando real ejecutado:

```bash
time make fpga BOARD=genesys2 2>&1 | tee /home/nachofalchi/data/fpga-work/logs/fpga_genesys2_build_20260709-222009.log
```

Resultado: falló, código 2.

Etapa alcanzada:

- Bootrom generado correctamente (`bootrom_64.sv`).
- Generación de lista de fuentes FPGA iniciada/completada por Makefile.
- Entrada a `corev_apu/fpga` para generación de bitstream.
- Falló al generar el primer IP Xilinx: `xlnx_axi_clock_converter.xci`.

Primer error real:

```text
ERROR: Vivado Design Suite cannot be launched because a valid license was not found. Visit the Vivado Licensing page to choose and generate the right license.
```

Contexto del fallo:

```text
Generating xlnx_axi_clock_converter.xci
cd xilinx/xlnx_axi_clock_converter && make clean && make
vivado -mode batch -source tcl/run.tcl
ERROR: Vivado Design Suite cannot be launched because a valid license was not found.
make[2]: *** [../common.mk:2: all] Error 42
make[1]: *** [Makefile:35: work-fpga/xlnx_axi_clock_converter.xci] Error 2
make: *** [Makefile:821: fpga] Error 2
```

Outputs generados:

- No se generaron archivos `.bit`.
- No se generaron archivos `.mcs`.
- `corev_apu/fpga/work-fpga`: `4.0K`.
- `corev_apu/fpga/ariane.runs`: no existe.

Logs relevantes:

```text
/home/nachofalchi/data/fpga-work/logs/fpga_genesys2_make_dryrun_after_restore.log
/home/nachofalchi/data/fpga-work/logs/fpga_genesys2_build_20260709-222009.log
```

Espacio final:

- `/home/nachofalchi/data`: `43G` libres, `76%` usado.

Estado git final:

- `git status --short`: limpio.

Conclusión:

El flujo oficial Genesys2 ya avanza más allá del dry-run y compila la bootrom, pero queda bloqueado por licencia de Vivado antes de generar IPs, síntesis, implementación o bitstream. No hay evidencia todavía de problema de RTL, constraints, board files, MIG DDR3, parte FPGA o Vivado 2026.1; el primer bloqueo efectivo es licencia.

Próximo paso recomendado:

Configurar una licencia válida para Vivado que permita lanzar los IP Tcl batch del flujo (`vivado -mode batch -source tcl/run.tcl`) y repetir `make fpga BOARD=genesys2` desde el mismo workspace. Mantener monitoreo de disco y frenar si baja de `15G` libres.

