`timescale 1ns/1ps
`default_nettype none
// UDP payload: channel (1..3), mode (0..3), or 0x80 to read mode.
// Reply after PPS-domain application: 0x00, channel, applied mode, 0x01.
// Malformed/busy packets are drained, counted, and receive no reply.
module udp_pps_control (
 input wire clk,rst,
 input wire hdr_valid, output wire hdr_ready,
 input wire [47:0] dest_mac,
 input wire [31:0] dest_ip,source_ip,
 input wire [15:0] source_port,dest_port,udp_length,ip_length,udp_checksum,
 input wire [3:0] ip_ihl, input wire [2:0] ip_flags,
 input wire [12:0] fragment_offset,
 input wire [7:0] data, input wire valid,last,user,
 output reg cmd_valid, input wire cmd_ready, output reg [4:0] cmd_data,
 input wire result_valid, input wire [1:0] result_data,
 output wire tx_hdr_valid, input wire tx_hdr_ready,
 output reg [31:0] tx_dest_ip, output reg [15:0] tx_dest_port,
 output wire [7:0] tx_data, output wire tx_valid, input wire tx_ready,
 output wire tx_last,
 output reg [31:0] accepted_count, invalid_count, overflow_count
);
 reg frame=0, eligible=0, was_busy=0, bad=0, busy=0;
 reg [1:0] count=0;
 reg [7:0] channel=0;
 reg [31:0] peer_ip=0;
 reg [15:0] peer_port=0;
 reg [19:0] checksum_sum=0;
 reg checksum_disabled=0;
 reg [2:0] tx_state=0; // 0 wait, 1 header, 2..5 reply bytes
 reg [1:0] reply_mode=0;
 reg [7:0] reply_channel=0;
 wire [20:0] sum_payload={1'b0,checksum_sum}+{5'b0,channel,data};
 wire [16:0] folded={1'b0,sum_payload[15:0]}+sum_payload[20:16];
 wire [16:0] folded2={1'b0,folded[15:0]}+folded[16];
 wire checksum_ok=checksum_disabled || folded2==17'h0ffff;
 assign hdr_ready=!frame;
 assign tx_hdr_valid=tx_state==1;
 assign tx_valid=tx_state>=2;
 assign tx_last=tx_state==5;
 assign tx_data=tx_state==2 ? 8'h00 : tx_state==3 ? reply_channel :
                tx_state==4 ? {6'b0,reply_mode} : 8'h01;
 always @(posedge clk) begin
   if (rst) begin
     frame<=0; eligible<=0; was_busy<=0; bad<=0; busy<=0; count<=0;
     channel<=0; peer_ip<=0; peer_port<=0; checksum_sum<=0; checksum_disabled<=0;
     tx_state<=0; reply_mode<=0; reply_channel<=0;
     cmd_valid<=0; cmd_data<=0; tx_dest_ip<=0; tx_dest_port<=0;
     accepted_count<=0; invalid_count<=0; overflow_count<=0;
   end else begin
     cmd_valid<=0;
     if (hdr_valid && hdr_ready) begin
       frame<=1; count<=0; bad<=0; was_busy<=busy || !cmd_ready;
       eligible<=dest_mac==48'h020000000050 && dest_ip==32'hc0a80180 &&
         dest_port==1234 && udp_length==10 && ip_length==30 && ip_ihl==5 &&
         !ip_flags[0] && fragment_offset==0;
       peer_ip<=source_ip; peer_port<=source_port;
       checksum_disabled<=udp_checksum==0;
       checksum_sum<={4'b0,source_ip[31:16]}+{4'b0,source_ip[15:0]}+
          20'hc0a8+20'h0180+20'd17+20'd20+
          {4'b0,source_port}+{4'b0,dest_port}+{4'b0,udp_checksum};
     end
     if (frame && valid) begin
       bad<=bad || user;
       if (count==0) channel<=data;
       if (count!=3) count<=count+1'b1;
       if (last) begin
         frame<=0;
         if (eligible && count==1 && !bad && !user && channel>=1 && channel<=3 &&
             (data<=3 || data==8'h80) && checksum_ok) begin
           if (was_busy || busy || !cmd_ready) overflow_count<=overflow_count+1;
           else begin
             cmd_data<={data==8'h80,channel[1:0],data[1:0]}; cmd_valid<=1;
             busy<=1; accepted_count<=accepted_count+1;
             tx_dest_ip<=peer_ip; tx_dest_port<=peer_port; reply_channel<=channel;
           end
         end else invalid_count<=invalid_count+1;
       end
     end
     if (result_valid && busy && tx_state==0) begin reply_mode<=result_data; tx_state<=1; end
     if (tx_state==1 && tx_hdr_ready) tx_state<=2;
     if (tx_valid && tx_ready) begin
       if (tx_last) begin tx_state<=0; busy<=0; end
       else tx_state<=tx_state+1'b1;
     end
   end
 end
endmodule
`default_nettype wire
