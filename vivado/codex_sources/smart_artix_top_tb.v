`timescale 1ns/1ps
`default_nettype none
module smart_artix_top_tb;
    reg clk = 0, reset_n = 0;
    always #10 clk = ~clk;
    wire [2:0] pps;
    integer cycle, count0, count1, count2;
    smart_artix_top #(.PPS_REF_CLK_HZ(1000)) dut (
        .clk_50m(clk), .reset_n(reset_n), .pps_out(pps)
    );
    initial begin
        repeat (10) @(negedge clk);
        reset_n = 1;
        wait(dut.init_step == 3);
        @(negedge dut.clk_10);
        count0 = 0; count1 = 0; count2 = 0;
        for (cycle = 0; cycle < 2000; cycle = cycle + 1) begin
            @(negedge dut.clk_10);
            if (pps[0]) count0 = count0 + 1;
            if (pps[1]) count1 = count1 + 1;
            if (pps[2]) count2 = count2 + 1;
        end
        if (count0 != 2 || count1 != 20 || count2 != 200) begin
            $display("FAIL counts %0d %0d %0d", count0,count1,count2); $fatal(1);
        end
        reset_n = 0;
        repeat (10) @(negedge clk);
        reset_n = 1;
        wait(dut.init_step == 3);
        repeat (10) @(negedge dut.clk_10);
        $display("PASS smart_artix_top init/reset and 3 PPS rates");
        $finish;
    end
    initial begin #1000000; $display("FAIL timeout"); $fatal(1); end
endmodule
`default_nettype wire
