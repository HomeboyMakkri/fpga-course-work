# Vivado 2019.1. SRAM only; no configuration-memory/Flash operations.
# Arguments: absolute .bit path, exact hw_target cable serial.
if {$argc != 2} {error "Usage: -tclargs <bitstream.bit> <cable-serial>"}
set bitfile [file normalize [lindex $argv 0]]
set serial [lindex $argv 1]
if {![file isfile $bitfile] || [file extension $bitfile] ne ".bit"} {
    error "Expected an existing .bit file: $bitfile"
}
open_hw
connect_hw_server
set matches {}
foreach target [get_hw_targets] {
    if {[file tail $target] eq $serial} {lappend matches $target}
}
if {[llength $matches] != 1} {error "Expected exactly one cable with serial $serial; found $matches"}
current_hw_target [lindex $matches 0]
open_hw_target
set devices [get_hw_devices]
if {[llength $devices] != 1} {error "Expected one FPGA in the chain; found $devices"}
set device [lindex $devices 0]
if {[get_property PART $device] ne "xc7a50t"} {
    error "Wrong FPGA: $device PART=[get_property PART $device]"
}
puts "VERIFIED_TARGET=[current_hw_target] DEVICE=$device PART=[get_property PART $device]"
set_property PROGRAM.FILE $bitfile $device
program_hw_devices $device
refresh_hw_device -update_hw_probes false $device
if {[get_property REGISTER.CONFIG_STATUS.BIT14_DONE_PIN $device] != 1 ||
    [get_property REGISTER.CONFIG_STATUS.BIT00_CRC_ERROR $device] != 0 ||
    [get_property REGISTER.CONFIG_STATUS.BIT15_IDCODE_ERROR $device] != 0} {
    error "FPGA configuration status did not pass DONE/CRC/IDCODE checks"
}
puts "SRAM_PROGRAMMING_COMPLETED FILE=$bitfile"
foreach prop [lsort [list_property $device]] {
    if {[regexp -nocase {DONE|CONFIG_STATUS|IDCODE|IS_PROGRAMMED} $prop]} {
        puts "DEVICE_STATUS $prop=[get_property $prop $device]"
    }
}
close_hw_target
disconnect_hw_server
close_hw
