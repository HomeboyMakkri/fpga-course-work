`timescale 1ns/1ps
`default_nettype none
module rtl8211e_init #(
 parameter integer RESET_CYCLES=1_250_000,
 parameter integer WAIT_CYCLES=5_000_000,
 parameter integer MDC_HALF=64
) (
 input wire clk,rst, input wire mdio_in,
 output wire mdio_out,mdio_oe, output reg mdc,
 output wire phy_reset_n, output reg ready, output reg fault,
 output reg [15:0] phy_id1,phy_id2,phy_status,delay_readback
);
 reg [23:0] timer=0;
 assign phy_reset_n=!rst && timer>=RESET_CYCLES;
 reg start=0, read_op=0;
 reg [4:0] address=0;
 reg [15:0] write_data=0;
 reg active=0,done=0,ta_error=0;
 reg [15:0] read_data=0;
 reg [63:0] serial=0;
 reg [6:0] bit_index=0;
 reg [15:0] divider=0;
 assign mdio_out=serial[bit_index];
 assign mdio_oe=active && (!read_op || bit_index>17);
 always @(posedge clk) begin
   done<=0;
   if(rst) begin active<=0; mdc<=0; divider<=0; bit_index<=0; ta_error<=0; serial<=0; read_data<=0; end
   else if(start && !active) begin
     serial<={32'hffffffff,2'b01,read_op ? 2'b10 : 2'b01,5'd3,address,2'b10,write_data};
     bit_index<=63; active<=1; divider<=0; mdc<=0; ta_error<=0; read_data<=0;
   end else if(active) begin
     if(divider==MDC_HALF-1) begin
       divider<=0; mdc<=~mdc;
       if(!mdc) begin
         if(read_op && bit_index==16 && mdio_in!=0) ta_error<=1;
         if(read_op && bit_index<16) read_data<={read_data[14:0],mdio_in};
       end else if(bit_index==0) begin active<=0; done<=1; end
       else bit_index<=bit_index-1'b1;
     end else divider<=divider+1'b1;
   end
 end
 reg [4:0] step=0;
 reg waiting=0;
 reg [15:0] saved_delay=0;
 always @(posedge clk) begin
   start<=0;
   if(rst) begin timer<=0; step<=0; waiting<=0; ready<=0; fault<=0;
     read_op<=0; address<=0; write_data<=0; saved_delay<=0;
     phy_id1<=0; phy_id2<=0; phy_status<=0; delay_readback<=0;
   end else if(timer<RESET_CYCLES+WAIT_CYCLES) timer<=timer+1'b1;
   else if(!fault) begin
     if(!waiting && !active) begin
       start<=1; waiting<=1;
       case(step)
         0: begin read_op<=1; address<=2; end
         1: begin read_op<=1; address<=3; end
         2: begin read_op<=0; address<=31; write_data<=7; end
         3: begin read_op<=0; address<=30; write_data<=16'h00a4; end
         4: begin read_op<=1; address<=28; end
         5: begin read_op<=0; address<=28; write_data<=saved_delay | 16'h3800; end
         6: begin read_op<=1; address<=28; end
         7: begin read_op<=0; address<=31; write_data<=0; end
         // Disable EEE advertisement: MMD 7 register 0x3c via clause 22.
         8: begin read_op<=0; address<=13; write_data<=16'h0007; end
         9: begin read_op<=0; address<=14; write_data<=16'h003c; end
         10: begin read_op<=0; address<=13; write_data<=16'h4007; end
         11: begin read_op<=0; address<=14; write_data<=0; end
         12: begin read_op<=0; address<=13; write_data<=0; end
         13: begin read_op<=0; address<=4; write_data<=16'h0141; end
         14: begin read_op<=0; address<=9; write_data<=16'h0200; end
         15: begin read_op<=0; address<=0; write_data<=16'h1200; end
         default: begin read_op<=1; address<=1; end
       endcase
     end
     if(done) begin
       waiting<=0;
       if(read_op && ta_error) begin fault<=1; ready<=0; end
       else case(step)
         0: begin phy_id1<=read_data; if(read_data!=16'h001c) fault<=1; step<=1; end
         1: begin phy_id2<=read_data; if(read_data!=16'hc915) fault<=1; step<=2; end
         4: begin saved_delay<=read_data; step<=5; end
         6: begin delay_readback<=read_data; if((read_data & 16'h3800)!=16'h3800) fault<=1; step<=7; end
         16: begin phy_status<=read_data; ready<=read_data[2] && read_data[5]; end
         default: step<=step+1'b1;
       endcase
     end
   end
 end
endmodule
`default_nettype wire

