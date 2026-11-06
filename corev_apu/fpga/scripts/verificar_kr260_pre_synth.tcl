# Ejecutar con source desde la Tcl Console del proyecto KR260 abierto.
# Solo validacion y elaboracion RTL: no lanza synth_1 ni implementacion.
proc verificar_kr260 {} {
    if {[llength [current_project -quiet]] != 1} {
        error "Primero abri el proyecto KR260."
    }
    set fs [get_filesets sources_1]
    if {[get_property TOP $fs] ne "kr260_top"} {
        error "La top debe ser kr260_top."
    }
    foreach nombre {
        kr260_top.sv
        ariane_kr260.sv
        kr260_addr_pkg.sv
        bootrom.sv
        kr260_ps_ddr_bd.bd
        kr260_ps_ddr_bd_wrapper.v
    } {
        set archivos [get_files -quiet */$nombre]
        if {[llength $archivos] != 1} {
            error "Se esperaba un archivo $nombre; encontrados: $archivos"
        }
    }
    foreach nombre {
        ariane_kr260_ps_bd.bd
        ariane_kr260_ps_bd_wrapper.v
        kr260_ps_ddr_bd_sv.sv
    } {
        if {[llength [get_files -quiet */$nombre]] != 0} {
            error "Todavia esta registrado: $nombre"
        }
    }
    set defs [get_property VERILOG_DEFINE $fs]
    if {[lsearch -exact $defs KR260_MEMORY_TEST_BOOTROM] < 0} {
        error "Falta KR260_MEMORY_TEST_BOOTROM."
    }
    foreach nombre {kr260_axi_ila kr260_reset_vio} {
        if {[llength [get_ips -quiet $nombre]] != 1} {
            error "Falta la IP $nombre."
        }
    }
    set inicial [get_property CONFIG.C_PROBE_OUT0_INIT_VAL [get_ips kr260_reset_vio]]
    if {$inicial != 0} {
        error "El VIO mantiene reset al arrancar: valor inicial $inicial."
    }
    set carpeta [file join [get_property DIRECTORY [current_project]] pre_synth_check]
    file mkdir $carpeta

    open_bd_design [get_files */kr260_ps_ddr_bd.bd]
    validate_bd_design
    save_bd_design
    update_compile_order -fileset sources_1
    report_ip_status -file [file join $carpeta ip_status.rpt]
    report_compile_order -used_in synthesis -file [file join $carpeta compile_order.rpt]

    # Cierra una vista de netlist anterior, si estuviera abierta.
    if {[llength [current_design -quiet]] != 0} {
        close_design
    }
    # -rtl solo elabora: no ejecuta sintesis de logica.
    synth_design -rtl -name kr260_pre_synth

    set cajas [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]
    if {[llength $cajas] != 0} {
        error "Modulos sin resolver: $cajas"
    }
    foreach instancia {i_ariane_kr260 i_ps_ddr i_kr260_axi_ila i_kr260_reset_vio} {
        if {[llength [get_cells -quiet $instancia]] != 1} {
            error "Falta la instancia $instancia."
        }
    }
    set reloj [get_clocks -quiet clk_pl_0]
    if {[llength $reloj] != 1} {
        error "No se reconoce el reloj clk_pl_0 del PS."
    }
    set periodo [get_property PERIOD $reloj]
    if {abs($periodo - 40.0) > 0.01} {
        error "Periodo inesperado: $periodo ns; se esperaban unos 40 ns."
    }
    report_clocks -file [file join $carpeta clocks.rpt]
    puts "============================================"
    puts "KR260: VERIFICACION RTL COMPLETADA"
    puts "Reportes: $carpeta"
    puts "No se ejecuto sintesis de logica."
    puts "Revisar ip_status.rpt y advertencias de consola."
    puts "Timing final y DDR en hardware siguen pendientes."
    puts "============================================"
}
verificar_kr260
