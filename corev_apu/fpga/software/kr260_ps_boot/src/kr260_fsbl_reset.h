/* SPDX-License-Identifier: Apache-2.0 */
#ifndef KR260_FSBL_RESET_H
#define KR260_FSBL_RESET_H
#include "xil_io.h"
/* pl_resetn0 = GPIO bank5 bit31 / EMIO95 in this XSA. Preserve other GPIOs. */
static inline void Kr260HoldCva6(void)
{
    Xil_Out32(0xff0a002cU, 0x7fff0000U); /* preload output low */
    Xil_Out32(0xff0a0344U, Xil_In32(0xff0a0344U) | 0x80000000U);
    Xil_Out32(0xff0a0348U, Xil_In32(0xff0a0348U) | 0x80000000U);
    __asm__ volatile("dsb sy" ::: "memory");
}
#endif
