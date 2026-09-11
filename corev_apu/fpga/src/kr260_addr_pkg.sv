// Copyright 2026 FaMAF-CVA6-Project contributors.
// SPDX-License-Identifier: SHL-0.51
//
// Common address map for the CVA6 KR260 wrappers.

package kr260_addr_pkg;

  // CVA6 exposes the DDR window at 0x8000_0000..0xbfff_ffff.
  localparam logic [63:0] CVA6_DDR_BASE = 64'h0000_0000_8000_0000;
  localparam logic [63:0] CVA6_DDR_END  = 64'h0000_0000_c000_0000;

endpackage
