`timescale 1ns/1ps
module ethernet_integration_tb;
 `include "vector_size.vh"
 reg clk=0,refclk=0,rxclk=0,arst=0,run_ref=1,run_net=1;
 always #4 if(run_net) clk=~clk;
 always #50 if(run_ref) refclk=~refclk;
 always #4 rxclk=~rxclk;
 reg [3:0] rxd=0;
 reg rxctl=0;
 wire txclk,txctl;
 wire [3:0] txd;
 wire cv,cr,rv,pv;
 wire [4:0] cd;
 wire [1:0] rd,pc,pm;
 wire [2:0] pps;
 wire [31:0] accepted,invalid,overflow;
 ethernet_core #(.TARGET("GENERIC")) net(.clk(clk),.clk90(clk),.rst(arst),.enable(1'b1),
  .phy_rx_clk(rxclk),.phy_rxd(rxd),.phy_rx_ctl(rxctl),.phy_tx_clk(txclk),.phy_txd(txd),.phy_tx_ctl(txctl),
  .cmd_valid(cv),.cmd_ready(cr),.cmd_data(cd),.result_valid(rv),.result_data(rd),
  .accepted_count(accepted),.invalid_count(invalid),.overflow_count(overflow));
 command_mailbox mailbox(.net_clk(clk),.ref_clk(refclk),.arst(arst),.net_rst(arst),.ref_rst(arst),
  .cmd_valid(cv),.cmd_ready(cr),.cmd_data(cd),.result_valid(rv),.result_data(rd),
  .pps_valid(pv),.pps_channel(pc),.pps_mode(pm));
 pps_generator #(.REF_CLK_HZ(1000)) pps_gen(.clk_ref(refclk),.reset(arst),.cmd_valid(pv),
  .cmd_channel(pc),.cmd_mode(pm),.pps_out(pps));
 integer requests=0,applies=0,replies=0;
 always @(posedge clk) if(!arst) begin
   if(cv && cr) requests=requests+1;
   if(rv) replies=replies+1;
 end
 // Independent cycle scoreboard: commands may restart only the selected channel.
 integer modes[0:2],counts[0:2],periods[0:3];
 integer k;
 reg [2:0] expected;
 initial begin periods[0]=1;periods[1]=1000;periods[2]=100;periods[3]=10; end
 always @(posedge refclk) begin
   expected=0;
   for(k=0;k<3;k=k+1) begin
     if(arst) begin modes[k]=0;counts[k]=0; end
     else if(pv && pc==k+1) begin modes[k]=pm;counts[k]=0; end
     else if(modes[k]!=0) begin
       counts[k]=counts[k]+1;
       if(counts[k]==periods[modes[k]]) begin expected[k]=1;counts[k]=0;end
     end
   end
   if(!arst && pv) applies=applies+1;
   #1;
   if(pps!==expected) $fatal(1,"PPS scoreboard mismatch: got %b expected %b",pps,expected);
 end
 reg [7:0] vectors[0:65535];
 integer j;
 task send_frame(input integer offset,input integer length);
 begin
   // Drive both DDR nibbles 2 ns before sampling edges (PHY integrated delay).
   @(negedge rxclk); #2;
   for(j=0;j<length;j=j+1) begin
     rxctl=1;rxd=vectors[offset+j][3:0]; #4;
     rxd=vectors[offset+j][7:4]; #4;
   end
   rxctl=0;rxd=0;
   repeat(16) @(negedge rxclk);
 end
 endtask
 task settle;
 begin repeat(1800) @(negedge clk); end
 endtask
 task check_requests(input integer n);
 begin if(requests!=n) $fatal(1,"requests got %d expected %d replies=%d accepted=%d invalid=%d overflow=%d busy=%d txstate=%d",requests,n,replies,accepted,invalid,overflow,net.app.busy,net.app.tx_state); end
 endtask
 // Capture physical transmit stream; Python checks FCS, ARP, IP/UDP checksums/replies.
 integer out;
 initial out=$fopen("tx_nibbles.txt","w");
 always @(posedge txclk) begin #1; if(txctl) $fwrite(out,"L%1x\n",txd); else $fwrite(out,"-\n");end
 always @(negedge txclk) begin #1; if(txctl) $fwrite(out,"H%1x\n",txd); end
 initial begin
   $readmemh("frames.hex",vectors,0,VECTOR_BYTES-1);
   repeat(5) @(negedge clk); arst=1; repeat(30) @(negedge clk); arst=0;
   repeat(2000) @(negedge clk);
   `include "stimulus.vh"
   $display("PASS Ethernet RGMII/ARP/IPv4/UDP + CDC/PPS: requests=%0d applies=%0d replies=%0d invalid=%0d overflow=%0d",requests,applies,replies,invalid,overflow);
   $fclose(out);$finish;
 end
 initial begin #5000000; $fatal(1,"integration timeout"); end
endmodule



