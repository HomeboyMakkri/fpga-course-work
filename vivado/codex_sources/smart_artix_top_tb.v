`timescale 1ns/1ps
`default_nettype none
// Full board wrapper smoke test with Vivado UNISIM, not sim_mmcm_model.v.
// Command wires are forced here; wire-level Ethernet is checked by integration_tb.
module smart_artix_top_tb;
 reg clk=0,rxclk=0,reset_n=0;
 always #10 clk=~clk;
 always #4 rxclk=~rxclk;
 wire [2:0] pps;
 tri1 mdio;
 wire txclk,txctl,phyrst,mdc;
 wire [3:0] txd;
 reg injected_valid=0;
 reg [4:0] injected_data=0;
 integer cycle,count0,count1,count2;
 smart_artix_top #(.PPS_REF_CLK_HZ(1000)) dut(
 .clk_50m(clk),.reset_n(reset_n),.pps_out(pps),.phy_rx_clk(rxclk),.phy_rxd(4'b0),.phy_rx_ctl(1'b0),
 .phy_tx_clk(txclk),.phy_txd(txd),.phy_tx_ctl(txctl),.phy_reset_n(phyrst),.phy_mdc(mdc),.phy_mdio(mdio));
 task command(input [1:0] channel,input [1:0] mode);
 begin
   wait(dut.cmd_ready);
   @(negedge dut.clk_net);injected_data={1'b0,channel,mode};injected_valid=1;
   @(negedge dut.clk_net);injected_valid=0;
   wait(dut.result_valid);@(negedge dut.clk_net);
 end
 endtask
 initial begin
   force dut.cmd_valid=injected_valid;
   force dut.cmd_data=injected_data;
   repeat(20) @(negedge clk);reset_n=1;
   wait(!dut.ref_rst);repeat(20) @(negedge dut.clk_10);
   if(pps!==0) $fatal(1,"power-on must be OFF");
   command(1,1);command(2,2);command(3,3);
   count0=0;count1=0;count2=0;
   @(negedge dut.clk_10);
   for(cycle=0;cycle<2000;cycle=cycle+1) begin
     @(negedge dut.clk_10);
     if(pps[0]) count0=count0+1;
     if(pps[1]) count1=count1+1;
     if(pps[2]) count2=count2+1;
   end
   if(count0!=2 || count1!=20 || count2!=200) $fatal(1,"full top PPS counts %d %d %d",count0,count1,count2);
   reset_n=0;repeat(20) @(negedge clk);reset_n=1;
   wait(!dut.ref_rst);repeat(20) @(negedge dut.clk_10);
   if(pps!==0) $fatal(1,"reset must clear PPS");
   $display("PASS full smart_artix_top UNISIM: MMCM clocks, reset, mailbox and PPS");$finish;
 end
 initial begin #1000000;$fatal(1,"top timeout");end
endmodule
`default_nettype wire
