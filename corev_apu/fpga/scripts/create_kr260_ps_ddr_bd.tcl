# Create the KR260 PS/DDR portion of the CVA6 system.
#
# The caller must have an open project with board_part
# xilinx.com:kr260_som:part0:2.0. The CVA6-facing interface uses PS physical
# addresses: 0x0000_0000..0x3fff_ffff maps to the lower 1 GiB of DDR_LOW.
# Translation from the CVA6 view (base 0x8000_0000) is explicit in
# ariane_kr260_system.sv.

set_param general.maxThreads 1

set bd_name ariane_kr260_ps_bd
if {[llength [get_bd_designs -quiet $bd_name]] != 0} {
    current_bd_design $bd_name
    puts "KR260_PS_BD=REUSED"
    return
}

create_bd_design $bd_name

set ps_vlnv [lindex [lsort [get_ipdefs -all \
    -filter {VLNV =~ "xilinx.com:ip:zynq_ultra_ps_e:*"}]] end]
if {$ps_vlnv eq ""} {
    error "Vivado does not provide zynq_ultra_ps_e"
}
set ps [create_bd_cell -type ip -vlnv $ps_vlnv zynq_ultra_ps_e_0]
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset "1"} $ps

# Keep the board's complete PS/MIO/DDR preset, but expose to the PL only one
# non-coherent high-performance slave port and one 25 MHz PL clock.
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0                 {0} \
    CONFIG.PSU__USE__M_AXI_GP1                 {0} \
    CONFIG.PSU__USE__M_AXI_GP2                 {0} \
    CONFIG.PSU__USE__S_AXI_GP0                 {0} \
    CONFIG.PSU__USE__S_AXI_GP1                 {0} \
    CONFIG.PSU__USE__S_AXI_GP2                 {1} \
    CONFIG.PSU__USE__S_AXI_GP3                 {0} \
    CONFIG.PSU__USE__S_AXI_GP4                 {0} \
    CONFIG.PSU__USE__S_AXI_GP5                 {0} \
    CONFIG.PSU__USE__S_AXI_GP6                 {0} \
    CONFIG.PSU__SAXIGP2__DATA_WIDTH            {64} \
    CONFIG.PSU__FPGA_PL0_ENABLE                {1} \
    CONFIG.PSU__FPGA_PL1_ENABLE                {0} \
    CONFIG.PSU__FPGA_PL2_ENABLE                {0} \
    CONFIG.PSU__FPGA_PL3_ENABLE                {0} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {25} \
    CONFIG.PSU__USE__IRQ0                      {0} \
] $ps

set reset [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:* \
    proc_sys_reset_0]
set reset_inverter [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:util_vector_logic:* reset_inverter]
set_property -dict [list \
    CONFIG.C_OPERATION {not} \
    CONFIG.C_SIZE {1} \
] $reset_inverter

set const_one [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:* \
    constant_one]
set_property -dict [list CONFIG.CONST_VAL {1}] $const_one
set const_zero [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:* \
    constant_zero]
set_property -dict [list CONFIG.CONST_VAL {0}] $const_zero

set clk_o [create_bd_port -dir O -type clk clk_o]
set_property -dict [list \
    CONFIG.FREQ_HZ {24999750} \
    CONFIG.ASSOCIATED_RESET {rst_no} \
] $clk_o
set rst_no [create_bd_port -dir O -type rst rst_no]
set_property -dict [list CONFIG.POLARITY {ACTIVE_LOW}] $rst_no

connect_bd_net [get_bd_pins $ps/pl_clk0] \
    [get_bd_pins $ps/saxihp0_fpd_aclk] \
    [get_bd_pins $reset/slowest_sync_clk] $clk_o
connect_bd_net [get_bd_pins $ps/pl_resetn0] \
    [get_bd_pins $reset_inverter/Op1]
connect_bd_net [get_bd_pins $reset_inverter/Res] \
    [get_bd_pins $reset/ext_reset_in]
connect_bd_net [get_bd_pins $const_one/dout] \
    [get_bd_pins $reset/dcm_locked]
connect_bd_net [get_bd_pins $const_zero/dout] \
    [get_bd_pins $reset/aux_reset_in] \
    [get_bd_pins $reset/mb_debug_sys_rst]
connect_bd_net [get_bd_pins $reset/peripheral_aresetn] $rst_no

# This is an AXI master as seen from inside the BD: CVA6 is the initiator and
# S_AXI_HP0_FPD is the target. USER/ATOP are intentionally not part of this
# standard AXI4 interface; the HDL boundary handles them explicitly.
set cva6_axi [create_bd_intf_port -mode Slave \
    -vlnv xilinx.com:interface:aximm_rtl:1.0 S_AXI_CVA6]
set_property -dict [list \
    CONFIG.PROTOCOL {AXI4} \
    CONFIG.ADDR_WIDTH {49} \
    CONFIG.DATA_WIDTH {64} \
    CONFIG.AWUSER_WIDTH {1} \
    CONFIG.ARUSER_WIDTH {1} \
    CONFIG.HAS_BURST {1} \
    CONFIG.HAS_LOCK {1} \
    CONFIG.HAS_CACHE {1} \
    CONFIG.HAS_PROT {1} \
    CONFIG.HAS_QOS {1} \
    CONFIG.HAS_REGION {0} \
    CONFIG.HAS_WSTRB {1} \
    CONFIG.NUM_READ_OUTSTANDING {16} \
    CONFIG.NUM_WRITE_OUTSTANDING {16} \
    CONFIG.FREQ_HZ {24999750} \
] $cva6_axi

connect_bd_intf_net $cva6_axi [get_bd_intf_pins $ps/S_AXI_HP0_FPD]
set_property CONFIG.ASSOCIATED_BUSIF {S_AXI_CVA6} $clk_o

# CVA6 exposes five ID bits. The HDL boundary zero-extends them to the six bits
# required by HP0 and checks/truncates the returned upper bit.
set ddr_segment [get_bd_addr_segs $ps/SAXIGP2/HP0_DDR_LOW]
assign_bd_address -offset 0x00000000 -range 0x40000000 \
    -target_address_space [get_bd_addr_spaces S_AXI_CVA6] \
    $ddr_segment -force

validate_bd_design
save_bd_design
puts "KR260_PS_BD=SUCCESS"
