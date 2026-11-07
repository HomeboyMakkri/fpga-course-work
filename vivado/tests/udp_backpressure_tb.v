`timescale 1ns/1ps
module udp_backpressure_tb;
 reg clk=0,rst=1,hv=0,v=0,last=0,user=0,rv=0,thr=0,tr=0;
 always #4 clk=~clk;
 reg [7:0] data=0;
 wire hr,cv,thv,tv,tl;
 wire [4:0] cd;
 wire [7:0] td;
 wire [31:0] ti,accepted,invalid,overflow;
 wire [15:0] tp;
 integer commands=0,bytes_sent=0,k;
 reg [7:0] expected[0:3];
 udp_pps_control dut(.clk(clk),.rst(rst),.hdr_valid(hv),.hdr_ready(hr),
 .dest_mac(48'h020000000050),.dest_ip(32'hc0a80180),.source_ip(32'hc0a8010a),
 .source_port(16'd40000),.dest_port(16'd1234),.udp_length(16'd10),.ip_length(16'd30),
 .udp_checksum(16'd0),.ip_ihl(4'd5),.ip_flags(3'd0),.fragment_offset(13'd0),
 .data(data),.valid(v),.last(last),.user(user),.cmd_valid(cv),.cmd_ready(1'b1),.cmd_data(cd),
 .result_valid(rv),.result_data(2'd3),.tx_hdr_valid(thv),.tx_hdr_ready(thr),
 .tx_dest_ip(ti),.tx_dest_port(tp),.tx_data(td),.tx_valid(tv),.tx_ready(tr),.tx_last(tl),
 .accepted_count(accepted),.invalid_count(invalid),.overflow_count(overflow));
 always @(posedge clk) if(cv) begin
   commands=commands+1;
   if(cd!=5'b00111) $fatal(1,"command changed under reply backpressure");
 end
 task packet(input integer length,input integer error_first);
 begin
   wait(hr);@(negedge clk);hv=1;
   @(negedge clk);hv=0;
   for(k=0;k<length;k=k+1) begin
     data=k==0 ? 1 : 3;v=1;last=k==length-1;user=error_first && k==0;
     @(negedge clk);v=0;last=0;user=0;
     // Deliberate AXIS bubbles.
     repeat(2) @(negedge clk);
   end
 end
 endtask
 initial begin
   expected[0]=0;expected[1]=1;expected[2]=3;expected[3]=1;
   repeat(5) @(negedge clk);rst=0;
   packet(2,1);packet(9,0);
   if(commands!=0 || invalid!=2) $fatal(1,"early user flag / excess payload accepted");
   packet(2,0);
   if(commands!=1) $fatal(1,"valid packet missing");
   @(negedge clk);rv=1;@(negedge clk);rv=0;
   wait(thv);
   packet(2,0);
   if(commands!=1 || overflow!=1) $fatal(1,"busy reply must reject new command");
   repeat(20) begin
     @(negedge clk);
     if(!thv || ti!=32'hc0a8010a || tp!=40000) $fatal(1,"header not held");
   end
   thr=1;@(negedge clk);thr=0;
   for(bytes_sent=0;bytes_sent<4;bytes_sent=bytes_sent+1) begin
     repeat(7) begin
       @(negedge clk);
       if(!tv || td!=expected[bytes_sent] || tl!=(bytes_sent==3)) $fatal(1,"payload changed while stalled");
     end
     tr=1;@(negedge clk);tr=0;
   end
   @(negedge clk);
   if(tv || thv) $fatal(1,"extra reply bytes");
   packet(2,0);
   if(commands!=2) $fatal(1,"did not recover from backpressure");
   $display("PASS UDP bubbles, early error flag, excess length, full slot and reply header/payload backpressure");$finish;
 end
 initial begin #100000;$fatal(1,"backpressure timeout");end
endmodule
