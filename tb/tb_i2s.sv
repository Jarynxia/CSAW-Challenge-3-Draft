`timescale 1ns/1ps
module tb_i2s;
  reg clk=0, rst=1, bclk=0, ws=0, sd=0;
  wire out;
  always #50 clk=~clk;
  phase4_dut dut(.clk(clk),.rst(rst),.bclk(bclk),.lrclk(ws),.sd_in(sd),.sd_out(out));
  integer half_ns=500, offset_ns=17, count, f, j, rc, fd, logfd;
  integer failures=0, rx_count=0, received=0;
  reg [15:0] lin, rin, ey, ee, read_l, read_r;
  reg [31:0] send_word, read_word;
  integer ea, es;
  string vectors, logfile;
  always @(negedge clk) begin
    if (!rst && dut.u_core.new_sample) begin
      rx_count=rx_count+1;
      if (dut.u_core.left_sample !== lin) begin
        failures=failures+1;
        if (failures<12) $display("RX mismatch frame=%0d actual=%h expected=%h",f,dut.u_core.left_sample,lin);
      end
    end
  end
  initial begin
    if (!$value$plusargs("VECTORS=%s",vectors)) $fatal(1,"missing vectors");
    if (!$value$plusargs("LOG=%s",logfile)) $fatal(1,"missing log");
    rc=$value$plusargs("HALF=%d",half_ns);
    rc=$value$plusargs("OFFSET=%d",offset_ns);
    fd=$fopen(vectors,"r"); logfd=$fopen(logfile,"w");
    if (!fd || !logfd) $fatal(1,"file open failure");
    rc=$fscanf(fd,"%d\n",count);
    #2000; rst=0; #(offset_ns); bclk=1; #(2*half_ns);
    for(f=0; f<count; f=f+1) begin
      rc=$fscanf(fd,"%h %h %h %h %d %d\n",lin,rin,ey,ee,ea,es);
      if(rc!=6) $fatal(1,"bad vector at frame %0d",f);
      send_word={lin,rin}; read_word=0;
      for(j=0;j<32;j=j+1) begin
        bclk=0;
        // Philips I2S: WS changes one bit BEFORE the following word's MSB.
        ws=(j>=15 && j<31);
        sd=send_word[31-j];
        #(half_ns); bclk=1;
        read_word={read_word[30:0],out};
        #(half_ns);
      end
      read_l=read_word[31:16]; read_r=read_word[15:0];
      if (read_l !== ey || read_r !== ee || dut.u_core.payload_active !== ea[0] || dut.u_core.trigger_state !== es[1:0]) begin
        failures=failures+1;
        if(failures<12) $display("FAIL frame=%0d y=%h expected=%h echo=%h expected=%h active=%b expected=%0d state=%d expected=%0d",f,read_l,ey,read_r,ee,dut.u_core.payload_active,ea,dut.u_core.trigger_state,es);
      end
      $fdisplay(logfd,"%0d,%0d,%0d,%0d,%0d",f,$signed(lin),$signed(read_l),$signed(read_r),dut.u_core.payload_active);
      received=received+1;
    end
    if(rx_count!=count) begin failures=failures+1; $display("RX strobe count %0d expected %0d",rx_count,count); end
    $fclose(fd); $fclose(logfd);
    $display("RESULT frames=%0d rx=%0d failures=%0d half_ns=%0d offset_ns=%0d",received,rx_count,failures,half_ns,offset_ns);
    if(failures) $fatal(1,"verification failed");
    $finish;
  end
endmodule
