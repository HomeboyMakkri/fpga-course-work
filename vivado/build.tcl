# Run with: vivado -mode batch -source build.tcl -tclargs <output-directory>
set source_dir [file normalize [file dirname [info script]]]
if {$argc != 1} { error "Pass a new or empty output directory as the only argument" }
set output_dir [file normalize [lindex $argv 0]]
file mkdir $output_dir
if {[llength [glob -nocomplain -directory $output_dir *]] != 0} {
    error "Output directory must be empty: $output_dir"
}
cd $output_dir
read_verilog [list [file join $source_dir codex_sources pps_generator.v] [file join $source_dir codex_sources smart_artix_top.v]]
synth_design -top smart_artix_top -part xc7a50tfgg484-2
read_xdc [file join $source_dir codex_sources smart_artix.xdc]
opt_design
place_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -file timing_summary.rpt
report_drc -file drc.rpt
report_clock_utilization -file clocks.rpt
report_utilization -file utilization.rpt
write_bitstream smart_artix_pps.bit
