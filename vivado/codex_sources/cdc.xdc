# No blanket asynchronous clock groups: preserve upstream FIFO max-delay/skew.
# First synchronizer stages only; second stages retain normal setup/hold.
set_false_path -to [get_pins {mailbox/req_sync_reg[0]/D mailbox/ack_sync_reg[0]/D mdio_sync_reg[0]/D}]
# IDELAYCTRL RDY is an asynchronous status output, sampled only after two stages.
set_false_path -to [get_pins {delay_ready_sync_reg[0]/D}]
set_max_delay -datapath_only 8.0 -from [get_cells ethernet_enable_reg] -to [get_cells {net/rx_enable_sync_reg[0]}]
# Bundled command/result are held through two synchronizer stages and ack.
# Bound their routes to <one net cycle, well below the available settling time.
set_max_delay -datapath_only 8.0 -from [get_cells {mailbox/held_command_reg[*]}] -to [get_cells {mailbox/ref_command_reg[*]}]
set_max_delay -datapath_only 8.0 -from [get_cells {mailbox/held_result_reg[*]}] -to [get_cells {mailbox/result_data_reg[*]}]
set_false_path -to [get_pins -of_objects [get_cells -hier -filter {REF_NAME =~ FD* && ASYNC_REG == TRUE}] -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}]
