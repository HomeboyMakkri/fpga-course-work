# Run only while ethernet_generator.xpr is closed in GUI.
set root [file normalize [file dirname [info script]]]
source [file join $root sources.tcl]
open_project [file join $root ethernet_generator.xpr]
add_files -norecurse $rtl_files
foreach f $cdc_files {
    add_files -fileset constrs_1 -norecurse $f
    if {[file extension $f]==".tcl"} {set_property FILE_TYPE TCL [get_files $f]}
    set_property USED_IN_SYNTHESIS false [get_files $f]
    set_property PROCESSING_ORDER LATE [get_files $f]
}
set_property top smart_artix_top [get_filesets sources_1]
add_files -fileset sim_1 -norecurse [file join $root codex_sources smart_artix_top_tb.v]
update_compile_order -fileset sources_1
close_project
