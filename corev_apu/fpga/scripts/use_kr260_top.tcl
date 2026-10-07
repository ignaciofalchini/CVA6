# Apply the top rename to the open project, including an existing GUI session.
# Keep the project directory and Block Designs at their existing paths.
set kr260_fpga_dir [file normalize [file join [file dirname [info script]] ..]]
set kr260_top_source [file join $kr260_fpga_dir src kr260_top.sv]
if {[llength [current_project -quiet]] != 1} {
    error "Open the KR260 project before sourcing this script"
}
set kr260_expected_project [file join $kr260_fpga_dir ariane_kr260_debug]
if {[file normalize [get_property DIRECTORY [current_project]]] ne $kr260_expected_project} {
    error "The open project is not the expected KR260 project"
}
if {![file isfile $kr260_top_source]} {
    error "Missing source: $kr260_top_source"
}
set kr260_old_source [get_files -quiet -of_objects [get_filesets sources_1] *ariane_kr260_debug.sv]
if {[llength [get_files -quiet $kr260_top_source]] == 0} {
    add_files -fileset sources_1 -norecurse $kr260_top_source
}
set_property file_type SystemVerilog [get_files $kr260_top_source]
if {[llength $kr260_old_source] != 0} {
    remove_files $kr260_old_source
}
set_property top kr260_top [get_filesets sources_1]
update_compile_order -fileset sources_1
puts "KR260 top updated: [get_property TOP [get_filesets sources_1]]"
