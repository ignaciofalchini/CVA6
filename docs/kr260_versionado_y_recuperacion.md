# KR260: estado versionado y recuperación

## Alcance del estado del 11/09/2026

Vivado 2026.1, top `ariane_kr260_debug`, placa KR260. La variante activa usa BRAM de 8 KiB, no DDR del PS, aunque se conservan nombres históricos como `ariane_kr260_ps_bd` e `i_ps_ddr`.

Se observó en hardware la ejecución del bucle de la ROM de prueba y un tramo de 54 escrituras consecutivas (datos 537 a 590), todas con respuestas OKAY y AWID=BID=1. Eso no valida todo el procesador: quedan pendientes lectura y comparación de RAM, capturar el recorrido completo y su reinicio, y resolver la descarga intermitente de capturas ILA. El JTAG consultado estaba a 15 MHz; la reducción propuesta no se aplicó.

## Qué guardar en Git

- RTL, restricciones, scripts y documentación.
- `corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr`: proyecto guardado, fuentes y estrategias, incluida `Performance_ExplorePostRoutePhysOpt`.
- BD activo: `corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.srcs/sources_1/bd/ariane_kr260_ps_bd/ariane_kr260_ps_bd.bd`.
- Los dos XCI de BRAM/controlador bajo ese BD y los XCI de ILA/VIO bajo `corev_apu/fpga/ip/kr260_debug/`. Se conserva la configuración, no los productos generados.
- `memory_test.S`, su Makefile/linker y el SV generado `bootrom_kr260_memory_test.sv`: se guarda la imagen RTL exacta que necesita el proyecto. Al cambiar el assembly, regenerar el SV y revisar/versionar ambos juntos.
- `bootrom_64.sv`: ROM normal también referenciada por el XPR, pero marcada AutoDisabled. No es la ROM activa de este top.

No versionar `.runs`, `.gen`, `.cache`, `.hw`, `.ip_user_files`, DCP, BIT, LTX, capturas, ZIP de Archive ni backups históricos. Las reglas locales de `.gitignore` no borran esos archivos. El backup completo conserva los productos actuales y los auxiliares no seleccionados para este cambio.

## Recuperar desde Git

1. Obtener el repositorio manteniendo su estructura y los submódulos, con Vivado 2026.1 disponible. Git no instala Vivado, las licencias ni toolchains.
2. Abrir el XPR indicado. Sus fuentes e includes usan rutas relativas al proyecto; el atributo superior `Project Path` conserva la ubicación original guardada por Vivado. No editar el XPR de la sesión activa a mano para cambiarla.
3. Regenerar los Output Products de las IP/BD y el HDL Wrapper del BD, administrado por Vivado. El wrapper pertenece a `.gen` y no se incluye en Git. La configuración ILA debe tener 21 probes y probe20 de 20 bits.
4. El XPR conserva referencias a un checkpoint incremental y al estado de runs de la máquina original. Esos resultados no están en Git. En la copia recuperada, si Vivado señala un checkpoint faltante, quitar esa referencia/desactivar su uso incremental y ejecutar síntesis completa. No asumir que la indicación de un run completado implica que existe su resultado.
5. Comprobar que la jerarquía se elabora, regenerar síntesis e implementación, y usar BIT y LTX de la misma ejecución.

El script `run_kr260_debug_synth.tcl` abre el XPR guardado y necesita sus IP preparadas; no es un recreador completo de proyecto desde cero. No usar scripts históricos de VC707 ni `create_kr260_ps_ddr_bd.tcl` para reemplazar el BD BRAM de esta variante.

Las verificaciones de preparación de Git son estáticas (dependencias, formatos, parámetros e índice). No se ejecutó una nueva síntesis ni se probó una instalación limpia de Vivado. Para transferir ahora un proyecto con resultados ya generados, usar además el ZIP producido por Archive Project.

## Artefactos de referencia fuera de Git

Bitstream del 10/09/2026, 22:32; timing post-route con WNS +11,854 ns y WHS +0,012 ns. SHA-256:

- `ariane_kr260_debug.bit`: `4c689722427883c2109d540431f71f6922b66466c50201b9a2b5e03a4001599f`
- `ariane_kr260_debug.ltx`: `631d7647e8ebf6133d18e8c87324dcfd89f2f46c93f83b3a5e8da06eda58ecd1`

El backup completo previo a la preparación de Git es `cva6-kr260_2026-09-11_11-15-55/cva6-equipo_completo.tar.gz`, de 1.408.686.469 bytes. SHA-256: `f6741834451dd785da10be4cbb7e36d694d20dc1de404d064fd8ed29194e3a04`. Preservar una copia fuera del disco de trabajo. Ese backup no incluye las nuevas reglas de Git ni este documento, creados después.
