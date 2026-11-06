# Codex overnight synthesis runner/validator for the existing CVA6 VC707 project.
# By default this validates the current synth_1 run. Set CODEX_RESET_SYNTH=1 to
# reset and rerun synth_1; no implementation or bitstream commands are used.

set project_file [file normalize [file join [file dirname [info script]] .. ariane.xpr]]
set report_dir [file normalize [file join [file dirname [info script]] .. .. .. reports codex_overnight]]
file mkdir $report_dir

set_param general.maxThreads 1
open_project $project_file

set synth_run [get_runs synth_1]
if {[llength $synth_run] != 1} {
    error "Expected exactly one synth_1 run"
}

if {[info exists ::env(CODEX_RESET_SYNTH)] && $::env(CODEX_RESET_SYNTH) eq "1"} {
    reset_run $synth_run
    launch_runs $synth_run -jobs 1
    wait_on_run $synth_run
}

set status [get_property STATUS $synth_run]
set progress [get_property PROGRESS $synth_run]
set run_dir [get_property DIRECTORY $synth_run]
puts "CODEX_SYNTH_STATUS=$status"
puts "CODEX_SYNTH_PROGRESS=$progress"
puts "CODEX_SYNTH_DIRECTORY=$run_dir"

if {![string match "*Complete*" $status] || [string match "*Failed*" $status]} {
    error "synth_1 is not complete and successful: $status"
}

open_run $synth_run
report_utilization -file [file join $report_dir synth_utilization.rpt]
report_timing_summary -file [file join $report_dir synth_timing_summary.rpt]
check_timing -file [file join $report_dir synth_check_timing.rpt]

close_project
puts "CODEX_SYNTH_VALIDATION=SUCCESS"
