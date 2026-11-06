module kr260_address_tb;
  import kr260_addr_pkg::*;
  initial begin
    assert (ps_ddr_address(64'h80000000) == 49'h800000000) else $fatal;
    assert (ps_ddr_address(64'h80002000) == 49'h800002000) else $fatal;
    assert (ps_ddr_address(64'hbfffffff) == 49'h83fffffff) else $fatal;
    for (int bitno = 0; bitno < 30; bitno++) begin
      assert (ps_ddr_address(CVA6_DDR_BASE + (64'd1 << bitno)) ==
              49'(PS_DDR_BASE + (64'd1 << bitno))) else $fatal;
    end
    $display("PASS DDR address boundaries and all 30 offset bits");
    $finish;
  end
endmodule
