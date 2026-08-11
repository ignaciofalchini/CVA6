// Copyright 2026 FaMAF-CVA6-Project contributors.
// SPDX-License-Identifier: SHL-0.51
//
// Minimal KR260 integration wrapper.
//
// The AXI master ports form the intentional PL-to-system-memory boundary.
// They are not connected to a dummy memory in this design.

module ariane_kr260 (
    input  logic        clk_i,
    input  logic        rst_ni,

    // Optional RISC-V Debug Transport Module pins.  Their physical routing is
    // deliberately left for a later KR260 hardware-integration stage.
    input  logic        tck_i,
    input  logic        tms_i,
    input  logic        tdi_i,
    input  logic        trst_ni,
    output logic        tdo_o,

    // AXI4+ATOP memory-system boundary, to be connected to KR260 PS/PL DDR.
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

  function automatic config_pkg::cva6_cfg_t build_fpga_config(
      config_pkg::cva6_user_cfg_t CVA6UserCfg
  );
    config_pkg::cva6_user_cfg_t cfg = CVA6UserCfg;
    cfg.RVZiCond = bit'(0);
    cfg.NrNonIdempotentRules = unsigned'(1);
    cfg.NonIdempotentAddrBase = 1024'({64'b0});
    cfg.NonIdempotentLength = 1024'({ariane_soc::DRAMBase});
    return build_config_pkg::build_config(cfg);
  endfunction

  localparam config_pkg::cva6_cfg_t CVA6Cfg = build_fpga_config(cva6_config_pkg::cva6_cfg);
  localparam type rvfi_probes_instr_t = `RVFI_PROBES_INSTR_T(CVA6Cfg);
  localparam type rvfi_probes_csr_t = `RVFI_PROBES_CSR_T(CVA6Cfg);
  localparam type rvfi_probes_t = struct packed {
    logic csr;
    logic instr;
  };

  localparam int unsigned NrSlaves = 2;  // CVA6 and debug system-bus access
  localparam int unsigned NrMasters = 4; // DRAM, CLINT, ROM and debug memory
  localparam int unsigned Dram = 0;
  localparam int unsigned Clint = 1;
  localparam int unsigned Rom = 2;
  localparam int unsigned Debug = 3;
  localparam int unsigned AxiAddrWidth = 64;
  localparam int unsigned AxiDataWidth = 64;
  localparam int unsigned AxiIdWidthMaster = 4;
  localparam int unsigned AxiIdWidthSlaves = AxiIdWidthMaster + $clog2(NrSlaves);
  localparam int unsigned AxiUserWidth = CVA6Cfg.AxiUserWidth;

  `AXI_TYPEDEF_ALL(axi_slave,
                   logic [AxiAddrWidth-1:0],
                   logic [AxiIdWidthSlaves-1:0],
                   logic [AxiDataWidth-1:0],
                   logic [(AxiDataWidth/8)-1:0],
                   logic [AxiUserWidth-1:0])

  AXI_BUS #(
      .AXI_ADDR_WIDTH ( AxiAddrWidth ),
      .AXI_DATA_WIDTH ( AxiDataWidth ),
      .AXI_ID_WIDTH   ( AxiIdWidthMaster ),
      .AXI_USER_WIDTH ( AxiUserWidth )
  ) slave [NrSlaves-1:0] ();

  AXI_BUS #(
      .AXI_ADDR_WIDTH ( AxiAddrWidth ),
      .AXI_DATA_WIDTH ( AxiDataWidth ),
      .AXI_ID_WIDTH   ( AxiIdWidthSlaves ),
      .AXI_USER_WIDTH ( AxiUserWidth )
  ) master [NrMasters-1:0] ();

  logic test_en;
  logic ndmreset;
  logic ndmreset_n;
  logic debug_req_irq;
  logic timer_irq;
  logic ipi;
  logic rtc;
  logic [1:0] irq;

  assign test_en = 1'b0;
  assign irq = '0;

  // `rst_ni` is the KR260 integration reset input.  The future PS/PL design
  // must hold it low until the selected memory path and clock are stable.
  rstgen i_rstgen_main (
      .clk_i       ( clk_i ),
      .rst_ni      ( rst_ni & ~ndmreset ),
      .test_mode_i ( test_en ),
      .rst_no      ( ndmreset_n ),
      .init_no     ( )
  );

  // --------------------------------------------------------------------------
  // AXI crossbar: Debug, ROM, CLINT and the external DDR-memory boundary.
  // --------------------------------------------------------------------------
  axi_pkg::xbar_rule_64_t [NrMasters-1:0] addr_map;

  assign addr_map = '{
      '{idx: Debug, start_addr: ariane_soc::DebugBase,
        end_addr: ariane_soc::DebugBase + ariane_soc::DebugLength},
      '{idx: Rom, start_addr: ariane_soc::ROMBase,
        end_addr: ariane_soc::ROMBase + ariane_soc::ROMLength},
      '{idx: Clint, start_addr: ariane_soc::CLINTBase,
        end_addr: ariane_soc::CLINTBase + ariane_soc::CLINTLength},
      '{idx: Dram, start_addr: ariane_soc::DRAMBase,
        end_addr: ariane_soc::DRAMBase + ariane_soc::DRAMLength}
  };

  localparam axi_pkg::xbar_cfg_t AXI_XBAR_CFG = '{
      NoSlvPorts:         NrSlaves,
      NoMstPorts:         NrMasters,
      MaxMstTrans:        1,
      MaxSlvTrans:        1,
      FallThrough:        1'b0,
      LatencyMode:        axi_pkg::CUT_ALL_PORTS,
      AxiIdWidthSlvPorts: AxiIdWidthMaster,
      AxiIdUsedSlvPorts:  AxiIdWidthMaster,
      UniqueIds:          1'b0,
      AxiAddrWidth:       AxiAddrWidth,
      AxiDataWidth:       AxiDataWidth,
      NoAddrRules:        NrMasters
  };

  axi_xbar_intf #(
      .AXI_USER_WIDTH ( AxiUserWidth ),
      .Cfg            ( AXI_XBAR_CFG ),
      .rule_t         ( axi_pkg::xbar_rule_64_t )
  ) i_axi_xbar (
      .clk_i                 ( clk_i ),
      .rst_ni                ( ndmreset_n ),
      .test_i                ( test_en ),
      .slv_ports             ( slave ),
      .mst_ports             ( master ),
      .addr_map_i            ( addr_map ),
      .en_default_mst_port_i ( '0 ),
      .default_mst_port_i    ( '0 )
  );

  // --------------------------------------------------------------------------
  // RISC-V debug module.  It is board-independent; only its future physical
  // JTAG pin assignment is deferred.
  // --------------------------------------------------------------------------
  logic         debug_req_valid;
  logic         debug_req_ready;
  dm::dmi_req_t debug_req;
  logic         debug_resp_valid;
  logic         debug_resp_ready;
  dm::dmi_resp_t debug_resp;
  logic         dmactive;

  dmi_jtag i_dmi_jtag (
      .clk_i            ( clk_i ),
      .rst_ni           ( rst_ni ),
      .dmi_rst_no       ( ),
      .testmode_i       ( test_en ),
      .dmi_req_valid_o  ( debug_req_valid ),
      .dmi_req_ready_i  ( debug_req_ready ),
      .dmi_req_o        ( debug_req ),
      .dmi_resp_valid_i ( debug_resp_valid ),
      .dmi_resp_ready_o ( debug_resp_ready ),
      .dmi_resp_i       ( debug_resp ),
      .tck_i            ( tck_i ),
      .tms_i            ( tms_i ),
      .trst_ni          ( trst_ni ),
      .td_i             ( tdi_i ),
      .td_o             ( tdo_o ),
      .tdo_oe_o         ( )
  );

  logic                     dm_slave_req;
  logic                     dm_slave_we;
  logic [CVA6Cfg.XLEN-1:0] dm_slave_addr;
  logic [CVA6Cfg.XLEN/8-1:0] dm_slave_be;
  logic [CVA6Cfg.XLEN-1:0] dm_slave_wdata;
  logic [CVA6Cfg.XLEN-1:0] dm_slave_rdata;
  logic                     dm_master_req;
  logic [CVA6Cfg.XLEN-1:0] dm_master_add;
  logic                     dm_master_we;
  logic [CVA6Cfg.XLEN-1:0] dm_master_wdata;
  logic [CVA6Cfg.XLEN/8-1:0] dm_master_be;
  logic                     dm_master_gnt;
  logic                     dm_master_r_valid;
  logic [CVA6Cfg.XLEN-1:0] dm_master_r_rdata;

  dm_top #(
      .NrHarts         ( 1 ),
      .BusWidth        ( CVA6Cfg.XLEN ),
      .SelectableHarts ( 1'b1 )
  ) i_dm_top (
      .clk_i            ( clk_i ),
      .rst_ni           ( rst_ni ),
      .testmode_i       ( test_en ),
      .ndmreset_o       ( ndmreset ),
      .dmactive_o       ( dmactive ),
      .debug_req_o      ( debug_req_irq ),
      .unavailable_i    ( '0 ),
      .hartinfo_i       ( {ariane_pkg::DebugHartInfo} ),
      .slave_req_i      ( dm_slave_req ),
      .slave_we_i       ( dm_slave_we ),
      .slave_addr_i     ( dm_slave_addr ),
      .slave_be_i       ( dm_slave_be ),
      .slave_wdata_i    ( dm_slave_wdata ),
      .slave_rdata_o    ( dm_slave_rdata ),
      .master_req_o     ( dm_master_req ),
      .master_add_o     ( dm_master_add ),
      .master_we_o      ( dm_master_we ),
      .master_wdata_o   ( dm_master_wdata ),
      .master_be_o      ( dm_master_be ),
      .master_gnt_i     ( dm_master_gnt ),
      .master_r_valid_i ( dm_master_r_valid ),
      .master_r_rdata_i ( dm_master_r_rdata ),
      .dmi_rst_ni       ( rst_ni ),
      .dmi_req_valid_i  ( debug_req_valid ),
      .dmi_req_ready_o  ( debug_req_ready ),
      .dmi_req_i        ( debug_req ),
      .dmi_resp_valid_o ( debug_resp_valid ),
      .dmi_resp_ready_i ( debug_resp_ready ),
      .dmi_resp_o       ( debug_resp )
  );

  axi2mem #(
      .AXI_ID_WIDTH   ( AxiIdWidthSlaves ),
      .AXI_ADDR_WIDTH ( CVA6Cfg.XLEN ),
      .AXI_DATA_WIDTH ( CVA6Cfg.XLEN ),
      .AXI_USER_WIDTH ( AxiUserWidth )
  ) i_dm_axi2mem (
      .clk_i  ( clk_i ),
      .rst_ni ( rst_ni ),
      .slave  ( master[Debug] ),
      .req_o  ( dm_slave_req ),
      .we_o   ( dm_slave_we ),
      .addr_o ( dm_slave_addr ),
      .be_o   ( dm_slave_be ),
      .data_o ( dm_slave_wdata ),
      .data_i ( dm_slave_rdata )
  );

  ariane_axi::req_t dm_axi_m_req;
  ariane_axi::resp_t dm_axi_m_resp;
  logic [1:0] axi_adapter_size;
  assign axi_adapter_size = 2'b11;

  axi_adapter #(
      .CVA6Cfg   ( CVA6Cfg ),
      .DATA_WIDTH ( CVA6Cfg.XLEN ),
      .axi_req_t ( ariane_axi::req_t ),
      .axi_rsp_t ( ariane_axi::resp_t )
  ) i_dm_axi_master (
      .clk_i                 ( clk_i ),
      .rst_ni                ( rst_ni ),
      .req_i                 ( dm_master_req ),
      .type_i                ( ariane_pkg::SINGLE_REQ ),
      .amo_i                 ( ariane_pkg::AMO_NONE ),
      .gnt_o                 ( dm_master_gnt ),
      .addr_i                ( dm_master_add ),
      .we_i                  ( dm_master_we ),
      .wdata_i               ( dm_master_wdata ),
      .be_i                  ( dm_master_be ),
      .size_i                ( axi_adapter_size ),
      .id_i                  ( '0 ),
      .valid_o               ( dm_master_r_valid ),
      .rdata_o               ( dm_master_r_rdata ),
      .id_o                  ( ),
      .critical_word_o       ( ),
      .critical_word_valid_o ( ),
      .axi_req_o             ( dm_axi_m_req ),
      .axi_resp_i            ( dm_axi_m_resp )
  );

  `AXI_ASSIGN_FROM_REQ(slave[1], dm_axi_m_req)
  `AXI_ASSIGN_TO_RESP(dm_axi_m_resp, slave[1])

  // --------------------------------------------------------------------------
  // CVA6, CLINT and boot ROM.
  // --------------------------------------------------------------------------
  ariane_axi::req_t axi_ariane_req;
  ariane_axi::resp_t axi_ariane_resp;

  ariane #(
      .CVA6Cfg             ( CVA6Cfg ),
      .rvfi_probes_instr_t ( rvfi_probes_instr_t ),
      .rvfi_probes_csr_t   ( rvfi_probes_csr_t ),
      .rvfi_probes_t       ( rvfi_probes_t )
  ) i_ariane (
      .clk_i         ( clk_i ),
      .rst_ni        ( ndmreset_n ),
      .boot_addr_i   ( ariane_soc::ROMBase ),
      .hart_id_i     ( '0 ),
      .irq_i         ( irq ),
      .ipi_i         ( ipi ),
      .time_irq_i    ( timer_irq ),
      .rvfi_probes_o ( ),
      .debug_req_i   ( debug_req_irq ),
      .noc_req_o     ( axi_ariane_req ),
      .noc_resp_i    ( axi_ariane_resp )
  );

  `AXI_ASSIGN_FROM_REQ(slave[0], axi_ariane_req)
  `AXI_ASSIGN_TO_RESP(axi_ariane_resp, slave[0])

  always_ff @(posedge clk_i or negedge ndmreset_n) begin
    if (!ndmreset_n) begin
      rtc <= 1'b0;
    end else begin
      rtc <= ~rtc;
    end
  end

  axi_slave_req_t axi_clint_req;
  axi_slave_resp_t axi_clint_resp;
  clint #(
      .CVA6Cfg        ( CVA6Cfg ),
      .AXI_ADDR_WIDTH ( AxiAddrWidth ),
      .AXI_DATA_WIDTH ( AxiDataWidth ),
      .AXI_ID_WIDTH   ( AxiIdWidthSlaves ),
      .NR_CORES       ( 1 ),
      .axi_req_t      ( axi_slave_req_t ),
      .axi_resp_t     ( axi_slave_resp_t )
  ) i_clint (
      .clk_i       ( clk_i ),
      .rst_ni      ( ndmreset_n ),
      .testmode_i  ( test_en ),
      .axi_req_i   ( axi_clint_req ),
      .axi_resp_o  ( axi_clint_resp ),
      .rtc_i       ( rtc ),
      .timer_irq_o ( timer_irq ),
      .ipi_o       ( ipi )
  );
  `AXI_ASSIGN_TO_REQ(axi_clint_req, master[Clint])
  `AXI_ASSIGN_FROM_RESP(master[Clint], axi_clint_resp)

  logic                    rom_req;
  logic [AxiAddrWidth-1:0] rom_addr;
  logic [AxiDataWidth-1:0] rom_rdata;
  axi2mem #(
      .AXI_ID_WIDTH   ( AxiIdWidthSlaves ),
      .AXI_ADDR_WIDTH ( AxiAddrWidth ),
      .AXI_DATA_WIDTH ( AxiDataWidth ),
      .AXI_USER_WIDTH ( AxiUserWidth )
  ) i_axi2rom (
      .clk_i  ( clk_i ),
      .rst_ni ( ndmreset_n ),
      .slave  ( master[Rom] ),
      .req_o  ( rom_req ),
      .we_o   ( ),
      .addr_o ( rom_addr ),
      .be_o   ( ),
      .data_o ( ),
      .data_i ( rom_rdata )
  );

  bootrom_64 i_bootrom (
      .clk_i   ( clk_i ),
      .req_i   ( rom_req ),
      .addr_i  ( rom_addr ),
      .rdata_o ( rom_rdata )
  );

  // Atomics remain in front of the external memory system.  No clock or width
  // conversion is inserted until the concrete KR260 PS/PL memory port is chosen.
  AXI_BUS #(
      .AXI_ADDR_WIDTH ( AxiAddrWidth ),
      .AXI_DATA_WIDTH ( AxiDataWidth ),
      .AXI_ID_WIDTH   ( AxiIdWidthSlaves ),
      .AXI_USER_WIDTH ( AxiUserWidth )
  ) dram ();

  axi_riscv_atomics_wrap #(
      .AXI_ADDR_WIDTH      ( AxiAddrWidth ),
      .AXI_DATA_WIDTH      ( AxiDataWidth ),
      .AXI_ID_WIDTH        ( AxiIdWidthSlaves ),
      .AXI_USER_WIDTH      ( AxiUserWidth ),
      .AXI_MAX_WRITE_TXNS  ( 1 ),
      .RISCV_WORD_WIDTH    ( 64 )
  ) i_axi_riscv_atomics (
      .clk_i  ( clk_i ),
      .rst_ni ( ndmreset_n ),
      .slv    ( master[Dram] ),
      .mst    ( dram )
  );

  // --------------------------------------------------------------------------
  // Explicit AXI boundary to future KR260 memory integration.
  // --------------------------------------------------------------------------
  assign m_axi_mem_awid     = dram.aw_id;
  assign m_axi_mem_awaddr   = dram.aw_addr;
  assign m_axi_mem_awlen    = dram.aw_len;
  assign m_axi_mem_awsize   = dram.aw_size;
  assign m_axi_mem_awburst  = dram.aw_burst;
  assign m_axi_mem_awlock   = dram.aw_lock;
  assign m_axi_mem_awcache  = dram.aw_cache;
  assign m_axi_mem_awprot   = dram.aw_prot;
  assign m_axi_mem_awqos    = dram.aw_qos;
  assign m_axi_mem_awatop   = dram.aw_atop;
  assign m_axi_mem_awregion = dram.aw_region;
  assign m_axi_mem_awuser   = dram.aw_user;
  assign m_axi_mem_awvalid  = dram.aw_valid;
  assign dram.aw_ready       = m_axi_mem_awready;
  assign m_axi_mem_wdata     = dram.w_data;
  assign m_axi_mem_wstrb     = dram.w_strb;
  assign m_axi_mem_wlast     = dram.w_last;
  assign m_axi_mem_wuser     = dram.w_user;
  assign m_axi_mem_wvalid    = dram.w_valid;
  assign dram.w_ready        = m_axi_mem_wready;
  assign dram.b_id           = m_axi_mem_bid;
  assign dram.b_resp         = m_axi_mem_bresp;
  assign dram.b_user         = m_axi_mem_buser;
  assign dram.b_valid        = m_axi_mem_bvalid;
  assign m_axi_mem_bready    = dram.b_ready;
  assign m_axi_mem_arid      = dram.ar_id;
  assign m_axi_mem_araddr    = dram.ar_addr;
  assign m_axi_mem_arlen     = dram.ar_len;
  assign m_axi_mem_arsize    = dram.ar_size;
  assign m_axi_mem_arburst   = dram.ar_burst;
  assign m_axi_mem_arlock    = dram.ar_lock;
  assign m_axi_mem_arcache   = dram.ar_cache;
  assign m_axi_mem_arprot    = dram.ar_prot;
  assign m_axi_mem_arqos     = dram.ar_qos;
  assign m_axi_mem_arregion  = dram.ar_region;
  assign m_axi_mem_aruser    = dram.ar_user;
  assign m_axi_mem_arvalid   = dram.ar_valid;
  assign dram.ar_ready       = m_axi_mem_arready;
  assign dram.r_id           = m_axi_mem_rid;
  assign dram.r_data         = m_axi_mem_rdata;
  assign dram.r_resp         = m_axi_mem_rresp;
  assign dram.r_last         = m_axi_mem_rlast;
  assign dram.r_user         = m_axi_mem_ruser;
  assign dram.r_valid        = m_axi_mem_rvalid;
  assign m_axi_mem_rready    = dram.r_ready;

endmodule
