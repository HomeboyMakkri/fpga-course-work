`timescale 1ns/1ps
`default_nettype none

module pps_generator_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg reset = 1;
    reg valid = 0;
    reg [1:0] channel = 0;
    reg [1:0] mode = 0;
    wire [2:0] pps;
    integer cycle;

    // Periods are 1000, 100 and 10 cycles for practical exhaustive checks.
    pps_generator #(.REF_CLK_HZ(1000)) dut (
        .clk_ref(clk), .reset(reset), .cmd_valid(valid),
        .cmd_channel(channel), .cmd_mode(mode), .pps_out(pps)
    );

    task tick;
        begin @(posedge clk); #1; end
    endtask
    task command(input [1:0] ch, input [1:0] value);
        begin
            @(negedge clk); channel = ch; mode = value; valid = 1;
            tick;
            @(negedge clk); valid = 0;
        end
    endtask
    task require(input condition, input [255:0] message);
        begin if (!condition) begin $display("FAIL: %0s", message); $fatal(1); end end
    endtask

    initial begin
        tick; require(pps == 0, "reset outputs");
        @(negedge clk); reset = 0;
        command(1, 1); // ch1 starts two cycles before ch3
        command(2, 2);
        command(3, 3);
        // At this point channel 1 has advanced four cycles, channel 2 two.
        for (cycle = 1; cycle <= 2000; cycle = cycle + 1) begin
            tick;
            require(pps[0] == (((cycle + 4) % 1000) == 0), "ch1 1 PPS timing");
            require(pps[1] == (((cycle + 2) % 100) == 0), "ch2 10 PPS timing");
            require(pps[2] == ((cycle % 10) == 0), "ch3 100 PPS timing");
        end
        command(3, 0);
        for (cycle = 1; cycle <= 210; cycle = cycle + 1) begin
            tick;
            require(pps[2] == 0, "OFF stays low");
        end
        // Switching ch2 restarts its counter while ch3 remains off.
        command(2, 3);
        for (cycle = 1; cycle <= 30; cycle = cycle + 1) begin
            tick;
            require(pps[1] == ((cycle % 10) == 0), "mode change restarts period");
            require(pps[2] == 0, "other channel remains off");
        end
        command(0, 0); // Invalid channel is ignored.
        for (cycle = 2; cycle <= 21; cycle = cycle + 1) begin
            tick;
            require(pps[1] == ((cycle % 10) == 0), "invalid channel ignored");
        end
        @(negedge clk); reset = 1; tick;
        require(pps == 0, "reset during operation");
        @(negedge clk); reset = 0;
        repeat (20) begin tick; require(pps == 0, "reset clears modes"); end
        $display("PASS: accelerated PPS tests");
        $finish;
    end
endmodule
`default_nettype wire
