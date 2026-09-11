# 25 MHz external clock
create_clock -period 40.000 -name clk [get_ports clk_i]
set_property PACKAGE_PIN C3 [get_ports clk_i]
set_property IOSTANDARD LVCMOS18 [get_ports clk_i]