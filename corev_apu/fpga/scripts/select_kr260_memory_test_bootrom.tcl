# Agrega al proyecto la ROM minima de CVA6, que salta a 0x80000000.
# ariane_kr260 instancia esta ROM incondicionalmente.

set boot_rom [file normalize [file join [file dirname [info script]] .. .. bootrom bootrom.sv]]
if {![file exists $boot_rom]} { error "Falta corev_apu/bootrom/bootrom.sv" }
if {[llength [get_files -quiet $boot_rom]] == 0} {
    add_files -fileset sources_1 -norecurse $boot_rom
}
