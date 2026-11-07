`timescale 1ns/1ps
`default_nettype none

// Three independent PPS outputs. All inputs are synchronous to clk_ref.
// A valid command restarts only the addressed channel; the first pulse is
// emitted after a complete period. Reset and OFF hold the output low.
module pps_generator #(
    parameter integer REF_CLK_HZ = 10_000_000
) (
    input  wire       clk_ref,
    input  wire       reset,
    input  wire       cmd_valid,
    input  wire [1:0] cmd_channel, // 1, 2, 3
    input  wire [1:0] cmd_mode,    // 0=OFF, 1=1PPS, 2=10PPS, 3=100PPS
    output wire [2:0] pps_out
);

    genvar channel;
    generate
        for (channel = 0; channel < 3; channel = channel + 1) begin : channels
            pps_channel #(.REF_CLK_HZ(REF_CLK_HZ)) u_channel (
                .clk_ref(clk_ref),
                .reset(reset),
                .set_mode(cmd_valid && cmd_channel == (channel + 1)),
                .mode_in(cmd_mode),
                .pulse(pps_out[channel])
            );
        end
    endgenerate
endmodule

module pps_channel #(
    // Must be >= 100 and exactly divisible by 100.
    parameter integer REF_CLK_HZ = 10_000_000
) (
    input  wire       clk_ref,
    input  wire       reset,
    input  wire       set_mode,
    input  wire [1:0] mode_in,
    output reg        pulse
);
    localparam [1:0] OFF = 2'd0, PPS_1 = 2'd1,
                     PPS_10 = 2'd2, PPS_100 = 2'd3;
    localparam [31:0] PERIOD_1 = REF_CLK_HZ;
    localparam [31:0] PERIOD_10 = REF_CLK_HZ / 10;
    localparam [31:0] PERIOD_100 = REF_CLK_HZ / 100;

    reg [1:0] mode;
    reg [31:0] count;
    reg [31:0] period;

    always @* begin
        case (mode)
            PPS_1:   period = PERIOD_1;
            PPS_10:  period = PERIOD_10;
            PPS_100: period = PERIOD_100;
            default: period = 32'd1;
        endcase
    end

    always @(posedge clk_ref) begin
        if (reset) begin
            mode <= OFF;
            count <= 0;
            pulse <= 0;
        end else if (set_mode) begin
            mode <= mode_in;
            count <= 0;
            pulse <= 0;
        end else if (mode == OFF) begin
            count <= 0;
            pulse <= 0;
        end else if (count == period - 1'b1) begin
            count <= 0;
            pulse <= 1;
        end else begin
            count <= count + 1'b1;
            pulse <= 0;
        end
    end
endmodule

`default_nettype wire
