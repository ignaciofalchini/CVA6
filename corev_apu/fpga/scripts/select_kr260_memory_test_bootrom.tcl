# Add the generated KR260 memory-test ROM to a Vivado project.
# ariane_kr260 instantiates this ROM unconditionally.

set test_rom [file normalize src/bootrom/kr260_memory_test/bootrom_kr260_memory_test.sv]
if {![file exists $test_rom]} {
    error "Generate the test ROM first: make -C src/bootrom/kr260_memory_test all"
}

if {[llength [get_files -quiet $test_rom]] == 0} {
    add_files -fileset sources_1 -norecurse $test_rom
}
