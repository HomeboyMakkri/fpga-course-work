set src_root [file normalize [file dirname [info script]]]
set rtl_files {}
foreach f {pps_generator command_mailbox udp_pps_control rtl8211e_init ethernet_core smart_artix_top} {
    lappend rtl_files [file join $src_root codex_sources $f.v]
}
set vendor_root [file join $src_root third_party verilog-ethernet]
set rtl_files [concat $rtl_files [lsort [glob $vendor_root/rtl/*.v]] [lsort [glob $vendor_root/lib/axis/rtl/*.v]]]
set cdc_files [list $vendor_root/syn/vivado/rgmii_phy_if.tcl $vendor_root/syn/vivado/eth_mac_1g_rgmii.tcl $vendor_root/syn/vivado/eth_mac_fifo.tcl $vendor_root/lib/axis/syn/vivado/axis_async_fifo.tcl $vendor_root/lib/axis/syn/vivado/sync_reset.tcl [file join $src_root codex_sources cdc.xdc]]
