# Run with: vivado -mode batch -source build.tcl -tclargs <output-directory>
set source_dir [file normalize [file dirname [info script]]]
if {$argc != 1} { error "Pass a new or empty output directory as the only argument" }
set output_dir [file normalize [lindex $argv 0]]
file mkdir $output_dir
if {[llength [glob -nocomplain -directory $output_dir *]] != 0} {
    error "Output directory must be empty: $output_dir"
}
cd $output_dir
source [file join $source_dir sources.tcl]
read_verilog $rtl_files
read_xdc [file join $source_dir codex_sources smart_artix.xdc]
synth_design -top smart_artix_top -part xc7a50tfgg484-2
foreach f $cdc_files { if {[file extension $f] == ".tcl"} {source $f} else {read_xdc $f} }
opt_design
place_design
route_design
source [file join $source_dir reports.tcl]
