`timescale 1ns/1ps
module rtl8211e_init_tb;
 reg clk=0,rst=1;
 always #4 clk=~clk;
 wire mdc,mo,oe,reset_n,ready,fault;
 tri1 mdio;
 reg slave_drive=0,slave_bit=1,absent=0,wrong_id=0,link_up=1;
 assign mdio=oe ? mo : 1'bz;
 assign mdio=slave_drive && !absent ? slave_bit : 1'bz;
 wire [15:0] id1,id2,status,delays;
 rtl8211e_init #(.RESET_CYCLES(20),.WAIT_CYCLES(80),.MDC_HALF(4)) dut(
 .clk(clk),.rst(rst),.mdio_in(mdio),.mdio_out(mo),.mdio_oe(oe),.mdc(mdc),
 .phy_reset_n(reset_n),.ready(ready),.fault(fault),.phy_id1(id1),.phy_id2(id2),
 .phy_status(status),.delay_readback(delays));
 integer bit_count=0,transaction=0,eee_step=0;
 reg [63:0] frame=0;
 reg [15:0] response=0,delay_reg=16'h0456,page=0,extpage=0;
 reg reading=0;
 reg [4:0] address=0;
 always @(negedge reset_n) begin bit_count=0;reading=0;slave_drive=0;page=0;extpage=0;delay_reg=16'h0456; end
 always @(posedge mdc) begin
   frame={frame[62:0],mdio};
   if(bit_count==45) begin
     if(frame[13:12]!=2'b01 || frame[9:5]!=3) $fatal(1,"MDIO ST/address");
     reading=frame[11:10]==2'b10;
     address=frame[4:0];
     case(address)
       2: response=wrong_id ? 16'hffff : 16'h001c;
       3: response=16'hc915;
       28: begin
         if(page!=7 || extpage!=16'ha4) $fatal(1,"delay page selection");
         response=delay_reg;
       end
       1: response=link_up ? 16'h0024 : 0;
       default: response=0;
     endcase
   end
   if(bit_count==63) begin
     transaction=transaction+1;
     if(!reading) begin
       if(frame[17:16]!=2'b10) $fatal(1,"write TA");
       case(address)
         31: page=frame[15:0];
         30: extpage=frame[15:0];
         28: delay_reg=frame[15:0];
         13: begin
           if(eee_step==0 && frame[15:0]==7) eee_step=1;
           else if(eee_step==2 && frame[15:0]==16'h4007) eee_step=3;
           else if(eee_step==4 && frame[15:0]==0) eee_step=5;
           else $fatal(1,"EEE MMD control");
         end
         14: begin
           if(eee_step==1 && frame[15:0]==16'h003c) eee_step=2;
           else if(eee_step==3 && frame[15:0]==0) eee_step=4;
           else $fatal(1,"EEE MMD data");
         end
         4: if(frame[15:0]!=16'h0141) $fatal(1,"half duplex advertised");
         9: if(frame[15:0]!=16'h0200) $fatal(1,"gigabit advertisement");
         0: if(frame[15:0]!=16'h1200 || eee_step!=5) $fatal(1,"AN restart / EEE disable");
       endcase
     end
     bit_count=0;reading=0;
   end else bit_count=bit_count+1;
 end
 always @(negedge mdc) begin
   slave_drive=reading && bit_count>=47;
   if(bit_count==47) slave_bit=0;
   else if(bit_count>=48) slave_bit=response[63-bit_count];
 end
 task reset_phy;
 begin rst=1;repeat(10) @(negedge clk);rst=0;end
 endtask
 initial begin
   reset_phy;
   wait(ready || fault);
   if(fault || id1!=16'h001c || id2!=16'hc915 || delays!=16'h3c56) $fatal(1,"PHY init/readback failed");
   link_up=0;wait(!ready);link_up=1;wait(ready);
   wrong_id=1;reset_phy;wait(fault);
   if(ready) $fatal(1,"wrong ID enabled");
   wrong_id=0;absent=1;reset_phy;wait(fault);
   if(ready) $fatal(1,"missing PHY enabled");
   $display("PASS MDIO wire model: ID, RMW preserved bits, readback, AN, link loss/recovery, wrong ID, missing TA");$finish;
 end
 initial begin #1000000;$fatal(1,"MDIO timeout");end
endmodule
