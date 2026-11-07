`timescale 1ns/1ps
`default_nettype none
// HISTORICAL pre-Ethernet model only. The new multi-clock top uses Vivado UNISIM
// (run_tests.py --top-only); do not compile this model with the Ethernet top.
// Simplified simulation-only model for the fixed 50 MHz -> 10 MHz setup.
// It does not model MMCM timing, jitter, lock accuracy or other configurations.
module MMCME2_BASE #(
    parameter BANDWIDTH = "OPTIMIZED", parameter real CLKIN1_PERIOD = 20.0,
    parameter integer DIVCLK_DIVIDE = 1, parameter real CLKFBOUT_MULT_F = 20.0,
    parameter real CLKOUT0_DIVIDE_F = 100.0, parameter STARTUP_WAIT = "FALSE"
) (input wire CLKIN1, CLKFBIN, RST, PWRDWN,
   output wire CLKFBOUT, output reg CLKOUT0 = 0, output reg LOCKED = 0);
    reg [2:0] phase = 0;
    assign CLKFBOUT = CLKIN1;
    always @(posedge CLKIN1 or posedge RST) begin
        if (RST || PWRDWN) begin phase <= 0; CLKOUT0 <= 0; LOCKED <= 0; end
        else begin
            if (phase == 4) phase <= 0; else phase <= phase + 1;
            CLKOUT0 <= (phase < 2);
            LOCKED <= 1;
        end
    end
endmodule
module BUFG(input wire I, output wire O); assign O = I; endmodule
`default_nettype wire
