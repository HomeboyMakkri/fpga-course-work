`timescale 1ns/1ps
`default_nettype none
module smart_artix_top #(parameter integer PPS_REF_CLK_HZ=10_000_000) (
 input wire clk_50m, reset_n,
 output wire [2:0] pps_out,
 input wire phy_rx_clk, input wire [3:0] phy_rxd, input wire phy_rx_ctl,
 output wire phy_tx_clk, output wire [3:0] phy_txd, output wire phy_tx_ctl,
 output wire phy_reset_n, output wire phy_mdc, inout wire phy_mdio
);
 wire fb_raw,fb,ref_raw,clk_10,net_raw,clk_net,delay_raw,clk_delay,locked;
 MMCME2_BASE #(.CLKIN1_PERIOD(20.0),.DIVCLK_DIVIDE(1),.CLKFBOUT_MULT_F(20.0),
   .CLKOUT0_DIVIDE_F(100.0),.CLKOUT1_DIVIDE(8),.CLKOUT2_DIVIDE(5),.STARTUP_WAIT("FALSE")) u_mmcm (
   .CLKIN1(clk_50m),.CLKFBIN(fb),.RST(!reset_n),.PWRDWN(1'b0),
   .CLKFBOUT(fb_raw),.CLKOUT0(ref_raw),.CLKOUT1(net_raw),.CLKOUT2(delay_raw),.LOCKED(locked));
 BUFG u_feedback_buf(.I(fb_raw),.O(fb));
 BUFG u_clk10_buf(.I(ref_raw),.O(clk_10));
 BUFG u_net_buf(.I(net_raw),.O(clk_net));
 BUFG u_delay_buf(.I(delay_raw),.O(clk_delay));
 wire arst=!reset_n || !locked;
 wire net_rst,ref_rst;
 reset_release nr(.clk(clk_net),.arst(arst),.rst(net_rst));
 reset_release rr(.clk(clk_10),.arst(arst),.rst(ref_rst));
 wire delay_rst,delay_ready;
 // IDELAYCTRL requires >=50 ns reset with a stable reference clock.
 reset_release #(.STAGES(16)) dr(.clk(clk_delay),.arst(arst),.rst(delay_rst));
 (* IODELAY_GROUP="RGMII_RX" *) IDELAYCTRL delayctrl(.REFCLK(clk_delay),.RST(delay_rst),.RDY(delay_ready));
 (* ASYNC_REG="TRUE" *) reg [1:0] delay_ready_sync=0;
 always @(posedge clk_net) if(net_rst) delay_ready_sync<=0; else delay_ready_sync<={delay_ready_sync[0],delay_ready};
 wire [4:0] delayed_rx;
 genvar d;
 generate for(d=0;d<5;d=d+1) begin: rx_delays
   (* IODELAY_GROUP="RGMII_RX" *) IDELAYE2 #(.DELAY_SRC("IDATAIN"),.IDELAY_TYPE("FIXED"),
     .IDELAY_VALUE(11),.REFCLK_FREQUENCY(200.0),.HIGH_PERFORMANCE_MODE("TRUE"),.SIGNAL_PATTERN("DATA")) delay_in(
     .IDATAIN(d==4 ? phy_rx_ctl : phy_rxd[d]),.DATAIN(1'b0),.DATAOUT(delayed_rx[d]),
     .C(1'b0),.CE(1'b0),.INC(1'b0),.LD(1'b0),.LDPIPEEN(1'b0),.REGRST(1'b0),.CINVCTRL(1'b0),.CNTVALUEIN(5'd0),.CNTVALUEOUT());
 end endgenerate
 wire mdio_out,mdio_oe,phy_ready,phy_reset_release;
 // R52/C670 provide the reset pull-up/RC. Sink low, then release the net;
 // do not actively charge the board's 1 uF reset capacitor from an FPGA output.
 assign phy_reset_n=phy_reset_release ? 1'bz : 1'b0;
 (* KEEP="TRUE" *) wire phy_fault;
 (* KEEP="TRUE" *) wire [15:0] phy_id1,phy_id2,phy_status,delay_readback;
 // MDIO is held for hundreds of net-clock cycles; synchronize its input.
 (* ASYNC_REG="TRUE" *) reg [1:0] mdio_sync=2'b11;
 always @(posedge clk_net) mdio_sync<={mdio_sync[0],phy_mdio};
 rtl8211e_init phy_init(.clk(clk_net),.rst(net_rst),.mdio_in(mdio_sync[1]),
   .mdio_out(mdio_out),.mdio_oe(mdio_oe),.mdc(phy_mdc),.phy_reset_n(phy_reset_release),
   .ready(phy_ready),.fault(phy_fault),.phy_id1(phy_id1),.phy_id2(phy_id2),
   .phy_status(phy_status),.delay_readback(delay_readback));
 assign phy_mdio=mdio_oe ? mdio_out : 1'bz;
 wire cmd_valid,cmd_ready,result_valid,pps_valid;
 wire [4:0] cmd_data;
 wire [1:0] result_data,pps_channel,pps_mode;
 (* KEEP="TRUE" *) wire [31:0] accepted_count,invalid_count,overflow_count;
 reg ethernet_enable=0;
 always @(posedge clk_net) if(net_rst) ethernet_enable<=0; else ethernet_enable<=phy_ready && delay_ready_sync[1];
 ethernet_core net(.clk(clk_net),.clk90(clk_net),.rst(net_rst),.enable(ethernet_enable),
   .phy_rx_clk(phy_rx_clk),.phy_rxd(delayed_rx[3:0]),.phy_rx_ctl(delayed_rx[4]),
   .phy_tx_clk(phy_tx_clk),.phy_txd(phy_txd),.phy_tx_ctl(phy_tx_ctl),
   .cmd_valid(cmd_valid),.cmd_ready(cmd_ready),.cmd_data(cmd_data),
   .result_valid(result_valid),.result_data(result_data),
   .accepted_count(accepted_count),.invalid_count(invalid_count),.overflow_count(overflow_count));
 command_mailbox mailbox(.net_clk(clk_net),.ref_clk(clk_10),.arst(arst),
   .net_rst(net_rst),.ref_rst(ref_rst),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
   .cmd_data(cmd_data),.result_valid(result_valid),.result_data(result_data),
   .pps_valid(pps_valid),.pps_channel(pps_channel),.pps_mode(pps_mode));
 pps_generator #(.REF_CLK_HZ(PPS_REF_CLK_HZ)) u_pps(.clk_ref(clk_10),.reset(ref_rst),
   .cmd_valid(pps_valid),.cmd_channel(pps_channel),.cmd_mode(pps_mode),.pps_out(pps_out));
endmodule
module reset_release #(parameter integer STAGES=4)(input wire clk,arst,output wire rst);
 (* ASYNC_REG="TRUE" *) reg [STAGES-1:0] stages={STAGES{1'b1}};
 always @(posedge clk or posedge arst)
   if(arst) stages<={STAGES{1'b1}}; else stages<={stages[STAGES-2:0],1'b0};
 assign rst=stages[STAGES-1];
endmodule
`default_nettype wire
