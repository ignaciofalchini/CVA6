# Select the separately generated KR260 DRAM smoke-test ROM in an existing
# Vivado project. The normal bootrom_64 source remains present and is still the
# default when KR260_MEMORY_TEST_BOOTROM is not defined.

set test_rom [file normalize src/bootrom/kr260_memory_test/bootrom_kr260_memory_test.sv]
if {![file exists $test_rom]} {
    error "Generate the test ROM first: make -C src/bootrom/kr260_memory_test all"
}

if {[llength [get_files -quiet $test_rom]] == 0} {
    add_files -fileset sources_1 -norecurse $test_rom
}

set defines [get_property verilog_define [current_fileset]]
if {[lsearch -exact $defines KR260_MEMORY_TEST_BOOTROM] < 0} {
    lappend defines KR260_MEMORY_TEST_BOOTROM
    set_property verilog_define $defines [current_fileset]
}
