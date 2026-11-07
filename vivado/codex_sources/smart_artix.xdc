# Smart Artix schematic v1.3: sheet 2, 6 and 9. Confirm actual board revision.
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property PACKAGE_PIN Y18 [get_ports clk_50m]
set_property IOSTANDARD LVCMOS33 [get_ports clk_50m]
create_clock -name board_clk_50m -period 20.000 [get_ports clk_50m]

# KEY3 is an active-low button in bank 14.
set_property PACKAGE_PIN T20 [get_ports reset_n]
set_property IOSTANDARD LVCMOS33 [get_ports reset_n]

# J5 bank 35 (3.3 V); schematic pin numbers, not board orientation.
set_property PACKAGE_PIN B1 [get_ports {pps_out[0]}]
set_property PACKAGE_PIN C2 [get_ports {pps_out[1]}]
set_property PACKAGE_PIN E1 [get_ports {pps_out[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {pps_out[*]}]
set_property DRIVE 4 [get_ports {pps_out[*]}]
set_property SLEW SLOW [get_ports {pps_out[*]}]
