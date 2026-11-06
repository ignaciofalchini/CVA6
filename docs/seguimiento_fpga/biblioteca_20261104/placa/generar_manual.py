from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
import textwrap,hashlib
base=Path('/home/nachofalchi/data/fpga-work'); out=base/'entregas/reunion_profesor_20261030/manual_placa';out.mkdir(exist_ok=True)
for n,f in [('Sans','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(n,'/usr/share/fonts/truetype/dejavu/'+f))
pages=[]
def page(title, intro, code='',after=''):pages.append((title,intro,code,after))
page('01 / Guía de prueba CVA6 - KR260', '''Manual local de arranque, diagnóstico y timing. 30 de octubre de 2026.
Objetivo: probar el bitstream cerrado a 90,908180 MHz, sin modificar CVA6 ni BootROM. El alias de comandos es 91; no significa 91 MHz exactos.
Estado: 25 MHz tiene validación funcional histórica. 90,9 MHz tiene timing cerrado y FSBL compilado; su primera validación en placa sigue pendiente.
STA a 90,9 MHz: WNS +0,001 ns; TNS 0; WHS +0,004 ns. El margen de setup es mínimo. Un PASS de placa no sustituye STA ni una validación completa del procesador.
Contenido: 02 automatización; 03 archivos/herramientas; 04 XSDB; 05 preparación; 06 comprobaciones; 07 ILA; 08 ejecución; 09 diagnóstico; 10 timing y referencias.
Llevar: notebook con cargador, KR260, fuente y USB de datos/JTAG. Las herramientas y archivos están locales.
La aplicación ARM escribe patrones en DDR y luego libera CVA6. Esta prueba borra contenido de esas zonas; no es un cargador de programas propios.
No ejecutar la vía manual y la automatizada a la vez. No volver a programar ni resetear entre armar ILA y liberar CVA6. Abrir Hardware Manager no programa por sí solo.''')
page('02 / Camino automatizado', '''Abrir una terminal Linux. Estos comandos funcionan desde cualquier directorio con el wrapper en PATH. Si “cva6” no existe, usar la ruta completa indicada debajo.
Con la placa encendida y conectada, repetir primero 25 MHz. Si falla, resolver el entorno antes de intentar 90,9 MHz.''', '''cva6 estado
cva6 verificar
cva6 ensayo --frecuencia 25 --ejecutar
cva6 ensayo --frecuencia 91 --con-ila --ejecutar

# Si el comando no aparece en PATH:
/home/nachofalchi/.local/bin/cva6 verificar
/home/nachofalchi/.local/bin/cva6 ensayo \\
  --frecuencia 91 --con-ila --ejecutar

# Plan sin tocar hardware:
cva6 ensayo --frecuencia 91 --con-ila
''', '''ensayo coordina FSBL, BIT, reset, aplicación y captura. Sin --ejecutar sólo planifica. verificar comprueba archivos; no valida la placa.
Con ILA, PASS requiere aplicación PASS y captura con muestras. READY sólo significa preparado; CAPTURED sólo significa captura obtenida.
La salida indica una carpeta nueva bajo /home/nachofalchi/data/fpga-work/operacion/cva6_ops/. Conservar result.json, console.log, hardware_status.tsv, plan.json, manifest.json y capture.csv de sus etapas.
Si hay errores, detenerse e inspeccionar los logs. No borrar locks para forzar ejecuciones. La vía manual siguiente es independiente del wrapper, pero usa los mismos archivos.''')
page('03 / Archivos y programas', '''Rutas canónicas en esta computadora. En las páginas siguientes se usan variables para evitar copiar rutas largas. En Tcl usar file join; en Bash, variables de shell. No intercambiar sintaxis.
Programas: terminal Linux para iniciar XSDB y servidor; Vivado para Hardware Manager e ILA; XSDB para FSBL/aplicación y memoria. No hace falta abrir el IDE de Vitis ni recompilar.''', '''# Terminal Linux (Bash):
CVA6_BASE=/home/nachofalchi/data/fpga-work
CVA6_TOOLS="$CVA6_BASE/Xilinx/2026.1"
"$CVA6_TOOLS/Vitis/bin/xsdb"

# En otra terminal, SOLO si no hay hw_server activo:
/home/nachofalchi/data/fpga-work/Xilinx/2026.1/\\
Vivado/bin/hw_server
''', '''Hardware Manager puede iniciar hw_server local. No lanzar dos servidores para el mismo puerto 3121. Mantener abierta la terminal del servidor.
Paquete BIT/LTX/DCP: cva6-equipo/corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/ bajo la base.
FSBL91: operacion/cva6_ops/fsbl91/build_20261029_1831/kr260_fsbl_91mhz_patched.elf.
Aplicación ARM: known_good_2026-09-18/kr260_app_jtag.elf dentro del mismo kr260_ps_boot. Reutilizarla es intencional: no es el firmware RISC-V.
El XSA describe hardware para generar FSBL. No se programa como un BIT. El DCP permite analizar timing; no hace falta abrirlo para programar la placa.''')
page('04 / XSDB: seleccionar archivos y placa', '''Abrir XSDB con el comando de la página 03. Todo el bloque siguiente se ejecuta en el prompt xsdb%, no en Bash ni en la consola de Vivado.
Conectar una sola KR260. El selector exige un único target con el nombre exacto. Si hay varias placas, desconectar las otras o revisar su identidad antes de continuar.''', '''set base /home/nachofalchi/data/fpga-work
set boot [file join $base cva6-equipo corev_apu fpga \\
    software kr260_ps_boot]
set pkg [file join $boot timing_closed_91mhz_2026-10-22]
set bit [file join $pkg kr260_top.bit]
set fsbl [file join $base operacion cva6_ops fsbl91 \\
    build_20261029_1831 kr260_fsbl_91mhz_patched.elf]
set app [file join $boot known_good_2026-09-18 \\
    kr260_app_jtag.elf]
foreach p [list $bit $fsbl $app] {
    if {![file isfile $p]} {error "Falta archivo: $p"}
}
proc sel {name} {
    set f [format {name == "%s"} $name]
    set ts [targets -target-properties -filter $f]
    if {[llength $ts] != 1} {error "Target ambiguo: $name"}
    set t [lindex $ts 0]
    puts $t
    targets [dict get $t target_id]
}
connect -url tcp:127.0.0.1:3121
after 4000
targets
sel PSU
''', '''Revisar la lista y el cable serial que imprime sel. El ARM seleccionado será Cortex-A53 #0; no el CVA6 RISC-V. Si cualquier comando devuelve error, no pegar el bloque siguiente a ciegas.''')
page('05 / Preparar PS, DDR y bitstream', '''Continuar en la misma sesión XSDB. Esta es la secuencia exacta de la plantilla actual: reset de sistema, FSBL, bitstream, FSBL otra vez, reset de A53. CVA6 queda retenido en reset por el FSBL parcheado.
Corrección respecto de la explicación abreviada: el FSBL se ejecuta DOS veces, no sólo antes de programar PL.''', '''# Seleccionar arranque JTAG volátil y resetear sistema.
sel PSU
mwr 0xffca0010 0x0
mwr 0xff5e0200 0x0100
rst -system
after 4000

# Primera ejecución de FSBL.
sel {Cortex-A53 #0}
rst -processor
after 1500
dow -force $fsbl
con
after 15000
stop

# Programar el BIT cerrado (no el de impl_1).
sel PSU
fpga -f $bit
after 3000

# Segunda ejecución de FSBL tras configurar PL.
sel {Cortex-A53 #0}
rst -processor
after 1500
dow -force $fsbl
con
after 15000
stop
rst -processor
after 1500
''', '''No hace falta Program Device en Vivado si ya se ejecutó fpga -f. Reprogramar ahora por otra vía invalida la preparación y obliga a repetirla. Los tiempos after están expresados en milisegundos. No liberar todavía CVA6 si se desea capturar el arranque.''')
page('06 / Verificar la preparación', '''Continuar en XSDB con A53 seleccionado. Este bloque comprueba clock, reset, PL configurada, DDR en modo normal y HP0 a 64 bits. Ante un error, detenerse antes de cargar la aplicación.''', '''proc rd32 {a} {
    return [expr {[lindex [mrd -value $a 1] 0] & 0xffffffff}]
}
proc rd64 {a} {
    set w [mrd -value $a 2]
    if {[llength $w] != 2} {error "Lectura incompleta"}
    return [expr {([lindex $w 0] & 0xffffffff) | \\
        (([lindex $w 1] & 0xffffffff) << 32)}]
}
set pl0 [rd32 0xff5e00c0]
puts [format "PL0_REF_CTRL=0x%08x" $pl0]
if {($pl0 & 0x013f3f07) != 0x01010b00} {
    error "Clock distinto de IOPLL/11"
}
set g [rd32 0xff0a0054]
set d [rd32 0xff0a0344]
set o [rd32 0xff0a0348]
if {($g & 0x80000000) != 0 || \\
    ($d & 0x80000000) == 0 || ($o & 0x80000000) == 0} {
    error "CVA6 no esta retenido en reset"
}
if {([rd32 0xffca3010] & 8) == 0} {
    error "PL sin configurar"
}
if {([rd32 0xfd070004] & 7) != 1} {
    error "DDR fuera de modo normal"
}
foreach a {0xfd380000 0xfd380014} {
    if {([rd32 $a] & 3) != 1} {error "HP0 no es 64 bits"}
}
puts "PREPARACION OK; aun no es PASS funcional"
''', '''El registro de clock confirma configuración, no mide la frecuencia físicamente. Para 25 MHz se usan BIT/LTX/FSBL del paquete conocido y el valor de comparación 0x01012800, no el valor91. No mezclar frecuencias.''')
page('07 / Vivado: armar captura ILA', '''Ahora abrir Hardware Manager en Vivado: Flow > Open Hardware Manager; Open Target > Auto Connect. Elegir la misma placa. No pulsar Program Device: XSDB ya programó el BIT.
Seleccionar el dispositivo y asociar kr260_top.ltx del paquete91 en sus propiedades de probes; luego Refresh Device. Debe aparecer un único ILA. En Trigger Setup seleccionar m_debug_commit_valid, comparación == 1, modo básico. Pulsar Run Trigger ANTES de la página 08.
Alternativa reproducible: pegar lo siguiente en Tcl Console de VIVADO después de conectar el target; no en XSDB. Este bloque arma pero no espera, para dejarte ir a XSDB.''', '''set base /home/nachofalchi/data/fpga-work
set pkg [file join $base cva6-equipo corev_apu fpga \\
    software kr260_ps_boot timing_closed_91mhz_2026-10-22]
set ds [get_hw_devices]
if {[llength $ds] != 1} {error "Dispositivo ambiguo"}
set dev [lindex $ds 0]
current_hw_device $dev
set_property PROBES.FILE [file join $pkg kr260_top.ltx] $dev
refresh_hw_device $dev
set cores [get_hw_ilas -of_objects $dev]
if {[llength $cores] != 1} {error "ILA ausente/ambiguo"}
set ila [lindex $cores 0]
set p [get_hw_probes m_debug_commit_valid -of_objects $ila]
if {[llength $p] != 1} {error "Probe ausente/ambiguo"}
reset_hw_ila $ila
set_property CONTROL.TRIGGER_MODE BASIC_ONLY $ila
set_property CONTROL.TRIGGER_CONDITION AND $ila
set_property CONTROL.CAPTURE_MODE ALWAYS $ila
set_property TRIGGER_COMPARE_VALUE eq1'b1 $p
run_hw_ila $ila
''', '''El ILA debe quedar esperando el trigger. A continuación ejecutar la página 08 en XSDB; después volver a Vivado para descargar la captura. Si no se desea ILA, omitir esta página: sólo se evaluará el resultado por memoria.''')
page('08 / Ejecutar y guardar evidencia', '''Volver a la MISMA sesión XSDB, sin resetear ni reprogramar. El ARM ya está detenido. La aplicación prueba DDR y libera el CVA6. Lecturas de 64 bits: dos palabras de 32 bits, menor primero.''', '''for {set off 0} {$off < 32} {incr off 4} {
    mwr [expr {0x800004000 + $off}] 0
}
sel {Cortex-A53 #0}
dow -force $app
con
after 20000
stop
set deadline [expr {[clock milliseconds] + 30000}]
set s [rd64 0x800004000]
while {$s == 0 && [clock milliseconds] < $deadline} {
    after 500
    set s [rd64 0x800004000]
}
foreach a {0x800004000 0x800004008 0x800004010 0x800004018} {
    puts [format "0x%x = 0x%016x" $a [rd64 $a]]
}
puts [format "GPIO=0x%08x" [rd32 0xff0a0054]]
''', '''PASS: STATUS0=1, STATUS8=0, STATUS16=0, STATUS24=0 y GPIO bit31=1 (reset liberado). STATUS0=0xffffffffffffffff indica fallo de comparación; guardar los otros tres registros. STATUS0=0 o distinto de PASS no acredita éxito.
Volver a Vivado Tcl Console para guardar ILA en una carpeta nueva:''')
# append capture code separately on next page for clean layout
page('09 / Captura y diagnóstico', '''En VIVADO Tcl Console, después de lanzar la aplicación. El tiempo de espera está en minutos. $ila proviene de la página 07. Si usaste sólo la UI, seleccioná el ILA exacto o ejecutá primero su selección por comandos.''', '''wait_on_hw_ila -timeout 2 $ila
if {[get_property CORE_STATUS $ila] ne "IDLE"} {
    error "Captura no completada"
}
set run [file join /home/nachofalchi/data/fpga-work \\
    operacion cva6_ops \\
    manual_[clock format [clock seconds] -format %Y%m%d_%H%M%S]]
if {[file exists $run]} {error "Salida ya existe"}
file mkdir $run
set data [upload_hw_ila_data $ila]
write_hw_ila_data -csv_file [file join $run capture.csv] $data
puts "Guardar tambien salida XSDB y archivos usados en: $run"
''', '''Guardar la salida de XSDB copiando la consola a un .txt nuevo, la de Vivado, CSV, BIT/LTX/FSBL/app usados y sus hashes. El CSV debe tener muestras. No sobrescribir evidencia histórica.
No conecta a localhost:3121: comprobar alimentación, USB de datos y hw_server. En Bash: lsusb; pgrep -af hw_server. No matar procesos ajenos ni usar sudo a ciegas.
Targets vacíos o ambiguos: ejecutar targets en XSDB y comprobar cable/placa; no elegir el primero arbitrariamente.
Fallo al cargar ELF o DDR: revisar FSBL91, estado del PS y controles de la página06. No sustituirlo por FSBL25.
ILA/probes no aparecen: comprobar BIT y LTX del mismo paquete, Refresh Device y clock/reset. No reprogramar después de armar la captura.
ILA sin trigger: comprobar que se armó ANTES de liberar CVA6. Una captura sola no demuestra PASS; revisar STATUS.
Error/timeout/logout: no continuar desde un paso incierto. Guardar evidencias; cerrar la sesión propia y repetir una preparación completa nueva cuando se confirme el estado. No hay recuperación automática de hardware.''')
page('10 / Timing, identidad y referencias', '''Para analizar timing, no hace falta conectar la placa. En Vivado: File > Checkpoint > Open; abrir kr260_top_91mhz_closed.dcp del paquete91. Luego Reports > Timing > Report Timing Summary > OK. Si aparece una opción de nueva ventana, dejarla desmarcada.
Para probar hardware no hace falta abrir el DCP ni el proyecto. Hardware Manager programa el BIT; la inicialización del PS/DDR se realiza con XSDB. El resultado de impl_1 no es el BIT cerrado seleccionado.
Verificación independiente del wrapper (Bash):''', '''CVA6_BASE=/home/nachofalchi/data/fpga-work
CVA6_BOOT="$CVA6_BASE/cva6-equipo/corev_apu/fpga/software"
CVA6_PKG="$CVA6_BOOT/kr260_ps_boot/timing_closed_91mhz_2026-10-22"
(cd "$CVA6_PKG" && sha256sum -c SHA256SUMS.txt)
sha256sum "$CVA6_BASE/operacion/cva6_ops/fsbl91/\\
build_20261029_1831/kr260_fsbl_91mhz_patched.elf"
''', '''SHA256 esperado del FSBL91 (unir las dos mitades):
4b2c98d7ea93099d62b7538ce4d92b071
d3672ef157b48acf7bf688df380ab87
El paquete91 debe verificar 29 archivos. El manifiesto histórico25 tiene una autoentrada incorrecta conocida; esto no autoriza ignorar fallos de los binarios.
Fuente operativa: automatizacion/cva6_ops/templates_board/board_run.tcl e ila_capture.tcl; board_ops.py, config.json y README.md. La secuencia de este manual se contrastó con esos archivos el 30/10/2026. No se ejecutó hardware al elaborar el manual.
Referencia AMD: docs.amd.com/r/en-US/conversion-methodology/Timing-Closure
Referencia ILA: docs.amd.com/r/2021.2-English/ug835-vivado-tcl-commands/run_hw_ila
El procedimiento manual no incluye los locks, la validación de identidad ni los registros automáticos completos de ensayo. Preferir la vía automatizada cuando funcione. Este manual no promete PASS ni modifica el CVA6.''')
# Expand the manual with physical setup, exact recovery and a professor appendix.
core=pages[:]
pages=[]
page('Antes de empezar / conexión física', '''1. Identificar que la placa sea KR260. Colocarla estable y mantener libre su ventilación. Tener a mano su fuente y un cable micro-USB de DATOS. La notebook debe tener cargador conectado.
2. Con la placa sin alimentar, identificar J4: micro-USB UART/JTAG. No confundirlo con los conectores USB host para periféricos. Conectar ahí el extremo micro-B del cable; conectar el otro extremo a la notebook.
3. Identificar J12, entrada de alimentación. Conectar la fuente adecuada de la placa y alimentarla. Comprobar los indicadores de alimentación. Si no hay indicación de encendido, no intentar solucionar por software.
4. En esta prueba JTAG no hace falta preparar una microSD, monitor, teclado ni Ethernet. No estamos ejecutando el tutorial de Linux ni arrancando un sistema operativo en CVA6.
5. No pulsar SW1/FWUEN: es el botón de actualización/recuperación de firmware, no el control del clock ni el selector habitual de esta prueba. No modificar jumpers o resistencias para esta guía. El script cambia el modo de arranque de forma volátil por registros.
6. Abrir una terminal y comprobar USB con los comandos de abajo. Registrar cualquier error. Que aparezca el puente USB no prueba todavía que JTAG pueda abrirse.
7. Si la placa estaba ejecutando Linux u otra aplicación, el reset de sistema de este procedimiento la interrumpe. No ejecutar dos pruebas simultáneas.
Fuente de identificación física: documentación AMD KR260, conexión J4/J12 y UG1092 Firmware Update; enlaces completos en el apéndice.''', '''lsusb
pgrep -af hw_server
# Espacio disponible y hora para identificar evidencia:
df -h /home/nachofalchi/data/fpga-work
date -Is
''', '''Si USB no aparece: revisar alimentación, otro puerto de la notebook y un cable de datos conocido. No asumir que encender LEDs significa tener un cable USB de datos. Si hay problemas de permisos, guardar el error exacto; no ejecutar Vivado como root ni instalar drivers sin diagnosticar.''')
page('Ventanas y consolas / no mezclarlas', '''Ventana A - terminal Linux: comandos como cva6, lsusb, sha256sum y arranque de herramientas. Prompt usual terminado en $. Las variables se definen NOMBRE=valor.
Ventana B - XSDB: se inicia desde la terminal. Su prompt es xsdb%. Aquí van connect, targets, rst, dow, con, stop, mrd, mwr y fpga. Es Tcl: variables con set nombre valor.
Ventana C - Vivado: menú Hardware Manager e ILA. Su pestaña Tcl Console usa Tcl, pero las órdenes son de Vivado: get_hw_devices, get_hw_ilas, run_hw_ila. No pegar estas órdenes en XSDB.
Ventana D - servidor opcional: hw_server, sólo si no había uno local escuchando. Mantenerlo abierto. Si Hardware Manager ya lo inició, reutilizarlo.
Abrir Vivado no requiere abrir un proyecto ni un DCP para acceder al hardware. Si ya está abierto, reutilizar la ventana. El menú Flow está arriba entre Edit y Tools.
No correr cva6 ensayo mientras se está realizando el procedimiento manual. Los locks de la automatización no pueden impedir acciones manuales desde otra herramienta.
En Bash se usa barra invertida al final de una línea para continuar el comando. Copiar el bloque entero. En XSDB los bloques con llaves deben copiarse completos; si aparece prompt de continuación, terminar el bloque, no pegar comandos de otro apartado.''', '''# Ventana A: iniciar Vivado sólo si no está abierto.
/home/nachofalchi/data/fpga-work/Xilinx/2026.1/\\
Vivado/bin/vivado

# Otra terminal: iniciar XSDB.
/home/nachofalchi/data/fpga-work/Xilinx/2026.1/\\
Vitis/bin/xsdb
''')
page('Hardware Manager / conexión paso a paso', '''1. En la ventana principal de Vivado seleccionar Flow > Open Hardware Manager. Si se está en la pantalla inicial, usar su entrada Open Hardware Manager.
2. En Hardware Manager seleccionar Open Target > Auto Connect. La herramienta intentará usar el servidor local y abrir el cable detectado.
3. Expandir la jerarquía del servidor/target/dispositivo en Hardware. Revisar que corresponda a la KR260 conectada. Conectar sólo una placa para evitar selección ambigua.
4. Si aparece “No hardware target”, revisar cable, alimentación y servidor. Anotar el mensaje exacto. No seguir hasta tener un target.
5. Si el dispositivo aparece pero todavía no aparecen ILA/VIO, no concluir que el diseño está roto: puede estar sin programar o faltarle clock. Completar FSBL -> BIT -> FSBL como indica el apartado de preparación.
6. Abrir el target no descarga el BIT y no ejecuta el FSBL. El botón Program Device únicamente configura PL; por sí solo no inicializa nuestro PS/DDR.
7. Para esta guía, programar con fpga -f desde XSDB. El menú Program Device es una alternativa para ese paso concreto, explicada más adelante. No usar ambas formas consecutivamente.
8. Mantener XSDB abierto mientras se usa Hardware Manager. Si una herramienta informa que el target está ocupado, dejar de repetir órdenes: comprobar qué otra sesión lo controla y cerrar sólo la conexión propia que no se esté usando.
A partir de aquí elegir una vía: la automatizada del apartado correspondiente, o la manual completa. Conectar el hardware por la UI no obliga a programar desde la UI.''')
# Original overview and automated path, then extra manual baseline.
pages.extend(core[:2])
page('Control de referencia / repetir 25 MHz a mano', '''Antes de atribuir un fallo a 90,9 MHz, repetir el conocido bueno25. Si la automatización funciona, basta su comando25. Si no funciona y se sigue la vía manual, usar la misma preparación de las páginas operativas con estos cambios de archivos.
En XSDB, tras definir base y boot del apartado de selección, reemplazar las variables así. No ejecutar primero la preparación91: elegir un perfil completo antes de empezar.''', '''set pkg [file join $boot known_good_2026-09-18]
set bit [file join $pkg kr260_top.bit]
set fsbl [file join $pkg kr260_fsbl_patched.elf]
set app [file join $pkg kr260_app_jtag.elf]
''', '''Seguir la secuencia de reset, FSBL, BIT, FSBL y A53 detenido exactamente igual. En la comprobación de PL0 sustituir sólo la comparación 0x01010b00 por 0x01012800 (IOPLL/40). Los controles DDR/HP0/reset y el criterio PASS se conservan.
En Vivado usar kr260_top.ltx del paquete conocido25, nunca el del91. Guardar evidencia en una carpeta nueva identificada como25.
Si25 da PASS, pasar a91 exige una preparación COMPLETA nueva con BIT, LTX y FSBL91; no basta con cambiar el divisor en caliente.
Atajo histórico sin ILA, en Bash, si se desea usar los scripts ya validados25: definir las variables de abajo y ejecutar ambas órdenes en orden. No usar estos scripts para91: contienen rutas25.''')
page('Scripts históricos25 / comandos completos', '''Este método es alternativa al procedimiento manual interactivo25. Reinicia el sistema, programa y ejecuta la prueba. No arma automáticamente una captura ILA antes del arranque; para capturar el inicio, usar la vía coordinada o el procedimiento interactivo.''', '''CVA6_BASE=/home/nachofalchi/data/fpga-work
CVA6_BOOT="$CVA6_BASE/cva6-equipo/corev_apu/fpga/software"
CVA6_KG="$CVA6_BOOT/kr260_ps_boot/known_good_2026-09-18"
CVA6_XSDB="$CVA6_BASE/Xilinx/2026.1/Vitis/bin/xsdb"
"$CVA6_XSDB" "$CVA6_KG/kr260_jtag_boot.xsdb"
# Ejecutar la siguiente sólo si la anterior no dio error:
"$CVA6_XSDB" "$CVA6_KG/kr260_jtag_run.xsdb"
''', '''Resultado histórico esperado: STATUS0=1, STATUS8/16/24=0; GPIO_DATA5 bit31=1. Las lecturas históricas impresas con mrd son de32bits; el manual actual reconstruye los estados de64bits con rd64.
La captura histórica25 tuvo2048 muestras,26beats con AWVALID=1 y0 con ARVALID=1 dentro de esa ventana. Eso acredita escrituras observadas, no que no existan lecturas: pueden quedar fuera de la ventana.
La reproducción no sobrescribe ni convierte automáticamente esa evidencia en una validación91. Etiquetar frecuencia, archivos y fecha de la nueva sesión.''')
pages.extend(core[2:7])
page('Program Device / alternativa sólo para el BIT', '''Si se prefiere el botón de Vivado, sustituir exclusivamente las líneas “sel PSU; fpga -f $bit; after 3000” de la preparación por estos pasos. Mantener el resto de la secuencia XSDB intacta.
1. Ejecutar en XSDB hasta finalizar la PRIMERA ejecución de FSBL (stop). No ejecutar todavía la segunda.
2. En Hardware Manager seleccionar el dispositivo de la misma placa; clic derecho > Program Device.
3. En Bitstream file seleccionar kr260_top.bit dentro del paquete timing_closed_91mhz_2026-10-22. Verificar toda la ruta: el nombre por sí solo no distingue experimentos.
4. En Debug probes file seleccionar kr260_top.ltx de ESA misma carpeta. No seleccionar un BIT de impl_1 ni del paquete25.
5. Pulsar Program y esperar que termine sin errores.
6. Volver a XSDB y continuar con la SEGUNDA ejecución de FSBL, reset final de A53 y comprobaciones de preparación.
7. Recién después refrescar los probes en Vivado, armar ILA y lanzar la aplicación con XSDB.
No pulsar Program Device después de preparar/armar ILA. Si se hizo, volver a empezar la preparación completa. No sustituir FSBL91 por un archivo de25 aunque Vivado acepte el BIT.
Esta alternativa usa exactamente los mismos artefactos, pero introduce acciones manuales adicionales. Para una reproducción fiel y menos ambigua, el método principal del manual programa con XSDB.''')
pages.extend(core[7:])
page('Guardar una sesión / evidencia desde el principio', '''Antes de abrir XSDB, se puede registrar toda su terminal con script (herramienta Linux). El comando inicia una subshell grabada. Dentro de ella iniciar XSDB y seguir los pasos. Al terminar escribir disconnect y exit en XSDB, luego exit en la subshell para cerrar el registro.
El log puede contener secuencias de control del terminal; se conserva como evidencia original. Las órdenes siguientes son Bash, no Tcl.''', '''CVA6_BASE=/home/nachofalchi/data/fpga-work
CVA6_RUN="$CVA6_BASE/operacion/cva6_ops/manual_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CVA6_RUN"
printf '%s\n' "$CVA6_RUN"
script -q -f "$CVA6_RUN/xsdb_terminal.log"
# Dentro de la subshell grabada:
/home/nachofalchi/data/fpga-work/Xilinx/2026.1/\\
Vitis/bin/xsdb
# Al terminar, en XSDB: disconnect ; exit
# Luego en la subshell: exit
''', '''Anotar en una nota de sesión: fecha/hora,25o91, número de cable, nombre de BIT/LTX/FSBL/app y resultado por registro. Guardar CSV en la carpeta de captura indicada por Vivado y anotar esa ruta en la nota. Si son dos carpetas, conservar ambas.
Antes de desconectar: esperar fin de descarga de captura, guardar logs y verificar que los archivos existen. Cerrar sólo las conexiones propias; apagar la placa al finalizar. Tras cortar alimentación, no asumir que persisten el BIT o el modo de arranque volátil: repetir preparación.
No se programa QSPI ni se crea BOOT.BIN mediante este procedimiento. No pulsar actualización de firmware para esta prueba.''')
page('Errores / decidir dónde detenerse', '''Falla verificar por hashes: no tocar hardware. Identificar el archivo que difiere y compararlo con el manifiesto congelado. Sólo la autoentrada histórica del manifiesto25 es una excepción documentada; ninguna diferencia de ELF/BIT/LTX se ignora.
Falta cva6: usar su ruta completa; si el wrapper falta también, los apartados XSDB/Vivado son independientes. No se necesita instalar otro compilador para ejecutar los ELF preparados.
Falta hw_server o puerto ocupado: pgrep -af hw_server permite ver procesos. Si ya hay uno local, reutilizarlo; si no, iniciarlo con la ruta del manual. No ejecutar killall ni borrar locks de la suite.
XSDB no encuentra Cortex-A53 #0: ejecutar targets y guardar la lista. Revisar PSU, cable y alimentación. El selector del manual exige un target exacto; no cambiar a otro procesador por ensayo y error.
Clock incorrecto: comprobar el FSBL elegido y si se ejecutó después del BIT. No escribir un divisor suelto para esconder el fallo. Repetir secuencia coherente.
Reset no retenido: no cargar app ni armar captura como si todo estuviera listo. Confirmar FSBL parcheado y registros GPIO. El VIO no debe cambiarse arbitrariamente.
STATUS0=0: puede ser que CVA6 no arrancó o no terminó. Revisar reset, clock, DDR, app y errores anteriores; no declarar fallo de timing automáticamente.
STATUS0=-1: conservar estados secundarios y captura; corresponde a un reporte de comparación fallida de la ROM de test.
PASS de memoria pero sin CSV: hay evidencia funcional parcial, pero no un ensayo completo con ILA. Repetir con preparación nueva y captura armada antes del release.
USB desconectado, logout o herramienta terminada: guardar lo que quedó; no adivinar el estado. La ruta segura de reproducción es preparar nuevamente, usando carpetas nuevas. Los comandos de hardware no se reintentan solos.''')
page('Preguntas del profe / estado y resultados', '''¿Qué se logró? Una implementación que cumple STA a90,908180MHz y un paquete reproducible para probarla. El conocido bueno25 tiene PASS funcional histórico. La validación hardware91 debe obtenerse y registrarse; no se puede dar por realizada.
¿100MHz cerró? No. El mejor resultado100 adoptado en la documentación tiene WNS -0,553ns, TNS -322,607ns y1285endpoints negativos. Consultar CSV de evaluaciones para el historial completo; no afirmar que se probaron todas las combinaciones posibles.
¿Por qué bajar a90,9? Hay un resultado completo con clock configurado por IOPLL/11 y STA cerrado. Bajar frecuencia amplía el tiempo disponible por ciclo. No demuestra que90,9 sea el máximo absoluto de cualquier implementación.
¿Hay margen? Setup+0,001ns y hold+0,004ns: cumple el análisis guardado, con margen muy pequeño. No venderlo como cierre holgado ni robustez funcional demostrada.
¿La placa ya corrió91? No según el estado documental al preparar este manual. FSBL compilado y bitstream existente no son una ejecución hardware.
¿El clock es91 exacto? No:90,908180MHz. El análisis usa período11ns del clock generado por el IP del PS. La lectura de divisor confirma configuración, no medición con instrumental.
¿Podemos garantizar100 mañana? No hay evidencia para garantizarlo. Un bitstream generado tampoco prueba por sí solo cierre de timing.
¿Está medido consumo, rendimiento o IPC? No con esta batería de cierre/bring-up. No presentar frecuencia como un benchmark de rendimiento.
Evidencia para responder: README del paquete91, reports/timing_summary.rpt, docs/seguimiento_fpga/evaluaciones_100mhz.csv y resultados_clave.csv.''')
page('Preguntas del profe / arquitectura y test', '''¿Qué hace PS y qué hace PL? El ARM del PS ejecuta FSBL y la app de preparación/prueba. El CVA6 está implementado en PL y accede a la DDR del PS a través del camino AXI/HP0 preparado.
¿El FSBL es el programa de CVA6? No: es ELF AArch64 del ARM. Inicializa PS/DDR/clock y retiene reset. La aplicación ARM también es distinta del código RISC-V de la BootROM de test.
¿Qué comprueba PASS? El resultado que escribe la ROM de test en memoria, estados secundarios sin diferencias y reset liberado; con ILA se exige además una captura. Es bring-up de ROM/DDR, no un test exhaustivo de ISA, Linux, caches o todos los periféricos.
¿Por qué escribir DDR desde ARM? Es parte del test existente y su preparación. Puede destruir programas precargados. No es el mecanismo definitivo para cargar aplicaciones propias.
¿Direcciones? La ventana CVA6 0x80000000-0xBFFFFFFF se traduce a PS 0x800000000-0x83FFFFFFF. El estado visto por CVA6 en0x80004000 aparece desde PS en0x800004000. Cuidado con el dígito extra.
¿UART? Esta demo no depende de UART: se leen estados por JTAG. No esperar mensajes serie como criterio de éxito.
¿ILA prueba todo? No. Observa una ventana finita y señales concretas; ausencia de lecturas en una ventana no prueba ausencia global. El trigger por commit no captura necesariamente todos los accesos DDR.
¿Se modificó CPU para este manual? No. No se cambian RTL, parámetros ni microarquitectura por preparar/ejecutar la guía. El proyecto ya contiene modificaciones de integración previas del equipo; no afirmar que todo el repositorio es idéntico al upstream.
¿Restaurar ROM original y cargar DDR ya está hecho? No. Es un plan documental separado. No usar instrucciones antiguas sobre macros como evidencia de selección actual: consultar la auditoría y el plan actualizados.''')
page('Preguntas del profe / timing y reproducibilidad', '''¿WNS? El slack peor de setup. Negativo implica al menos una restricción incumplida; positivo indica margen en el peor camino analizado. ¿TNS? Suma de slacks negativos; cero es el objetivo, junto a ausencia de endpoints fallando.
¿Hold? Restricción de llegada demasiado temprana. WHS es el peor slack de hold y THS acumula violaciones. Cerrar hold no compensa fallar setup.
¿Síntesis cerrada garantiza ruteo? No. El timing de síntesis usa estimaciones; colocación, ruteo y optimizaciones físicas determinan los retardos finales. Comparar siempre el post-route del experimento correcto.
¿75 endpoints JTAG? El paquete91 documenta75endpoints sin restricción asociados al tck de JTAG atado a0. Hay que mostrar check_timing.rpt y el contexto de integración; no decir “todo está restringido” ni confundirlos con endpoints funcionales de setup fallando.
¿Qué receta produjo91? Síntesis Vivado Synthesis Defaults; implementación Performance_ExploreWithRemap, route NoTimingRelaxation con tns_cleanup y phys_opt post-route Explore; una pasada AggressiveExplore sobre el ruteado llevó el resultado de WNS -0,065ns a+0,001ns. Ver scripts y logs del paquete para los comandos reales.
¿Cambiar directivas cambia el CPU? Cambia la realización netlist/física buscando preservar la función HDL; no se está editando la microarquitectura. Eso no sustituye pruebas de equivalencia o validación funcional completa.
¿El .xpr reproduce automáticamente el mejor resultado? No. El checkpoint y BIT congelados identifican el resultado final; impl_1 puede ser un estado previo. No regenerar encima durante la reunión.
¿Cómo se liga evidencia a binarios? Con SHA256, manifiestos, configuración del FSBL y carpetas por sesión. Conservar logs y CSV con los archivos exactos usados. Un nombre idéntico no prueba identidad.
¿Fmax=1/(11ns-1ps)? No usar esa cuenta como máximo certificado. El máximo depende de restricciones, incertidumbre, implementación y validación; sólo afirmar el punto analizado que efectivamente pasó.''')
page('Rutas importantes / proyecto y archivos de placa', '''Base real de todo el trabajo:
/home/nachofalchi/data/fpga-work
Las rutas que siguen son RELATIVAS a esa base; concatenarlas para obtener la ruta absoluta. No son accesos directos.
Proyecto y fuentes: cva6-equipo/
Proyecto Vivado: cva6-equipo/corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr
Software de arranque: cva6-equipo/corev_apu/fpga/software/kr260_ps_boot/
Paquete91: dentro del software de arranque, timing_closed_91mhz_2026-10-22/
BIT: paquete91/kr260_top.bit. Probes: paquete91/kr260_top.ltx.
Checkpoint cerrado: paquete91/kr260_top_91mhz_closed.dcp.
Hardware exportado: paquete91/kr260_cva6_91mhz.xsa.
FSBL91: operacion/cva6_ops/fsbl91/build_20261029_1831/kr260_fsbl_91mhz_patched.elf.
Identidad del build: en esa misma carpeta fsbl91_manifest.json y result.json.
Referencia25: software de arranque/known_good_2026-09-18/.
App ARM: referencia25/kr260_app_jtag.elf. FSBL25: referencia25/kr260_fsbl_patched.elf.
Automatización: automatizacion/README.md; config.json; cva6_ops/board_ops.py; cva6_ops/session_ops.py; cva6_ops/templates_board/.
Resultados nuevos: operacion/cva6_ops/. La salida de cada comando informa su subcarpeta.
No mover ni borrar paquetes congelados. Para abrir las carpetas desde Bash, usar las órdenes de la página final. Para evitar ambigüedad, el índice de rutas también se entrega como texto.''')
page('Rutas importantes / reportes y documentación', '''Dentro de paquete91/reports/:
timing_summary.rpt: métricas globales de setup/hold.
critical_setup.rpt y critical_hold.rpt: detalle de caminos críticos.
clocks.rpt: clocks reconocidos. pulse_width.rpt: ancho de pulso.
check_timing.rpt: advertencias de cobertura/restricciones.
route_status.rpt: estado de ruteo. drc.rpt: reglas de diseño.
methodology.rpt y bus_skew.rpt: verificaciones complementarias.
Dentro de paquete91/scripts/: Tcl y logs de creación del resultado cerrado.
Dentro de paquete91/project_state/: instantánea de XPR, BD, XCI y diff del proyecto de ese momento.
Documentación unificada: cva6-equipo/docs/seguimiento_fpga/README.md.
Estado y resultados: mismo directorio/estado_y_resultados.md.
Datos de campañas: evaluaciones_100mhz.csv; resultados_clave.csv; historial_pruebas.md; metodologia_y_decisiones.md.
BootROM/DDR futuro: plan_bootrom_original_y_programas_ddr.md. Auditoría: auditorias/bootrom_y_carga_ddr_20261029.json.
Explicación del camino de memoria: cva6-equipo/docs/kr260_ps_ddr_architecture.md y kr260_ddr_integration.md. Algunos documentos antiguos describen estados previos; usar el plan/auditoría actual para la selección real de ROM.
Entrega reunión: entregas/reunion_profesor_20261030/.
Resumen PDF: esa entrega/output/pdf/CVA6_KR260_estado_reunion_20261030.pdf.
Manual actual: esa entrega/manual_placa/output/pdf/Manual_CVA6_KR260_90_9MHz.pdf.
Respaldo externo registrado: RESPALDO_EXTERNO_20261029.md. El destino conocido es nacho@192.168.86.31 bajo /home/nacho/backups/CVA6. Los respaldos son copias, no sustituyen archivos locales. No se garantiza acceso fuera de esa red.''')
page('Acceso rápido / comandos y referencias finales', '''Abrir directorios reales desde la terminal Linux. Estas órdenes no programan hardware. El archivo RUTAS_IMPORTANTES.txt contiene las rutas absolutas comprobadas.''', '''CVA6_BASE=/home/nachofalchi/data/fpga-work
cd "$CVA6_BASE/cva6-equipo"
# Abrir carpeta del proyecto:
xdg-open "$CVA6_BASE/cva6-equipo/corev_apu/fpga/ariane_kr260_debug"
# Abrir documentación y entrega:
xdg-open "$CVA6_BASE/cva6-equipo/docs/seguimiento_fpga"
xdg-open "$CVA6_BASE/entregas/reunion_profesor_20261030"
# Ver comandos disponibles sin ejecutar pruebas:
/home/nachofalchi/.local/bin/cva6 --help
/home/nachofalchi/.local/bin/cva6 ensayo --help
''', '''Fuentes operativas locales: plantillas board_run.tcl e ila_capture.tcl y configuración de automatización. Se contrastó el orden sin lanzar herramientas de hardware.
Conexiones J4/J12 - AMD (se usan sólo sus datos de conectores; la demo no sigue su arranque Linux):
https://xilinx.github.io/kria-apps-docs/kr260/linux_boot/embedded_linux/build/html/docs/connections.html
SW1/FWUEN - AMD UG1092:
https://docs.amd.com/r/en-US/ug1092-kr260-starter-kit/Firmware-Update
Checkpoint/timing - AMD:
https://docs.amd.com/r/en-US/conversion-methodology/Timing-Closure
ILA - AMD UG835:
https://docs.amd.com/r/2021.2-English/ug835-vivado-tcl-commands/run_hw_ila
Respuestas preparadas para preguntas probables; no son garantía de cubrir cualquier pregunta. Si falta evidencia, responder que no se midió o que sigue pendiente, y mostrar el archivo fuente relevante.''')
# Replace obsolete page references with named sections after expansion.
repls={'página 03':'apartado Archivos y programas','páginas 03':'apartado Archivos y programas','página 08':'apartado Ejecutar y guardar evidencia','página 07':'apartado Vivado: armar captura ILA','página06':'apartado Verificar la preparación','página 06':'apartado Verificar la preparación','página 02':'apartado Camino automatizado'}
for i,(title,intro,code,after) in enumerate(pages):
 for old,new in repls.items():intro=intro.replace(old,new);after=after.replace(old,new)
 if ' / ' in title and title.split(' / ')[0].isdigit():title=title.split(' / ',1)[1]
 if title=='Guía de prueba CVA6 - KR260':intro=intro.replace('Contenido: 02 automatización; 03 archivos/herramientas; 04 XSDB; 05 preparación; 06 comprobaciones; 07 ILA; 08 ejecución; 09 diagnóstico; 10 timing y referencias.','Guía ampliada: conexión física, herramientas, control25, procedimiento91, comprobaciones, ILA, diagnóstico, preguntas de reunión y rutas de evidencia.')
 pages[i]=(title,intro,code,after)

# Put the overview first, and normalize spacing in explanatory prose.
import re
summary = next(i for i,p in enumerate(pages) if p[0]=='Guía de prueba CVA6 - KR260')
pages.insert(0,pages.pop(summary))
for i,(title,intro,code,after) in enumerate(pages):
 for old,new in [('25o91','25 o 91'),('de32bits','de 32 bits'),('de64bits','de 64 bits'),('de64','de 64'),('25MHz','25 MHz'),('100MHz','100 MHz'),('90,9MHz','90,9 MHz'),('91MHz','91 MHz'),('2048muestras','2048 muestras'),('26beats','26 beats'),('0con','0 con'),('75endpoints','75 endpoints'),('1285endpoints','1285 endpoints'),('conectarhw','conectar hw')]:
  intro=intro.replace(old,new);after=after.replace(old,new)
 pages[i]=(title,intro,code,after)
# A single operating route, followed by independent appendices.
old={p[0]:p for p in pages}
manual=[]
def op(title,intro,code='',after=''):
 manual.append((title,intro,code,after))
op('Cómo utilizar este manual', '''Objetivo: ejecutar la prueba existente de BootROM/DDR del CVA6 en KR260, primero a25MHz como control y después a90,908180MHz. No se modifica el CPU ni la ROM.
Leer este apartado y seguir los pasos01a12 EN ORDEN. No hace falta recorrer los apéndices para realizar la vía principal. Cada paso indica la consola, la acción, la salida esperada y cuándo detenerse.
El procedimiento principal es manual: terminal Linux + XSDB + Vivado. Si se prefiere la rutina automatizada, ir al apéndice A y no realizar ambos procedimientos simultáneamente.
Primera pasada: seleccionar frecuencia25 en XSDB y en Vivado. Completar los pasos y guardar evidencia. Segunda pasada: comenzar desde una sesión nueva, seleccionar91 en ambas herramientas y repetir. Nunca cambiar sólo el divisor o mezclar BIT/LTX/FSBL.
25 significa24,999750MHz;91 significa90,908180MHz. El paquete91 tiene STA cerrado (WNS+0,001ns;TNS0;WHS+0,004ns), pero su funcionamiento hardware sigue pendiente al preparar esta edición.
Qué se considera éxito: estado de BootROM PASS, estados secundarios sin diferencias, reset liberado y captura ILA con muestras si se hizo captura. No es validación exhaustiva de ISA, Linux o memoria.
La aplicación ARM escribe patrones en DDR antes de liberar CVA6. No preserva programas precargados. No se toca QSPI ni se genera BOOT.BIN con esta guía.
Organización: procedimiento principal; alternativas y diagnóstico; preguntas para el profesor; rutas y referencias. Si una orden falla, detenerse en ese punto, guardar el mensaje y consultar diagnóstico. No continuar pegando el bloque siguiente.''')
p=old['Antes de empezar / conexión física'];op('Paso 01 / conectar y encender', 'DÓNDE: mesa de trabajo y terminal Linux. ESTADO INICIAL: placa sin alimentar.\n'+p[1],p[2],p[3]+'\nCOMPROBACIÓN: alimentación presente y puente USB visible en lsusb. DETENERSE si la placa no enciende o USB no aparece. SIGUIENTE: paso02.')
op('Paso 02 / verificar los archivos', '''DÓNDE: terminal Linux, antes de tocar registros del hardware.
ACCIÓN: comprobar los paquetes sin depender del wrapper cva6. Copiar el bloque completo. Se calculan hashes; no se programa la FPGA.
El paquete25 contiene un error histórico únicamente en la autoentrada de su manifiesto. Por eso se filtra ESA entrada y se verifican todos los archivos de contenido. No se omite ninguna entrada ELF, BIT o LTX. El paquete91 se verifica completo.''', r'''CVA6_BASE=/home/nachofalchi/data/fpga-work
CVA6_BOOT="$CVA6_BASE/cva6-equipo/corev_apu/fpga/software"
CVA6_BOOT="$CVA6_BOOT/kr260_ps_boot"
CVA6_KG="$CVA6_BOOT/known_good_2026-09-18"
CVA6_PK="$CVA6_BOOT/timing_closed_91mhz_2026-10-22"
(cd "$CVA6_KG" && awk '$2 !~ /SHA256SUMS.txt$/ {print}' \
  SHA256SUMS.txt | sha256sum -c -)
(cd "$CVA6_PK" && sha256sum -c SHA256SUMS.txt)
CVA6_FSBL="$CVA6_BASE/operacion/cva6_ops/fsbl91"
sha256sum "$CVA6_FSBL/build_20261029_1831/kr260_fsbl_91mhz_patched.elf"
''','''ESPERADO:17archivos de contenido25 y29archivos91 correctos. SHA256 del FSBL91 (unir mitades):
4b2c98d7ea93099d62b7538ce4d92b071
d3672ef157b48acf7bf688df380ab87
DETENERSE ante archivo faltante o hash diferente. SIGUIENTE: paso03.''')
op('Paso 03 / abrir herramientas y registrar', '''DÓNDE: terminal Linux. Dejar una terminal para XSDB y una ventana de Vivado. La grabación es opcional pero recomendable: primero crea una carpeta nueva y luego inicia una subshell grabada.
1. Ejecutar el bloque. Si script no existe, guardar manualmente el texto de XSDB al final; no impide ejecutar la prueba.
2. Dentro de la subshell que abre script, iniciar XSDB con la última orden.
3. Si Vivado ya está abierto, reutilizarlo. Si no, iniciarlo desde otra terminal con la ruta que figura abajo.
4. Para el servidor, usar Hardware Manager > Open Target > Auto Connect o iniciar hw_server si todavía no hay uno activo. No iniciar dos servidores sobre3121.''', r'''CVA6_BASE=/home/nachofalchi/data/fpga-work
CVA6_RUN="$CVA6_BASE/operacion/cva6_ops/manual_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CVA6_RUN"
echo "$CVA6_RUN"
script -q -f "$CVA6_RUN/xsdb_terminal.log"
# En la subshell grabada:
/home/nachofalchi/data/fpga-work/Xilinx/2026.1/\
Vitis/bin/xsdb
''','''ESPERADO: prompt xsdb%. La carpeta impresa es la de evidencia, anotarla.
Vivado: /home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/vivado
Servidor opcional: misma ruta Vivado/bin/hw_server. Mantener su terminal abierta.
En Vivado: Flow > Open Hardware Manager > Open Target > Auto Connect. Todavía no pulsar Program Device. Si falla, revisar cable y servidor. SIGUIENTE: paso04.''')
select=old['XSDB: seleccionar archivos y placa'][2]
start=select.index('set pkg ');end=select.index('foreach p ')
select=select[:start]+'''# PRIMERA pasada: 25. SEGUNDA pasada nueva: 91.
set frecuencia 25
if {$frecuencia == 25} {
    set pkg [file join $boot known_good_2026-09-18]
    set fsbl [file join $pkg kr260_fsbl_patched.elf]
    set clock_expected 0x01012800
} elseif {$frecuencia == 91} {
    set pkg [file join $boot timing_closed_91mhz_2026-10-22]
    set fsbl [file join $base operacion cva6_ops fsbl91 \\
        build_20261029_1831 kr260_fsbl_91mhz_patched.elf]
    set clock_expected 0x01010b00
} else {error "Frecuencia no admitida"}
set bit [file join $pkg kr260_top.bit]
set app [file join $boot known_good_2026-09-18 kr260_app_jtag.elf]
puts "PERFIL=$frecuencia; BIT=$bit; FSBL=$fsbl"
'''+select[end:]
op('Paso 04 / elegir perfil y conectar XSDB', '''DÓNDE: XSDB, prompt xsdb%. Mantener esta sesión abierta hasta el paso12.
ACCIÓN: en la primera pasada dejar set frecuencia25. En la segunda cambiar únicamente esa selección a91 ANTES de ejecutar el bloque completo. Las rutas se derivan del perfil; no editarlas a mano.
Conectar una sola placa. sel exige un único target exacto e imprime sus propiedades; confirmar que PSU y A53 pertenecen al mismo cable. El selector manual no reemplaza todos los controles de identidad de la automatización.''',select,'''ESPERADO: sin errores de archivos, lista de targets y PSU seleccionado. Anotar el cable serial. DETENERSE si faltan targets o aparece ambigüedad. No seleccionar otro procesador por tanteo.
Las variables de XSDB NO existen en Vivado. Allí se seleccionará el mismo perfil otra vez. SIGUIENTE: paso05.''')
prep=old['Preparar PS, DDR y bitstream'][2]
pos=prep.index('# Programar');pos2=prep.index('# Segunda')
op('Paso 05 / reset y primera ejecución FSBL', '''DÓNDE: misma sesión XSDB del paso04. ESTADO INICIAL: perfil elegido y PSU accesible.
ACCIÓN: cambiar el arranque a JTAG volátil, resetear el sistema y ejecutar el FSBL seleccionado en Cortex-A53 #0. La espera de15segundos no indica PASS por sí sola.
Qué hace cada orden: mwr escribe registros de control; rst -system reinicia el sistema; dow carga el ELF; con deja correr ARM; stop lo detiene para continuar. after usa milisegundos.''',prep[:pos],'''ESPERADO: descarga del FSBL y parada del ARM sin errores. Todavía no se ejecutó la prueba de CVA6.
DETENERSE si rst, dow, con o stop fallan. Guardar el error y revisar conectividad/ELF. SIGUIENTE: paso06.''')
op('Paso 06 / programar PL y repetir FSBL', '''DÓNDE: misma sesión XSDB. ESTADO INICIAL: primera ejecución de FSBL terminada.
ACCIÓN: cargar el BIT del perfil y ejecutar OTRA VEZ el FSBL. El segundo pase es necesario en esta receta para restablecer correctamente la inicialización tras programar PL.
El reset final sólo afecta al A53 seleccionado. CVA6 debe seguir retenido por el FSBL parcheado. No cargar todavía la aplicación y no cambiar VIO.''',prep[pos:],'''ESPERADO: configuración PL sin errores, segunda descarga FSBL finalizada y A53 detenido. No hace falta usar Program Device: fpga -f ya hizo ese trabajo.
DETENERSE ante error de programación o ejecución. SIGUIENTE: paso07.''')
checks=old['Verificar la preparación'][2].replace('!= 0x01010b00','!= $clock_expected').replace('Clock distinto de IOPLL/11','Clock distinto del perfil elegido')
op('Paso 07 / comprobar estado antes del arranque', '''DÓNDE: XSDB, con las variables del perfil todavía definidas.
ACCIÓN: ejecutar el bloque completo. rd32 lee una palabra; rd64 reconstruye un valor de64bits a partir de dos palabras de32bits. Se exige clock del perfil, reset retenido, PL configurada, DDR normal y HP0 de64bits.''',checks,'''ESPERADO: PREPARACION OK; aun no es PASS funcional. DETENERSE si cualquiera de los controles da error. No modificar un registro aislado para saltar la comprobación.
SIGUIENTE: paso08. Desde ahora hasta lanzar la app, no resetear PS/ARM ni volver a programar PL.''')
ila=old['Vivado: armar captura ILA'][2]
ss=ila.index('set pkg ');ee=ila.index('set ds ')
ila=ila[:ss]+'''# Debe ser el MISMO perfil elegido en XSDB.
set frecuencia 25
set boot [file join $base cva6-equipo corev_apu fpga \\
    software kr260_ps_boot]
if {$frecuencia == 25} {
    set pkg [file join $boot known_good_2026-09-18]
} elseif {$frecuencia == 91} {
    set pkg [file join $boot timing_closed_91mhz_2026-10-22]
} else {error "Frecuencia no admitida"}
'''+ila[ee:]
op('Paso 08 / asociar probes y armar ILA', '''DÓNDE: Vivado, Hardware Manager. XSDB queda abierto y detenido en el estado preparado.
1. Abrir Flow > Open Hardware Manager y Open Target > Auto Connect si no estaba conectado. Confirmar la misma placa/cable que en XSDB. No pulsar Program Device.
2. En Tcl Console de VIVADO, ejecutar el bloque siguiente. Elegir el mismo25o91 que en XSDB. El bloque selecciona un único dispositivo e ILA, carga el LTX y lo arma para commit_valid=1.
3. Esperar a que la UI indique espera de trigger. No ejecutar todavía wait_on_hw_ila: primero hay que arrancar la app en XSDB.
La captura ILA es parte de la ruta principal. Si se omite intencionalmente, registrar que el resultado funcional no incluye captura y saltar del paso07 al09.''',ila,'''ESPERADO: ILA armado, sin error de probes. DETENERSE si el LTX no corresponde o el dispositivo/ILA es ambiguo. Revisar BIT/LTX, clock y perfil.
SIGUIENTE: paso09 en XSDB, sin cerrar Vivado. No volver a ejecutar reset_hw_ila después de producir el evento.''')
run=old['Ejecutar y guardar evidencia'][2]
op('Paso 09 / lanzar aplicación y leer estados', '''DÓNDE: volver a la MISMA sesión XSDB; no iniciar otra ni ejecutar reset.
ESTADO INICIAL: paso07 correcto e ILA esperando si se hace captura.
ACCIÓN: borrar el estado anterior, cargar app ARM en el A53 detenido y ejecutarla. La app prepara/prueba DDR y libera CVA6. Se esperan20segundos y luego hasta30segundos adicionales por el estado de la ROM.
No interpretar dow completado como PASS. El criterio funcional está en el paso10.''',run,'''ESPERADO: cuatro valores de estado de64bits y GPIO impresos, sin errores de lectura. Guardar TODA la salida. Si el tiempo vence con estado0, registrar incompleto; no afirmar fallo de timing automáticamente.
SIGUIENTE: paso10 para evaluar esos valores, y después paso11 para guardar la captura.''')
op('Paso 10 / decidir PASS, FAIL o incompleto', '''DÓNDE: salida XSDB del paso09. No se ejecutan nuevos resets ni se repite la app durante la evaluación.
PASS funcional requiere TODOS estos valores:
0x800004000 (STATUS0): 0x0000000000000001.
0x800004008 (STATUS8): 0x0000000000000000.
0x800004010 (STATUS16): 0x0000000000000000.
0x800004018 (STATUS24): 0x0000000000000000.
GPIO en0xff0a0054: bit31 activo; por ejemplo0x80000000. Esto indica reset liberado. No se exige que los demás bits valgan0.
FAIL de comparación: STATUS0=0xffffffffffffffff. Guardar estados secundarios y captura para identificar la diferencia; no sobrescribirlos con un nuevo intento.
INCOMPLETO: STATUS0 sigue en0 o tiene otro valor no reconocido. Investigar arranque, reset, clock y memoria. No equivale a PASS ni identifica por sí solo el origen del problema.
ERROR de herramienta: fallo de USB, targets, descarga, lectura o timeout de herramienta. Registrar ERROR, separado de un fallo funcional de la ROM.
Con ILA, el ensayo completo exige además captura con muestras. Un PASS de memoria sin CSV sólo acredita la parte funcional observada.
SIGUIENTE: paso11 incluso si hubo FAIL, para preservar la captura disponible. Después cerrar y guardar en el paso12. No repetir automáticamente.''')
cap=old['Captura y diagnóstico'][2]
op('Paso 11 / descargar y conservar captura', '''DÓNDE: volver a Tcl Console de VIVADO, donde permanece definido $ila del paso08.
ACCIÓN: esperar hasta2minutos por el trigger y descargar la captura a un directorio nuevo. El timeout de wait_on_hw_ila se expresa en MINUTOS.
Si no se armó ILA, no ejecutar este bloque. Si CORE_STATUS no es IDLE, detenerse y registrar que la captura no terminó.''',cap,'''ESPERADO: archivo capture.csv en la carpeta que imprime Vivado. Abrirlo para comprobar que tiene encabezado y filas de muestras. Conservar la ruta junto a la sesión XSDB aunque se hayan creado dos carpetas distintas.
La UI muestra ondas después de subir los datos. No basta con que exista un ILA en Hardware Manager: debe haber una captura efectiva.
SIGUIENTE: paso12.''')
op('Paso 12 / cerrar y preparar la siguiente pasada', '''DÓNDE: XSDB, terminal Linux y Vivado.
1. Guardar el log de XSDB, captura CSV y una nota con fecha, perfil25o91, cable serial, rutas BIT/LTX/FSBL/app y los cuatro estados. Anotar PASS/FAIL/ERROR o incompleto.
2. En XSDB ejecutar disconnect y exit. Si se usó script para grabar la terminal, ejecutar exit otra vez en la subshell. Volver al prompt Linux original.
3. En Vivado conservar la captura; cerrar el hardware target propio al terminar su uso. No cerrar servidores o sesiones de otras personas.
4. Si se terminó la pasada25conPASS, realizar una nueva pasada desde el paso03, en carpeta nueva: en el paso04 elegir91 y en el paso08 elegir91. Repetir TODO el arranque. El BIT de25no se convierte en91 cambiando un registro suelto.
5. Si25falla, investigar el entorno y consultar diagnóstico antes de91. Si91falla, conservar el resultado sin modificar la evidencia25.
6. Al finalizar la reunión, desconectar de las herramientas y apagar la placa. Tras cortar alimentación no se asume que el BIT o modo volátil sigan cargados.
Alcance de la conclusión: la prueba demuestra lo observado en esa sesión. No permite afirmar frecuencia máxima absoluta, validación completa del CPU ni carga de aplicaciones genéricas.
Lista final de evidencia: hashes correctos; perfil coherente; log XSDB; estados completos; captura si se hizo; rutas y fecha. No borrar ni reemplazar paquetes congelados.''', '''# XSDB, al terminar:
disconnect
exit
# Si se estaba grabando con script, en la subshell Bash:
exit
''')
# All supporting material stays accessible, away from the operating sequence.
appendices=[('A / Alternativa automatizada','Camino automatizado'),('B / Consolas y herramientas','Ventanas y consolas / no mezclarlas'),('C / Programar el BIT desde la UI','Program Device / alternativa sólo para el BIT'),('D / Diagnóstico y recuperación','Errores / decidir dónde detenerse'),('E / Consultar timing en Vivado','Timing, identidad y referencias'),('F / Profesor: resultados','Preguntas del profe / estado y resultados'),('G / Profesor: arquitectura y prueba','Preguntas del profe / arquitectura y test'),('H / Profesor: timing y evidencia','Preguntas del profe / timing y reproducibilidad'),('I / Rutas: proyecto y placa','Rutas importantes / proyecto y archivos de placa'),('J / Rutas: reportes y documentación','Rutas importantes / reportes y documentación'),('K / Acceso rápido y referencias','Acceso rápido / comandos y referencias finales')]
for title,key in appendices:
 _,intro,code,after=old[key]
 if key=='Program Device / alternativa sólo para el BIT':intro=intro.replace('de la preparación','del paso06').replace('páginas','apartados')
 manual.append((title,intro,code,after))
pages=manual
# Readable units and step references in prose only; never alter executable code.
for i,(title,intro,code,after) in enumerate(pages):
 for field_old,field_new in [('25MHz','25 MHz'),('90,908180MHz','90,908180 MHz'),('25o91','25 o 91'),('25conPASS','25 con PASS'),('25falla','25 falla'),('91falla','91 falla'),('antes de91','antes de 91'),('25no','25 no'),('de64bits','de 64 bits'),('de32bits','de 32 bits'),('de15segundos','de 15 segundos'),('hasta30segundos','hasta 30 segundos'),('esperan20segundos','esperan 20 segundos'),('hasta2minutos','hasta 2 minutos'),('sobre3121','sobre 3121')]:
  intro=intro.replace(field_old,field_new);after=after.replace(field_old,field_new)
 pages[i]=(title,intro,code,after)

# Final wording makes profile and step references explicit.
for i,(title,intro,code,after) in enumerate(pages):
 for a,z in [('pasos01a12','pasos 01 a 12'),('frecuencia25','frecuencia 25'),('selección a91','selección a 91'),('seleccionar91','seleccionar 91'),('elegir91','elegir 91'),('0xff0a0054:','0xff0a0054:'),('por ejemplo0x','por ejemplo 0x'),('de25no','de 25 no'),('ESTADO INICIAL: paso07','ESTADO INICIAL: paso 07'),('ESPERADO:17archivos de contenido25 y29archivos91','ESPERADO: 17 archivos de contenido de 25 MHz y 29 archivos de 91 correctos'),('25significa','25 significa')]:
  intro=intro.replace(a,z);after=after.replace(a,z)
 if title.startswith('C /'):
  intro='Esta alternativa describe el perfil91. Para25, seleccionar BIT y LTX del paquete conocido25. En ambos casos sustituye sólo la programación del paso06; el resto de la secuencia se conserva.\n'+intro
 pages[i]=(title,intro,code,after)
# companion plaintext contains exactly the visible content and copyable commands
(out/'MANUAL_PLACA.txt').write_text('\n\n'.join(title+'\n\n'+intro+'\n\n'+code+'\n\n'+after for title,intro,code,after in pages))
pdf=out/'output/pdf/Manual_CVA6_KR260_90_9MHz.pdf'
c=canvas.Canvas(str(pdf),pagesize=(595.28,841.89))
c.setTitle('CVA6 / KR260 - Manual de prueba en placa');c.setAuthor('Proyecto CVA6 KR260')
navy='#102B3B';teal='#007F82';orange='#E8A34D';ink='#243C49';muted='#607681';light='#EFF5F6'
def text(x,y,s,font='Sans',size=10,color=ink):
 c.setFillColor(HexColor(color));c.setFont(font,size);c.drawString(x,y,s)
def footer(n):
 c.setStrokeColor(HexColor('#D8E3E7'));c.line(42,45,553,45)
 text(42,29,'CVA6 / KR260     ·     Guía de laboratorio',size=8,color=muted)
 c.setFont('Sans',8);c.drawRightString(553,29,f'{n:02d} / {len(pages)+2:02d}')
def section(i):
 if i==0:return 'LECTURA INICIAL / OBJETIVO Y ALCANCE'
 if i<=3:return 'PROCEDIMIENTO / PREPARAR EL ENTORNO'
 if i<=7:return 'PROCEDIMIENTO / PREPARAR LA PLACA'
 if i<=12:return 'PROCEDIMIENTO / EJECUTAR Y VERIFICAR'
 return 'APÉNDICES / CONSULTA Y EVIDENCIA'
# Cover, drawn as vector graphics for clean printing and zoom.
c.setFillColor(HexColor(navy));c.rect(0,0,595.28,841.89,fill=1,stroke=0)
c.setStrokeColor(HexColor('#214657'))
for x in range(345,610,24):c.line(x,150,x,842)
for yy in range(150,850,24):c.line(345,yy,596,yy)
c.setFillColor(HexColor(teal));c.rect(42,750,46,5,fill=1,stroke=0)
text(42,718,'GUÍA DE LABORATORIO',font='Bold',size=11,color='#72D1C7')
text(42,635,'CVA6',font='Bold',size=62,color='#FFFFFF')
text(42,586,'en KR260',font='Bold',size=38,color='#FFFFFF')
text(44,533,'De la conexión a la evidencia.',size=18,color='#D6E7ED')
text(44,502,'Arranque · XSDB · Vivado · ILA · Timing',size=12,color='#A6C3CE')
for x,value,label in [(42,'90,9 MHz','IMPLEMENTACIÓN CERRADA'),(306,'25 MHz','REFERENCIA FUNCIONAL')]:
 c.setFillColor(HexColor('#193D4E'));c.roundRect(x,342,247,103,10,fill=1,stroke=0)
 text(x+17,402,value,font='Bold',size=24,color='#FFFFFF');text(x+17,372,label,font='Bold',size=8,color='#7DD6CF')
c.setFillColor(HexColor(orange));c.roundRect(42,222,511,73,8,fill=1,stroke=0)
text(59,267,'ANTES DE LA PRUEBA',font='Bold',size=9,color=navy)
text(59,246,'90,9 MHz: validación en placa pendiente.',size=12,color=navy)
text(43,116,'Procedimiento manual y automatizado',font='Bold',size=12,color='#FFFFFF')
text(43,93,'Comandos completos, diagnóstico y preguntas para la reunión.',size=10,color='#C1D6DF')
text(43,49,'Edición local  /  30 octubre 2026',size=9,color='#8FACBA')
c.showPage()
# Contents with clickable links into the PDF.
text(42,788,'CVA6 / KR260',font='Bold',size=9,color=teal)
text(42,746,'Encontrar cada paso',font='Bold',size=25,color=navy)
text(42,719,'Índice interactivo. Hacé clic en un apartado para ir a su página.',size=10,color=muted)
y=679
for i,(title,_,_,_) in enumerate(pages):
 if i%2==0:
  c.setFillColor(HexColor(light));c.roundRect(36,y-8,523,22,3,fill=1,stroke=0)
 size=min(10,461/pdfmetrics.stringWidth(title,'Sans',1))
 text(46,y,title,size=size)
 text(528,y,f'{i+3:02d}',font='Bold',size=10,color=teal)
 c.linkRect('',f'section{i}',(36,y-8,559,y+14),relative=0,thickness=0)
 y-=23
footer(2);c.showPage()
for i,(title,intro,code,after) in enumerate(pages):
 c.bookmarkPage(f'section{i}');c.addOutlineEntry(title,f'section{i}',0,False)
 c.setFillColor(HexColor(teal));c.rect(0,811,595.28,31,fill=1,stroke=0)
 text(42,822,section(i),font='Bold',size=8,color='#FFFFFF')
 text(42,781,f'{i+1:02d}',font='Bold',size=11,color=teal)
 size=min(22,470/pdfmetrics.stringWidth(title,'Bold',1))
 text(78,779,title,font='Bold',size=size,color=navy)
 c.setStrokeColor(HexColor('#D8E3E7'));c.line(42,760,553,760)
 y=737
 def para(txt):
  global y
  for paragraph in txt.split('\n'):
   if not paragraph:continue
   is_question=paragraph.startswith('¿')
   lines=simpleSplit(paragraph,'Sans',10.3,505)
   for line in lines:
    text(44,y,line,size=10.3);y-=14.6
   y-=8
 para(intro)
 if code:
  lines=code.rstrip().splitlines();fs=min(8.3,493/max(pdfmetrics.stringWidth(line,'Mono',1) for line in lines));lh=11.2
  height=len(lines)*lh+39
  c.setFillColor(HexColor(light));c.roundRect(36,y-height+5,523,height,7,fill=1,stroke=0)
  c.setFillColor(HexColor(teal));c.roundRect(36,y-15,523,24,5,fill=1,stroke=0)
  label='XSDB  /  Tcl' if title.startswith(('Paso 04','Paso 05','Paso 06','Paso 07','Paso 09')) or title in ['XSDB: seleccionar archivos y placa','Preparar PS, DDR y bitstream','Verificar la preparación','Ejecutar y guardar evidencia','Control de referencia / repetir 25 MHz a mano'] else ('VIVADO  /  Tcl Console' if title.startswith(('Paso 08','Paso 11')) or title in ['Vivado: armar captura ILA','Captura y diagnóstico'] else 'TERMINAL  /  Bash')
  label='XSDB y TERMINAL / cierre' if title.startswith('Paso 12') else label
  text(47,y-7,label,font='Bold',size=8,color='#FFFFFF');y-=31
  for line in lines:
   text(47,y,line,font='Mono',size=fs,color=muted if line.lstrip().startswith('#') else navy);y-=lh
  y-=19
 para(after)
 if y<63:raise ValueError(f'Overflow page {i+3}: {y}')
 footer(i+3);c.showPage()
c.save()
print(pdf)
