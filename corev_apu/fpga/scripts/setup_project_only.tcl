# Copyright 2018 ETH Zurich and University of Bologna.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Author: Florian Zaruba <zarubaf@iis.ee.ethz.ch>

# hard-coded to Genesys 2 for the moment

if {$::env(BOARD) eq "genesys2"} {
    add_files -fileset constrs_1 -norecurse constraints/genesys-2.xdc
} elseif {$::env(BOARD) eq "kc705"} {
      add_files -fileset constrs_1 -norecurse constraints/kc705.xdc
} elseif {$::env(BOARD) eq "vc707"} {
      add_files -fileset constrs_1 -norecurse constraints/vc707.xdc
} elseif {$::env(BOARD) eq "nexys_video"} {
      add_files -fileset constrs_1 -norecurse constraints/nexys_video.xdc
} else {
      exit 1
}

read_ip { \
      "xilinx/xlnx_mig_7_ddr3/xlnx_mig_7_ddr3.srcs/sources_1/ip/xlnx_mig_7_ddr3/xlnx_mig_7_ddr3.xci" \
      "xilinx/xlnx_axi_clock_converter/xlnx_axi_clock_converter.srcs/sources_1/ip/xlnx_axi_clock_converter/xlnx_axi_clock_converter.xci" \
      "xilinx/xlnx_axi_dwidth_converter/xlnx_axi_dwidth_converter.srcs/sources_1/ip/xlnx_axi_dwidth_converter/xlnx_axi_dwidth_converter.xci" \
      "xilinx/xlnx_axi_dwidth_converter_dm_slave/xlnx_axi_dwidth_converter_dm_slave.srcs/sources_1/ip/xlnx_axi_dwidth_converter_dm_slave/xlnx_axi_dwidth_converter_dm_slave.xci" \
      "xilinx/xlnx_axi_dwidth_converter_dm_master/xlnx_axi_dwidth_converter_dm_master.srcs/sources_1/ip/xlnx_axi_dwidth_converter_dm_master/xlnx_axi_dwidth_converter_dm_master.xci" \
      "xilinx/xlnx_axi_gpio/xlnx_axi_gpio.srcs/sources_1/ip/xlnx_axi_gpio/xlnx_axi_gpio.xci" \
      "xilinx/xlnx_axi_quad_spi/xlnx_axi_quad_spi.srcs/sources_1/ip/xlnx_axi_quad_spi/xlnx_axi_quad_spi.xci" \
      "xilinx/xlnx_clk_gen/xlnx_clk_gen.srcs/sources_1/ip/xlnx_clk_gen/xlnx_clk_gen.xci" \
}
# read_ip xilinx/xlnx_protocol_checker/ip/xlnx_protocol_checker.xci

set_property include_dirs { \
	"src/axi_sd_bridge/include" \
	"../../vendor/pulp-platform/common_cells/include" \
	"../../vendor/pulp-platform/axi/include" \
	"../../core/cache_subsystem/hpdcache/rtl/include" \
	"../register_interface/include" \
	"../../core/include" \
} [current_fileset]

source scripts/add_sources.tcl

set_property top ${project}_xilinx [current_fileset]

if {$::env(BOARD) eq "genesys2"} {
    read_verilog -sv {src/genesysii.svh ../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh}
    set file "src/genesysii.svh"
    set registers "../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh"
} elseif {$::env(BOARD) eq "kc705"} {
      read_verilog -sv {src/kc705.svh ../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh}
      set file "src/kc705.svh"
      set registers "../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh"
} elseif {$::env(BOARD) eq "vc707"} {
      read_verilog -sv {src/vc707.svh ../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh}
      set file "src/vc707.svh"
      set registers "../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh"
} elseif {$::env(BOARD) eq "nexys_video"} {
      read_verilog -sv {src/nexys_video.svh ../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh}
      set file "src/nexys_video.svh"
      set registers "../../vendor/pulp-platform/common_cells/include/common_cells/registers.svh"
} else {
    exit 1
}

set file_obj [get_files -of_objects [get_filesets sources_1] [list "*$file" "$registers"]]
set_property -dict { file_type {Verilog Header} is_global_include 1} -objects $file_obj

update_compile_order -fileset sources_1

add_files -fileset constrs_1 -norecurse constraints/$project.xdc


puts ""
puts "============================================================"
puts "Proyecto CVA6 preparado correctamente."
puts "No se ejecuto sintesis."
puts "Usar Flow Navigator -> Run Synthesis."
puts "============================================================"
