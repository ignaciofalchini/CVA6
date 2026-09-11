// Copyright 2026 FaMAF-CVA6-Project contributors.
// SPDX-License-Identifier: SHL-0.51
//
// Debug-only KR260 wrapper.  The minimal ariane_kr260 top remains independent
// of Vivado debug IP.

module ariane_kr260_debug (
    input logic clk_i
);

  logic pl_clk;

  logic soft_reset;
  logic mem_rst_n;
  logic jtag_tdo_unused;
  logic [31:0] m_debug_instruction;
  logic        m_debug_instruction_valid;
  logic [63:0] m_debug_commit_pc;
  logic        m_debug_commit_valid;
  logic        m_debug_commit_ack;
  logic [63:0] m_debug_mem_paddr;
  logic [63:0] m_debug_lsu_vaddr;
  logic [7:0]  m_debug_lsu_be;
  logic [7:0]  m_debug_commit_op;
  logic [3:0]  m_debug_lsu_fu;

  // CVA6 memory AXI interface; observed by the ILA and connected to BRAM.
  logic [4:0]  m_axi_mem_awid;
  logic [63:0] m_axi_mem_awaddr;
  logic [7:0]  m_axi_mem_awlen;
  logic [2:0]  m_axi_mem_awsize;
  logic [1:0]  m_axi_mem_awburst;
  logic        m_axi_mem_awlock;
  logic [3:0]  m_axi_mem_awcache;
  logic [2:0]  m_axi_mem_awprot;
  logic [3:0]  m_axi_mem_awqos;
  logic [5:0]  m_axi_mem_awatop;
  logic [3:0]  m_axi_mem_awregion;
  logic [63:0] m_axi_mem_awuser;
  logic        m_axi_mem_awvalid;
  logic        m_axi_mem_awready;
  logic [63:0] m_axi_mem_wdata;
  logic [7:0]  m_axi_mem_wstrb;
  logic        m_axi_mem_wlast;
  logic [63:0] m_axi_mem_wuser;
  logic        m_axi_mem_wvalid;
  logic        m_axi_mem_wready;
  logic [4:0]  m_axi_mem_bid;
  logic [1:0]  m_axi_mem_bresp;
  logic        m_axi_mem_bvalid;
  logic        m_axi_mem_bready;
  logic [4:0]  m_axi_mem_arid;
  logic [63:0] m_axi_mem_araddr;
  logic [7:0]  m_axi_mem_arlen;
  logic [2:0]  m_axi_mem_arsize;
  logic [1:0]  m_axi_mem_arburst;
  logic        m_axi_mem_arlock;
  logic [3:0]  m_axi_mem_arcache;
  logic [2:0]  m_axi_mem_arprot;
  logic [3:0]  m_axi_mem_arqos;
  logic [3:0]  m_axi_mem_arregion;
  logic [63:0] m_axi_mem_aruser;
  logic        m_axi_mem_arvalid;
  logic        m_axi_mem_arready;
  logic [4:0]  m_axi_mem_rid;
  logic [63:0] m_axi_mem_rdata;
  logic [1:0]  m_axi_mem_rresp;
  logic        m_axi_mem_rlast;
  logic        m_axi_mem_rvalid;
  logic        m_axi_mem_rready;

  // VIO requests system reset; mem_rst_n is its synchronized system output.
  // Keep the debug clock running while the core and memory controller reset.
  assign pl_clk = clk_i;

  ariane_kr260 i_ariane_kr260 (
      .clk_i               ( pl_clk ),
      .rst_ni              ( ~soft_reset ),
      .mem_rst_no          ( mem_rst_n ),
      // The CVA6 JTAG DTM is not exposed by this wrapper.  Keep it in reset;
      // the Xilinx ILA/VIO remain accessible through the FPGA JTAG chain.
      .tck_i               ( 1'b0 ),
      .tms_i               ( 1'b1 ),
      .tdi_i               ( 1'b0 ),
      .trst_ni             ( 1'b0 ),
      .tdo_o               ( jtag_tdo_unused ),
      .m_axi_mem_awid      ( m_axi_mem_awid ),
      .m_axi_mem_awaddr    ( m_axi_mem_awaddr ),
      .m_axi_mem_awlen     ( m_axi_mem_awlen ),
      .m_axi_mem_awsize    ( m_axi_mem_awsize ),
      .m_axi_mem_awburst   ( m_axi_mem_awburst ),
      .m_axi_mem_awlock    ( m_axi_mem_awlock ),
      .m_axi_mem_awcache   ( m_axi_mem_awcache ),
      .m_axi_mem_awprot    ( m_axi_mem_awprot ),
      .m_axi_mem_awqos     ( m_axi_mem_awqos ),
      .m_axi_mem_awatop    ( m_axi_mem_awatop ),
      .m_axi_mem_awregion  ( m_axi_mem_awregion ),
      .m_axi_mem_awuser    ( m_axi_mem_awuser ),
      .m_axi_mem_awvalid   ( m_axi_mem_awvalid ),
      .m_axi_mem_awready   ( m_axi_mem_awready ),
      .m_axi_mem_wdata     ( m_axi_mem_wdata ),
      .m_axi_mem_wstrb     ( m_axi_mem_wstrb ),
      .m_axi_mem_wlast     ( m_axi_mem_wlast ),
      .m_axi_mem_wuser     ( m_axi_mem_wuser ),
      .m_axi_mem_wvalid    ( m_axi_mem_wvalid ),
      .m_axi_mem_wready    ( m_axi_mem_wready ),
      .m_axi_mem_bid       ( m_axi_mem_bid ),
      .m_axi_mem_bresp     ( m_axi_mem_bresp ),
      .m_axi_mem_buser     ( '0           ),
      .m_axi_mem_bvalid    ( m_axi_mem_bvalid ),
      .m_axi_mem_bready    ( m_axi_mem_bready ),
      .m_axi_mem_arid      ( m_axi_mem_arid ),
      .m_axi_mem_araddr    ( m_axi_mem_araddr ),
      .m_axi_mem_arlen     ( m_axi_mem_arlen ),
      .m_axi_mem_arsize    ( m_axi_mem_arsize ),
      .m_axi_mem_arburst   ( m_axi_mem_arburst ),
      .m_axi_mem_arlock    ( m_axi_mem_arlock ),
      .m_axi_mem_arcache   ( m_axi_mem_arcache ),
      .m_axi_mem_arprot    ( m_axi_mem_arprot ),
      .m_axi_mem_arqos     ( m_axi_mem_arqos ),
      .m_axi_mem_arregion  ( m_axi_mem_arregion ),
      .m_axi_mem_aruser    ( m_axi_mem_aruser ),
      .m_axi_mem_arvalid   ( m_axi_mem_arvalid ),
      .m_axi_mem_arready   ( m_axi_mem_arready ),
      .m_axi_mem_rid       ( m_axi_mem_rid ),
      .m_axi_mem_rdata     ( m_axi_mem_rdata ),
      .m_axi_mem_rresp     ( m_axi_mem_rresp ),
      .m_axi_mem_rlast     ( m_axi_mem_rlast ),
      .m_axi_mem_ruser     ( '0           ),
      .m_axi_mem_rvalid    ( m_axi_mem_rvalid ),
      .m_axi_mem_rready    ( m_axi_mem_rready ),
      .debug_instruction_o       ( m_debug_instruction ),
      .debug_instruction_valid_o ( m_debug_instruction_valid ),
      .debug_commit_pc_o         ( m_debug_commit_pc ),
      .debug_commit_valid_o      ( m_debug_commit_valid ),
      .debug_commit_ack_o        ( m_debug_commit_ack ),
      .debug_mem_paddr_o         ( m_debug_mem_paddr ),
      .debug_lsu_vaddr_o         ( m_debug_lsu_vaddr ),
      .debug_lsu_be_o            ( m_debug_lsu_be ),
      .debug_commit_op_o         ( m_debug_commit_op ),
      .debug_lsu_fu_o            ( m_debug_lsu_fu )
  );


  ariane_kr260_ps_bd_wrapper i_ps_ddr (
      .s_axi_aclk_0       ( clk_i ),
      .s_axi_aresetn      ( mem_rst_n ),
      .S_AXI_CVA6_awid   ( m_axi_mem_awid ),
      .S_AXI_CVA6_bid    ( m_axi_mem_bid  ),
      .S_AXI_CVA6_arid   ( m_axi_mem_arid ),
      .S_AXI_CVA6_rid    ( m_axi_mem_rid  ),
      .S_AXI_CVA6_awaddr  ( m_axi_mem_awaddr[12:0] ),
      .S_AXI_CVA6_awlen   ( m_axi_mem_awlen ),
      .S_AXI_CVA6_awsize  ( m_axi_mem_awsize ),
      .S_AXI_CVA6_awburst ( m_axi_mem_awburst ),
      .S_AXI_CVA6_awlock  ( m_axi_mem_awlock ),
      .S_AXI_CVA6_awcache ( m_axi_mem_awcache ),
      .S_AXI_CVA6_awprot  ( m_axi_mem_awprot ),
      .S_AXI_CVA6_awvalid ( m_axi_mem_awvalid ),
      .S_AXI_CVA6_awready ( m_axi_mem_awready ),
      .S_AXI_CVA6_wdata   ( m_axi_mem_wdata ),
      .S_AXI_CVA6_wstrb   ( m_axi_mem_wstrb ),
      .S_AXI_CVA6_wlast   ( m_axi_mem_wlast ),
      .S_AXI_CVA6_wvalid  ( m_axi_mem_wvalid ),
      .S_AXI_CVA6_wready  ( m_axi_mem_wready ),
      .S_AXI_CVA6_bresp   ( m_axi_mem_bresp ),
      .S_AXI_CVA6_bvalid  ( m_axi_mem_bvalid ),
      .S_AXI_CVA6_bready  ( m_axi_mem_bready ),
      .S_AXI_CVA6_araddr  ( m_axi_mem_araddr[12:0] ),
      .S_AXI_CVA6_arlen   ( m_axi_mem_arlen ),
      .S_AXI_CVA6_arsize  ( m_axi_mem_arsize ),
      .S_AXI_CVA6_arburst ( m_axi_mem_arburst ),
      .S_AXI_CVA6_arlock  ( m_axi_mem_arlock ),
      .S_AXI_CVA6_arcache ( m_axi_mem_arcache ),
      .S_AXI_CVA6_arprot  ( m_axi_mem_arprot ),
      .S_AXI_CVA6_arvalid ( m_axi_mem_arvalid ),
      .S_AXI_CVA6_arready ( m_axi_mem_arready ),
      .S_AXI_CVA6_rdata   ( m_axi_mem_rdata ),
      .S_AXI_CVA6_rresp   ( m_axi_mem_rresp ),
      .S_AXI_CVA6_rlast   ( m_axi_mem_rlast ),
      .S_AXI_CVA6_rvalid  ( m_axi_mem_rvalid ),
      .S_AXI_CVA6_rready  ( m_axi_mem_rready )
  );
  // Control groups keep the capture compact while preserving the AXI channel
  // boundaries.  Bit mappings are documented in docs/kr260_ila_vio.md.
  logic [12:0] ar_control;
  logic [4:0]  r_control;
  logic [12:0] aw_control;
  logic [10:0] w_control;
  logic [3:0]  b_control;
  logic [19:0] axi_ids;

  assign ar_control = {
      m_axi_mem_arvalid,
      m_axi_mem_arready,
      m_axi_mem_arlen,
      m_axi_mem_arsize
  };
  assign r_control = {
      m_axi_mem_rvalid,
      m_axi_mem_rready,
      m_axi_mem_rresp,
      m_axi_mem_rlast
  };
  assign aw_control = {
      m_axi_mem_awvalid,
      m_axi_mem_awready,
      m_axi_mem_awlen,
      m_axi_mem_awsize
  };
  assign w_control = {
      m_axi_mem_wstrb,
      m_axi_mem_wvalid,
      m_axi_mem_wready,
      m_axi_mem_wlast
  };
  assign b_control = {
      m_axi_mem_bresp,
      m_axi_mem_bvalid,
      m_axi_mem_bready
  };

  // Compare IDs on the respective request/response handshakes, not necessarily
  // in the same cycle. An ID with its channel VALID low is not a transaction.
  assign axi_ids = {
      m_axi_mem_awid,  // [19:15]
      m_axi_mem_bid,   // [14:10]
      m_axi_mem_arid,  // [9:5]
      m_axi_mem_rid    // [4:0]
  };

  kr260_axi_ila i_kr260_axi_ila (
      .clk        ( pl_clk ),
      .probe0 ( m_axi_mem_araddr ),
      .probe1 ( ar_control ),
      .probe2 ( m_axi_mem_rdata ),
      .probe3 ( r_control ),
      .probe4 ( m_axi_mem_awaddr ),
      .probe5 ( aw_control ),
      .probe6 ( m_axi_mem_wdata ),
      .probe7 ( w_control ),
      .probe8 ( b_control ),
      .probe9 ( mem_rst_n ),
      .probe10 ( m_debug_instruction ),
      .probe11 ( m_debug_instruction_valid ),
      .probe12 ( m_debug_commit_pc ),
      .probe13 ( m_debug_commit_valid ),
      .probe14 ( m_debug_commit_ack ),
      .probe15 ( m_debug_mem_paddr ),
      .probe16 ( m_debug_lsu_vaddr ),
      .probe17 ( m_debug_lsu_be ),
      .probe18 ( m_debug_commit_op ),
      .probe19 ( m_debug_lsu_fu ),
      .probe20 ( axi_ids )
  );

  kr260_reset_vio i_kr260_reset_vio (
      .clk    ( pl_clk ),
      .probe_in0  ( {soft_reset, mem_rst_n} ),
      .probe_out0 ( soft_reset )
  );

endmodule
