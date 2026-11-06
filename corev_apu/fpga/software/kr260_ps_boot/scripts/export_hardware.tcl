# Read-only project export; does not synthesize, implement or program hardware.
set root [file normalize [file join [file dirname [info script]] .. .. ..]]
set out [file join $root software kr260_ps_boot hardware]
file mkdir $out
open_project -read_only [file join $root ariane_kr260_debug ariane_kr260_debug.xpr]
if {[get_property TOP [get_filesets sources_1]] ne "kr260_top"} { error "Unexpected top" }
if {[get_property NEEDS_REFRESH [get_runs impl_1]]} { error "Implementation is stale; cannot export matching hardware" }
open_run impl_1
write_hw_platform -fixed -include_bit -force -file [file join $out kr260_cva6.xsa]
close_project
