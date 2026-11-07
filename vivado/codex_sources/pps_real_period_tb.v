`timescale 1ns/1ps
`default_nettype none
module pps_real_period_tb;
    reg clk = 0;
    always #1 clk = ~clk;
    reg reset = 1, valid = 0;
    reg [1:0] channel = 0, mode = 0;
    wire [2:0] pps;
    integer i;
    pps_generator dut (.clk_ref(clk), .reset(reset), .cmd_valid(valid),
                       .cmd_channel(channel), .cmd_mode(mode), .pps_out(pps));
    task tick; begin @(posedge clk); #0.1; end endtask
    task command(input [1:0] ch, input [1:0] m);
        begin @(negedge clk); channel = ch; mode = m; valid = 1; tick;
              @(negedge clk); valid = 0; end
    endtask
    initial begin
        tick; @(negedge clk); reset = 0;
        command(1, 1); command(2, 2); command(3, 3);
        for (i = 1; i <= 10_000_000; i = i + 1) begin
            tick;
            if (pps[0] !== (((i+4) % 10_000_000) == 0) ||
                pps[1] !== (((i+2) % 1_000_000) == 0) ||
                pps[2] !== ((i % 100_000) == 0)) begin
                $display("FAIL: real period at cycle %0d, pps=%b", i, pps); $fatal(1);
            end
        end
        $display("PASS: 10 MHz real periods 10000000, 1000000, 100000 cycles");
        $finish;
    end
endmodule
`default_nettype wire
