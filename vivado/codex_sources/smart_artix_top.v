`timescale 1ns/1ps
`default_nettype none

// Board bring-up: fixed 1, 10 and 100 PPS until Ethernet control is added.
module smart_artix_top #(
    parameter integer PPS_REF_CLK_HZ = 10_000_000
) (
    input  wire       clk_50m,
    input  wire       reset_n,
    output wire [2:0] pps_out
);
    wire clk_fb_raw, clk_fb, clk_10_raw, clk_10, locked;
    wire mmcm_reset = ~reset_n;

    // 50 MHz * 20 / 100 = 10 MHz. VCO = 1000 MHz.
    MMCME2_BASE #(
        .BANDWIDTH("OPTIMIZED"),
        .CLKIN1_PERIOD(20.0),
        .DIVCLK_DIVIDE(1),
        .CLKFBOUT_MULT_F(20.0),
        .CLKOUT0_DIVIDE_F(100.0),
        .STARTUP_WAIT("FALSE")
    ) u_mmcm (
        .CLKIN1(clk_50m), .CLKFBIN(clk_fb), .RST(mmcm_reset), .PWRDWN(1'b0),
        .CLKFBOUT(clk_fb_raw), .CLKOUT0(clk_10_raw), .LOCKED(locked)
    );
    BUFG u_feedback_buf (.I(clk_fb_raw), .O(clk_fb));
    BUFG u_clk10_buf (.I(clk_10_raw), .O(clk_10));

    // Assert reset immediately; release only after two live 10 MHz edges.
    (* ASYNC_REG = "TRUE" *) reg [1:0] reset_sync = 2'b11;
    always @(posedge clk_10 or negedge locked) begin
        if (!locked) reset_sync <= 2'b11;
        else reset_sync <= {reset_sync[0], 1'b0};
    end
    wire pps_reset = reset_sync[1];

    reg [1:0] init_step = 0;
    wire cmd_valid = init_step != 3;
    wire [1:0] cmd_channel = init_step + 1'b1;
    wire [1:0] cmd_mode = init_step + 1'b1;
    always @(posedge clk_10) begin
        if (pps_reset) init_step <= 0;
        else if (init_step != 3) init_step <= init_step + 1'b1;
    end
    pps_generator #(.REF_CLK_HZ(PPS_REF_CLK_HZ)) u_pps (
        .clk_ref(clk_10), .reset(pps_reset), .cmd_valid(cmd_valid),
        .cmd_channel(cmd_channel), .cmd_mode(cmd_mode), .pps_out(pps_out)
    );
endmodule
`default_nettype wire
