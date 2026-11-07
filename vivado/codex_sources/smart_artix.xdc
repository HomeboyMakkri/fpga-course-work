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

# RTL8211E-VB-CG: Smart Artix v1.3 sheet 2 BANK14 and sheet 5.
set_property -dict {PACKAGE_PIN W19 IOSTANDARD LVCMOS33} [get_ports {phy_rx_clk}]
set_property -dict {PACKAGE_PIN AA20 IOSTANDARD LVCMOS33} [get_ports {phy_rxd[0]}]
set_property -dict {PACKAGE_PIN W22 IOSTANDARD LVCMOS33} [get_ports {phy_rxd[1]}]
set_property -dict {PACKAGE_PIN W21 IOSTANDARD LVCMOS33} [get_ports {phy_rxd[2]}]
set_property -dict {PACKAGE_PIN W20 IOSTANDARD LVCMOS33} [get_ports {phy_rxd[3]}]
set_property -dict {PACKAGE_PIN AA21 IOSTANDARD LVCMOS33} [get_ports {phy_rx_ctl}]
set_property -dict {PACKAGE_PIN AB21 IOSTANDARD LVCMOS33} [get_ports {phy_tx_clk}]
set_property -dict {PACKAGE_PIN AB20 IOSTANDARD LVCMOS33} [get_ports {phy_txd[0]}]
set_property -dict {PACKAGE_PIN AA19 IOSTANDARD LVCMOS33} [get_ports {phy_txd[1]}]
set_property -dict {PACKAGE_PIN Y19 IOSTANDARD LVCMOS33} [get_ports {phy_txd[2]}]
set_property -dict {PACKAGE_PIN AB18 IOSTANDARD LVCMOS33} [get_ports {phy_txd[3]}]
set_property -dict {PACKAGE_PIN AA18 IOSTANDARD LVCMOS33} [get_ports {phy_tx_ctl}]
set_property -dict {PACKAGE_PIN V19 IOSTANDARD LVCMOS33} [get_ports {phy_reset_n}]
set_property -dict {PACKAGE_PIN V17 IOSTANDARD LVCMOS33} [get_ports {phy_mdio}]
set_property -dict {PACKAGE_PIN W17 IOSTANDARD LVCMOS33} [get_ports {phy_mdc}]
set_property SLEW FAST [get_ports {phy_tx_clk phy_txd[*] phy_tx_ctl}]
set_property DRIVE 8 [get_ports {phy_tx_clk phy_txd[*] phy_tx_ctl}]
create_clock -name rgmii_rx -period 8.000 [get_ports phy_rx_clk]
# Worst edge rate is 1 Gb/s. PHY internal RX delay enabled and read back by MDIO.
# Table 65: transmitter integrated-delay setup/hold >=1.2 ns.
# Provisional board data/clock skew allowance +/-0.2 ns, to measure on real board.
set_input_delay -clock rgmii_rx -max 3.0 [get_ports {phy_rxd[*] phy_rx_ctl}]
set_input_delay -clock rgmii_rx -min 1.0 [get_ports {phy_rxd[*] phy_rx_ctl}]
set_input_delay -clock rgmii_rx -clock_fall -add_delay -max 3.0 [get_ports {phy_rxd[*] phy_rx_ctl}]
set_input_delay -clock rgmii_rx -clock_fall -add_delay -min 1.0 [get_ports {phy_rxd[*] phy_rx_ctl}]
# TX clock forwarded without FPGA phase shift. Virtual PHY capture is +2 ns
# inside the PHY (both delay bits set). Receiver setup/hold 1 ns +0.2 margin.
create_generated_clock -name rgmii_tx_pin -source [get_pins u_mmcm/CLKOUT1] -divide_by 1 [get_ports phy_tx_clk]
create_generated_clock -name phy_tx_capture -source [get_ports phy_tx_clk] -edges {1 2 3} -edge_shift {2.0 2.0 2.0} -add -master_clock rgmii_tx_pin [get_ports phy_tx_clk]
set_output_delay -clock phy_tx_capture -max 1.2 [get_ports {phy_txd[*] phy_tx_ctl}]
set_output_delay -clock phy_tx_capture -min -1.2 [get_ports {phy_txd[*] phy_tx_ctl}]
set_output_delay -clock phy_tx_capture -clock_fall -add_delay -max 1.2 [get_ports {phy_txd[*] phy_tx_ctl}]
set_output_delay -clock phy_tx_capture -clock_fall -add_delay -min -1.2 [get_ports {phy_txd[*] phy_tx_ctl}]
# Asynchronous lab outputs/reset, not synchronous external interfaces.
set_false_path -to [get_ports {pps_out[*] phy_reset_n}]
set_false_path -from [get_ports reset_n]
# Management output has >500 ns stable setup at ~0.977 MHz MDC. Bound routing
# against net clock rather than excluding it; input uses a two-flop synchronizer.
set_output_delay -clock [get_clocks -of_objects [get_pins u_mmcm/CLKOUT1]] -max 2.0 [get_ports {phy_mdio phy_mdc}]
set_output_delay -clock [get_clocks -of_objects [get_pins u_mmcm/CLKOUT1]] -min -2.0 [get_ports {phy_mdio phy_mdc}]

# Only first MDIO synchronizer input is asynchronous; the engine samples >500 ns later.
set_false_path -from [get_ports phy_mdio] -to [get_pins {mdio_sync_reg[0]/D}]
set_multicycle_path -setup 32 -to [get_ports {phy_mdio phy_mdc}]
set_multicycle_path -hold 31 -to [get_ports {phy_mdio phy_mdc}]
