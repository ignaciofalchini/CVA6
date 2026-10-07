// Copyright 2026 FaMAF-CVA6-Project contributors.
// SPDX-License-Identifier: SHL-0.51
package kr260_addr_pkg;
  // Exclusive ends. Reserve this entire physical window in the PS boot software.
  localparam logic [63:0] CVA6_DDR_BASE = 64'h0000_0000_8000_0000;
  localparam logic [63:0] CVA6_DDR_SIZE = 64'h0000_0000_4000_0000;
  localparam logic [63:0] CVA6_DDR_END = CVA6_DDR_BASE + CVA6_DDR_SIZE;
  localparam logic [63:0] PS_DDR_BASE = 64'h0000_0008_0000_0000;
  localparam logic [63:0] PS_DDR_END = PS_DDR_BASE + CVA6_DDR_SIZE;

  function automatic logic [48:0] ps_ddr_address(input logic [63:0] address);
    return 49'(PS_DDR_BASE + (address - CVA6_DDR_BASE));
  endfunction
endpackage
