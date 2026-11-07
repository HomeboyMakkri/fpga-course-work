report_timing_summary -delay_type min_max -report_unconstrained -file timing_summary.rpt
report_drc -file drc.rpt
report_clock_utilization -file clocks.rpt
report_clocks -file clock_definitions.rpt
report_cdc -details -file cdc.rpt
report_clock_interaction -file clock_interaction.rpt
check_timing -verbose -file check_timing.rpt
report_exceptions -file exceptions.rpt
report_bus_skew -file bus_skew.rpt
report_io -file io.rpt
report_timing -from [get_ports {phy_rxd[*] phy_rx_ctl}] -delay_type min_max -max_paths 20 -file rgmii_rx_timing.rpt
report_timing -to [get_ports {phy_txd[*] phy_tx_ctl}] -delay_type min_max -max_paths 20 -file rgmii_tx_timing.rpt
report_utilization -file utilization.rpt
write_checkpoint routed.dcp
set fh [open cdc.rpt r]
set cdc_text [read $fh]
close $fh
if {[regexp -line {^CDC-[0-9]+[[:space:]]+Critical[[:space:]]+[1-9]} $cdc_text]} {
    error "Critical CDC findings; no bitstream generated"
}
if {[get_property SLACK [get_timing_paths -delay_type max -max_paths 1]] < 0 ||
    [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]] < 0} {
    error "Timing failed; inspect reports. No bitstream generated."
}
write_bitstream smart_artix_ethernet.bit
