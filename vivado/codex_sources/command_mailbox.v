`timescale 1ns/1ps
`default_nettype none
// One outstanding command. Bundled data stays stable until acknowledgement.
// Both halves MUST share arst; independent domain resets are not supported.
module command_mailbox (
 input wire net_clk, ref_clk, arst, net_rst, ref_rst,
 input wire cmd_valid, output wire cmd_ready, input wire [4:0] cmd_data,
 output reg result_valid, output reg [1:0] result_data,
 output wire pps_valid, output wire [1:0] pps_channel, pps_mode
);
 reg [4:0] held_command=0;
 reg request=0, acknowledge=0;
 reg [1:0] held_result=0;
 (* ASYNC_REG="TRUE" *) reg [1:0] req_sync=0, ack_sync=0;
 reg seen_ack=0;
 reg [1:0] modes [0:2];
 assign cmd_ready = !net_rst && (request == ack_sync[1]);
 reg pending=0;
 reg [4:0] ref_command=0;
 wire apply = !ref_rst && !pending && (req_sync[1] != acknowledge);
 assign pps_channel = ref_command[3:2];
 assign pps_mode = ref_command[1:0];
 assign pps_valid = pending && !ref_command[4];
 always @(posedge net_clk or posedge net_rst) begin
   if (net_rst) begin
     held_command<=0; request<=0; ack_sync<=0; seen_ack<=0;
     result_valid<=0; result_data<=0;
   end else begin
     ack_sync <= {ack_sync[0],acknowledge};
     result_valid <= 0;
     if (!net_rst) begin
       if (cmd_valid && cmd_ready) begin held_command<=cmd_data; request<=~request; end
       if (ack_sync[1] != seen_ack) begin
         seen_ack<=ack_sync[1]; result_data<=held_result; result_valid<=1;
       end
     end
   end
 end
 integer i;
 always @(posedge ref_clk or posedge ref_rst) begin
   if (ref_rst) begin
     req_sync<=0; acknowledge<=0; held_result<=0;
     pending<=0; ref_command<=0;
     for(i=0;i<3;i=i+1) modes[i]<=0;
   end else begin
     req_sync <= {req_sync[0],request};
     pending<=apply;
     if (apply) ref_command<=held_command;
     if (pending) begin
       if (ref_command[4]) held_result<=modes[ref_command[3:2]-1'b1];
       else begin
         modes[ref_command[3:2]-1'b1]<=ref_command[1:0];
         held_result<=ref_command[1:0];
       end
       acknowledge<=req_sync[1];
     end
   end
 end
endmodule
`default_nettype wire
