// Copyright 2026 FaMAF-CVA6-Project contributors.
// SPDX-License-Identifier: SHL-0.51
//
// Debug-only KR260 wrapper.  The minimal ariane_kr260 top remains independent
// of Vivado debug IP.

module ariane_kr260_debug (
    input  logic        clk_i,
    input  logic        rst_ni,

    input  logic        tck_i,
    input  logic        tms_i,
    input  logic        tdi_i,
    input  logic        trst_ni,
    output logic        tdo_o,

    output logic [4:0]  m_axi_mem_awid,
    output logic [63:0] m_axi_mem_awaddr,
    output logic [7:0]  m_axi_mem_awlen,
    output logic [2:0]  m_axi_mem_awsize,
    output logic [1:0]  m_axi_mem_awburst,
    output logic        m_axi_mem_awlock,
    output logic [3:0]  m_axi_mem_awcache,
    output logic [2:0]  m_axi_mem_awprot,
    output logic [3:0]  m_axi_mem_awqos,
    output logic [5:0]  m_axi_mem_awatop,
    output logic [3:0]  m_axi_mem_awregion,
    output logic [63:0] m_axi_mem_awuser,
    output logic        m_axi_mem_awvalid,
    input  logic        m_axi_mem_awready,
    output logic [63:0] m_axi_mem_wdata,
    output logic [7:0]  m_axi_mem_wstrb,
    output logic        m_axi_mem_wlast,
    output logic [63:0] m_axi_mem_wuser,
    output logic        m_axi_mem_wvalid,
    input  logic        m_axi_mem_wready,
    input  logic [4:0]  m_axi_mem_bid,
    input  logic [1:0]  m_axi_mem_bresp,
    input  logic [63:0] m_axi_mem_buser,
    input  logic        m_axi_mem_bvalid,
    output logic        m_axi_mem_bready,
    output logic [4:0]  m_axi_mem_arid,
    output logic [63:0] m_axi_mem_araddr,
    output logic [7:0]  m_axi_mem_arlen,
    output logic [2:0]  m_axi_mem_arsize,
    output logic [1:0]  m_axi_mem_arburst,
    output logic        m_axi_mem_arlock,
    output logic [3:0]  m_axi_mem_arcache,
    output logic [2:0]  m_axi_mem_arprot,
    output logic [3:0]  m_axi_mem_arqos,
    output logic [3:0]  m_axi_mem_arregion,
    output logic [63:0] m_axi_mem_aruser,
    output logic        m_axi_mem_arvalid,
    input  logic        m_axi_mem_arready,
    input  logic [4:0]  m_axi_mem_rid,
    input  logic [63:0] m_axi_mem_rdata,
    input  logic [1:0]  m_axi_mem_rresp,
    input  logic        m_axi_mem_rlast,
    input  logic [63:0] m_axi_mem_ruser,
    input  logic        m_axi_mem_rvalid,
    output logic        m_axi_mem_rready
);

  logic soft_reset;
  logic core_rst_ni;

  // The VIO reset is additive: the external active-low reset always retains
  // control, while soft_reset can only assert an additional debug reset.
  // ariane_kr260 performs its normal reset synchronization internally.
  assign core_rst_ni = rst_ni & ~soft_reset;

  ariane_kr260 i_ariane_kr260 (
      .clk_i               ( clk_i ),
      .rst_ni              ( core_rst_ni ),
      .tck_i               ( tck_i ),
      .tms_i               ( tms_i ),
      .tdi_i               ( tdi_i ),
      .trst_ni             ( trst_ni ),
      .tdo_o               ( tdo_o ),
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
      .m_axi_mem_buser     ( m_axi_mem_buser ),
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
      .m_axi_mem_ruser     ( m_axi_mem_ruser ),
      .m_axi_mem_rvalid    ( m_axi_mem_rvalid ),
      .m_axi_mem_rready    ( m_axi_mem_rready )
  );

  // Control groups keep the capture compact while preserving the AXI channel
  // boundaries.  Bit mappings are documented in docs/kr260_ila_vio.md.
  logic [12:0] ar_control;
  logic [4:0]  r_control;
  logic [12:0] aw_control;
  logic [10:0] w_control;
  logic [3:0]  b_control;

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

  kr260_axi_ila i_kr260_axi_ila (
      .clk    ( clk_i ),
      .probe0 ( m_axi_mem_araddr ),
      .probe1 ( ar_control ),
      .probe2 ( m_axi_mem_rdata ),
      .probe3 ( r_control ),
      .probe4 ( m_axi_mem_awaddr ),
      .probe5 ( aw_control ),
      .probe6 ( m_axi_mem_wdata ),
      .probe7 ( w_control ),
      .probe8 ( b_control ),
      .probe9 ( rst_ni )
  );

  kr260_reset_vio i_kr260_reset_vio (
      .clk        ( clk_i ),
      .probe_in0  ( {rst_ni, core_rst_ni} ),
      .probe_out0 ( soft_reset )
  );

endmodule
