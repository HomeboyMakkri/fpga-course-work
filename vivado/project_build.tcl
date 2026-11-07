# Verify the actual .xpr configuration. Close this project in GUI first.
set root [file normalize [file dirname [info script]]]
if {$argc!=1} {error "Pass a new/empty report directory"}
set out [file normalize [lindex $argv 0]]
file mkdir $out
if {[llength [glob -nocomplain -directory $out *]]} {error "Output directory must be empty"}
open_project [file join $root ethernet_generator.xpr]
reset_run synth_1
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]]!="100%"} {error "Synthesis failed"}
launch_runs impl_1 -to_step route_design -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]]!="100%"} {error "Implementation failed"}
open_run impl_1
cd $out
source [file join $root reports.tcl]
close_project
