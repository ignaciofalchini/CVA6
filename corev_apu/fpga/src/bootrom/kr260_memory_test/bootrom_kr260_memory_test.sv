/* Copyright 2018 ETH Zurich and University of Bologna.
 * Copyright and related rights are licensed under the Solderpad Hardware
 * License, Version 0.51 (the "License"); you may not use this file except in
 * compliance with the License.  You may obtain a copy of the License at
 * http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
 * or agreed to in writing, software, hardware and materials distributed under
 * this License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 *
 * File: $filename.v
 *
 * Description: Auto-generated bootrom
 */

// Auto-generated code
module bootrom_kr260_memory_test (
   input  logic         clk_i,
   input  logic         req_i,
   input  logic [63:0]  addr_i,
   output logic [63:0]  rdata_o
);
    localparam int RomSize = 40;

    const logic [RomSize-1:0][63:0] mem = {
        64'h00000000_00000000,
        64'h0000006f_0ff0000f,
        64'h01c4b023_fff00e13,
        64'h0ff0000f_0074bc23,
        64'h0064b823_0054b423,
        64'h00008067_00731463,
        64'h0002b383_0122c333,
        64'h00008067_0062b023,
        64'h0122c333_0000006f,
        64'h0ff0000f_0064b023,
        64'h00100313_0ff0000f,
        64'h024000ef_ff828293,
        64'h01e29293_0030029b,
        64'hffca68e3_40000e37,
        64'h001a1a13_040000ef,
        64'h014402b3_00002a37,
        64'h04c000ef_00040293,
        64'h0ff0000f_04c000ef,
        64'hff828293_01e29293,
        64'h0030029b_ffca68e3,
        64'h40000e37_001a1a13,
        64'h068000ef_014402b3,
        64'h00002a37_074000ef,
        64'h00040293_fc0994e3,
        64'hfff98993_fff94913,
        64'hfe9298e3_00828293,
        64'h0a731663_0002b383,
        64'h0122c333_00040293,
        64'h0ff0000f_fe929ae3,
        64'h00828293_0062b023,
        64'h0122c333_00040293,
        64'h00200993_5aa90913,
        64'h00c91913_aa590913,
        64'h00d91913_52b90913,
        64'h00c91913_2ad9091b,
        64'h02ad5937_0004bc23,
        64'h0004b823_0004b423,
        64'h0004b023_00e49493,
        64'h0014849b_000204b7,
        64'h01f41413_0010041b
    };

    logic [$clog2(RomSize)-1:0] addr_q;

    always_ff @(posedge clk_i) begin
        if (req_i) begin
            addr_q <= addr_i[$clog2(RomSize)-1+3:3];
        end
    end

    // this prevents spurious Xes from propagating into
    // the speculative fetch stage of the core
    assign rdata_o = (addr_q < RomSize) ? mem[addr_q] : '0;
endmodule
