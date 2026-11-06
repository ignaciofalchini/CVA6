# Reunión CVA6 KR260 del 30 de octubre de 2026

Leer primero [el resumen en PDF](../pdf/2026-10-30_Estado_reunion.pdf) o [el texto editable](../../reunion_20261030/RESUMEN_REUNION.md).

[evidencia_reunion_20261030.zip](/home/nachofalchi/data/fpga-work/entregas/reunion_profesor_20261030/evidencia_reunion_20261030.zip) reúne el PDF, tablas, investigación y reportes primarios. Es un paquete documental para explicar el resultado; no contiene los binarios necesarios para programar o reconstruir todo el proyecto.

El mensaje principal es cierre STA a 90,908MHz, con validación en placa pendiente. A100MHz sigue sin cerrarse setup. La prueba funcional previa documentada es de25MHz.

[Respaldo local y recuperación](/home/nachofalchi/data/fpga-work/backups/reunion_20261030/README_RECUPERACION.md). [Documentación central](/home/nachofalchi/data/fpga-work/cva6-equipo/docs/seguimiento_fpga/README.md).

La carpeta evidencia conserva nombres cortos y el manifiesto identifica las rutas originales relativas al workspace. Las rutas que aparecen dentro de los reportes y documentos históricos corresponden al workspace original. El PDF histórico de25/10 debe leerse junto al resumen actual y las aclaraciones, porque incluye conclusiones absolutas que no son una prueba de imposibilidad universal.

Todo este material está preparado localmente. No se envió ni compartió con terceros.

## Actualización posterior del respaldo

La transferencia a OpenClawd ya terminó y se verificaron 50 archivos por SHA256. [Recibo externo](../organizacion/RESPALDO_EXTERNO_20261029.md). Las menciones a copia externa pendiente en las capturas anteriores corresponden al estado previo a esta transferencia.

## Preparación final del 29 de octubre por la tarde

El resumen, PDF y ZIP se actualizaron después del respaldo externo y la limpieza adicional. El ZIP incorpora la guía para Gonza y el recibo externo. [Verificación documental actual](/home/nachofalchi/data/fpga-work/entregas/reunion_profesor_20261030/VERIFICACION_DOCUMENTAL_20261029_TARDE.json). Los informes de verificación anteriores conservan su fecha de corte. El FSBL de 90,9 MHz ya está compilado y verificado como software; la validación en placa sigue pendiente.

[Verificación de automatización del 29/10](/home/nachofalchi/data/fpga-work/entregas/reunion_profesor_20261030/VERIFICACION_AUTOMATIZACION_20261029.json): FSBL91 compilado y 68 pruebas offline aprobadas. El plan BootROM/DDR es documental. La prueba en placa sigue pendiente.

## Manual de prueba en placa

[Manual PDF de 90,9 MHz](../pdf/2026-10-30_Manual_placa_90_9MHz.pdf): vía automatizada, procedimiento manual XSDB/Vivado, comprobaciones y diagnóstico. [Comandos en texto](../placa/MANUAL_PLACA.txt). Preparado el 30/10/2026; no ejecuta hardware al generarse.

Manual ampliado: 26 páginas, conexión física, consolas, ejecución manual25/91, diagnóstico, preguntas de reunión y [rutas importantes](../placa/RUTAS_IMPORTANTES.txt).

Edición operativa: manual organizado en 12 pasos consecutivos y apéndices de consulta, con resultados esperados y criterios de parada.

Edición operativa: manual organizado en 12 pasos consecutivos y apéndices de consulta, con resultados esperados y criterios de parada.
