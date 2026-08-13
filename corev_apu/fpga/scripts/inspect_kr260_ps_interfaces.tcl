# Inspect the KR260 board preset and the PL-to-PS AXI slave interfaces exposed
# by the Vivado 2026.1 Zynq UltraScale+ MPSoC IP. This is a read-only design
# probe: it creates a disposable project but does not synthesize or implement.

if {![info exists ::env(XILINX_PART)] || ![info exists ::env(XILINX_BOARD)]} {
    error "XILINX_PART and XILINX_BOARD must be set"
}
if {![info exists ::env(KR260_PS_REPORT)]} {
    error "KR260_PS_REPORT must name the output report"
}

set_param general.maxThreads 1
set report_path [file normalize $::env(KR260_PS_REPORT)]
file mkdir [file dirname $report_path]

create_project kr260_ps_interface_probe kr260_ps_interface_probe -force \
    -part $::env(XILINX_PART)
set_property board_part $::env(XILINX_BOARD) [current_project]
create_bd_design ps_interface_probe

set ps_vlnv [lindex [lsort [get_ipdefs -all \
    -filter {VLNV =~ "xilinx.com:ip:zynq_ultra_ps_e:*"}]] end]
if {$ps_vlnv eq ""} {
    error "zynq_ultra_ps_e is not installed"
}
set ps [create_bd_cell -type ip -vlnv $ps_vlnv zynq_ultra_ps_e_0]
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset "1"} $ps

# Enable one non-coherent HP port and one coherent HPC port at the same 64-bit
# data width as CVA6. The legacy GP indices are the names used by PS IP config.
set ps_properties [list_property $ps]
foreach {property value} {
    CONFIG.PSU__USE__S_AXI_GP0       1
    CONFIG.PSU__SAXIGP0__DATA_WIDTH  64
    CONFIG.PSU__USE__S_AXI_GP2       1
    CONFIG.PSU__SAXIGP2__DATA_WIDTH  64
} {
    if {[lsearch -exact $ps_properties $property] >= 0} {
        set_property $property $value $ps
    } else {
        puts "KR260_PS_INSPECT_WARNING=missing property $property"
    }
}

set report [open $report_path w]
puts $report "Vivado: [version -short]"
puts $report "Part: [get_property PART [current_project]]"
puts $report "Board: [get_property BOARD_PART [current_project]]"
puts $report "PS IP: $ps_vlnv"

puts $report "\nRelevant PS configuration"
foreach property [lsort [list_property $ps]] {
    if {[string match "CONFIG.PSU__USE__S_AXI*" $property] ||
        [string match "CONFIG.PSU__SAXIGP*" $property] ||
        [string match "CONFIG.PSU__CRF_APB__TOPSW_*" $property] ||
        [string match "CONFIG.PSU__FPGA_PL*" $property]} {
        puts $report "$property=[get_property $property $ps]"
    }
}

puts $report "\nPS AXI interfaces"
foreach interface [lsort [get_bd_intf_pins -of_objects $ps]] {
    if {![string match "*AXI*" $interface] &&
        ![string match "*DDR*" $interface]} {
        continue
    }
    puts $report "\n$interface"
    foreach property [lsort [list_property $interface]] {
        if {$property in {MODE VLNV} ||
            [string match "CONFIG.*WIDTH" $property] ||
            [string match "CONFIG.*BURST*" $property] ||
            [string match "CONFIG.*LOCK*" $property] ||
            $property in {CONFIG.PROTOCOL CONFIG.FREQ_HZ CONFIG.READ_WRITE_MODE
                          CONFIG.NUM_READ_OUTSTANDING
                          CONFIG.NUM_WRITE_OUTSTANDING}} {
            puts $report "  $property=[get_property $property $interface]"
        }
    }
}

puts $report "\nPS clock and reset pins"
foreach pin [lsort [get_bd_pins -of_objects $ps]] {
    if {[string match -nocase "*clk*" $pin] ||
        [string match -nocase "*reset*" $pin]} {
        puts $report "$pin DIR=[get_property DIR $pin] \
TYPE=[get_property TYPE $pin]"
    }
}

puts $report "\nPS address segments"
foreach segment [lsort [get_bd_addr_segs -quiet]] {
    puts $report "$segment OFFSET=[get_property OFFSET $segment] \
RANGE=[get_property RANGE $segment]"
}
close $report

save_bd_design
close_project
puts "KR260_PS_INTERFACE_INSPECTION=SUCCESS"
