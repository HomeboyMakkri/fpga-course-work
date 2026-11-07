# Read-only discovery: never programs SRAM or Flash.
open_hw
connect_hw_server
set targets [get_hw_targets]
puts "DISCOVERED_TARGETS=$targets"
foreach target $targets {
    current_hw_target $target
    open_hw_target
    foreach device [get_hw_devices] {
        puts "DISCOVERED_DEVICE=$device PART=[get_property PART $device]"
    }
    close_hw_target
}
disconnect_hw_server
close_hw
