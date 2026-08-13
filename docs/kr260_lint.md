# Lint y comprobaciones RTL del port KR260

## Alcance y limitación

El target comprobado es `BOARD=kr260 target=cv64a6_imafdc_sv39`, con XLEN=64, el mismo orden de fuentes e include paths usados por la síntesis validada. No se cambió RTL para silenciar reglas estilísticas.

No hay un linter dedicado instalado. Por lo tanto, el resultado de esta fase es **PARTIAL**: `xvlog` y `synth_design -rtl` comprueban preprocesado, sintaxis, tipos, resolución de módulos, anchos y elaboración, pero no reemplazan el análisis de Verilator `--lint-only`, Verible o Slang.

## Herramientas detectadas

La búsqueda inicial fue:

```sh
command -v verible-verilog-lint
command -v verilator
command -v slang
command -v iverilog
command -v xvlog
```

Ninguna apareció en el `PATH`. Luego se inspeccionó la instalación local de Vivado y se encontró:

- Vivado 2026.1, build 6511674.
- `/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/xvlog`.
- No se encontró Verible, Verilator, Slang ni Icarus dentro de la instalación local consultada.
- No se descargó ni instaló software.

## Flujo reproducible

Primero se genera un proyecto temporal y se deja que Vivado resuelva el orden real de compilación. El script exporta ese orden y ejecuta elaboración RTL, con un único hilo:

```sh
cd corev_apu/fpga
mkdir -p ../../reports/kr260_next_steps/lint
XILINX_PART=xck26-sfvc784-2LV-c \
XILINX_BOARD=xilinx.com:kr260_som:part0:2.0 \
KR260_LINT_REPORT_DIR=../../reports/kr260_next_steps/lint \
/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/vivado \
  -mode batch -nojournal \
  -log ../../reports/kr260_next_steps/lint/vivado_rtl_elaboration.log \
  -source scripts/run_kr260_lint.tcl
```

Después se compila la misma lista como una sola unidad SystemVerilog. Esto conserva los macros que el flujo histórico comparte mediante `rvfi_types.svh` y `axi/{assign,typedef}.svh`:

```sh
/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/xvlog --sv \
  -i vendor/pulp-platform/common_cells/include \
  -i vendor/pulp-platform/axi/include \
  -i core/cache_subsystem/hpdcache/rtl/include \
  -i corev_apu/register_interface/include \
  -i core/include \
  -f reports/kr260_next_steps/lint/kr260_xvlog.f \
  --log reports/kr260_next_steps/lint/xvlog.log
```

Las rutas del segundo comando se muestran desde la raíz del repositorio. Conviene ejecutarlo en un directorio temporal para que `xsim.dir` y `xvlog.pb` no ensucien el árbol de fuentes.

## Resultado

- `xvlog`: SUCCESS; 247 archivos, 0 errores, 0 critical warnings y 0 warnings.
- `synth_design -rtl`: SUCCESS; 0 errores, 0 critical warnings y 327 warnings.
- Top elaborado: `ariane_kr260`.
- Parte: `xck26-sfvc784-2LV-c`.
- Black boxes inesperados: 0.

Durante elaboración aparecen tres instancias `unread`. Son módulos intencionales de una entrada y ninguna salida que absorben señales para evitar avisos de pines abiertos. La síntesis completa previa los elimina y termina con cero black boxes; el script sólo permite referencias `unread*` y falla ante cualquier otra black box.

## Clasificación de diagnósticos

### Errores reales

No se encontraron errores de sintaxis, tipos, resolución de módulos, puertos ni anchos en la pasada final.

### Warnings funcionalmente relevantes

Vivado informó 22 casos `Synth 8-3848` de nets sin driver y seis `Synth 8-3936` de registros internos recortados. Los ejemplos están en PTW/MMU, load unit, CLINT y lógica interna del core. Ya aparecen al elaborar el diseño existente y no apuntan a `ariane_kr260.sv`; deben considerarse deuda RTL preexistente si en el futuro se habilitan las funciones asociadas, pero no justifican cambios locales al port.

### Warnings esperados de integración

Los grupos repetidos `Synth 8-7129`, `8-7137` y `8-693` corresponden principalmente a bits o puertos sin carga en módulos genéricos: bits altos de dirección de la bootrom, campos AXI que `axi2mem` no consume y variantes parametrizadas. Vivado limita a 100 la impresión de algunos grupos. Son coherentes con la síntesis mínima ya validada y no se ocultaron.

### Warnings de herramienta o estilo

Los cuatro `Synth 8-11067` y un `8-11065` indican que Vivado trata ciertos parámetros de package o de listas formales como `localparam`. Son preexistentes y no se modificó RTL para evitarlos. Dos `filemgmt 56-315` ocurren durante el escaneo preliminar de fuentes; la elaboración posterior resuelve correctamente el diseño.

### Warnings propios del wrapper KR260

No hay warnings cuya ubicación sea `corev_apu/fpga/src/ariane_kr260.sv` en el log final.

## Evidencia generada

Los logs y listados reproducibles quedan bajo `reports/kr260_next_steps/lint/`:

- `vivado_rtl_elaboration.log`
- `xvlog.log`
- `compile_order.rpt`
- `kr260_xvlog.f`
- `rtl_blackboxes.rpt`

## Pendiente

Para completar un lint dedicado todavía hace falta disponer, sin instalación global, de al menos una de estas herramientas:

- Verilator y ejecutar `--lint-only` con la configuración `cv64a6_imafdc_sv39`.
- Verible sobre el wrapper KR260, los wrappers de debug/sistema y los archivos FPGA nuevos.
- Slang como frontend SystemVerilog adicional.

Hasta entonces este estado debe leerse como “RTL compilable y elaborable por Vivado”, no como “lint exhaustivo limpio”.
