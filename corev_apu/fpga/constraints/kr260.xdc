# KR260 minimal synthesis target.
#
# `clk_i` is an intentionally abstract PL clock input.  No PACKAGE_PIN or
# IOSTANDARD is assigned until the KR260 PS/PL clocking and board wiring are
# selected.  The 40 ns period is the requested initial 25 MHz CVA6 frequency.
create_clock -name cva6_clk -period 40.000 [get_ports clk_i]
