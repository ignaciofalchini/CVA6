/* SPDX-License-Identifier: Apache-2.0 */
#include "kr260_boot.h"
#include "xil_io.h"
#include "xil_cache.h"
#include "xil_printf.h"
#include "sleep.h"

static uint32_t read32(uint64_t a) { return Xil_In32((UINTPTR)a); }
static void write32(uint64_t a, uint32_t v) { Xil_Out32((UINTPTR)a, v); }
static uint64_t read64(uint64_t a) { return *(volatile uint64_t *)(UINTPTR)a; }
static void write64(uint64_t a, uint64_t v) { *(volatile uint64_t *)(UINTPTR)a = v; }
static void barrier(void) { __asm__ volatile("dsb sy" ::: "memory"); }
static void delay_ms(unsigned n) { while (n--) usleep(1000); }
static void hex64(const char *name, uint64_t v) {
    xil_printf("%s=0x%08x%08x\r\n", name, (unsigned)(v >> 32), (unsigned)v);
}
int main(void)
{
    uint64_t el;
    __asm__ volatile("mrs %0, CurrentEL" : "=r"(el));
    xil_printf("KR260 PS bare-metal: CVA6 DDR startup\r\n");
    if (((el >> 2) & 3U) != 3U) {
        xil_printf("ERROR: run on A53-0 in secure EL3.\r\n");
        for (;;) __asm__ volatile("wfe");
    }
    /* HP0 is non-coherent. Flush/disable CPU data cache before shared DDR use. */
    Xil_DCacheDisable();
    barrier();
    const kr260_io io = {read32, write32, read64, write64, barrier, delay_ms};
    kr260_failure failure;
    kr260_result result = kr260_boot(&io, 30000, &failure);
    static const char *const names[] = {
        "PASS", "RESET_NOT_HELD", "PL_NOT_READY", "DDR_NOT_READY",
        "HP_WIDTH_ERROR", "PS_DDR_CHECK_FAILED", "CVA6_COMPARE_FAILED",
        "TIMEOUT", "RESET_RELEASE_FAILED"
    };
    xil_printf("KR260 result: %s (%u)\r\n", names[result], (unsigned)result);
    if (result == KR260_DDR_CHECK_FAILED || result == KR260_CVA6_FAILED) {
        hex64("address", failure.address);
        hex64("expected", failure.expected);
        hex64("observed", failure.observed);
    }
    xil_printf("CPU parked; no automatic reset/retry.\r\n");
    for (;;) __asm__ volatile("wfe");
}
