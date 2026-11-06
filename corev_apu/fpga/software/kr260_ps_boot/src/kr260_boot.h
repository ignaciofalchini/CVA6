/* SPDX-License-Identifier: Apache-2.0 */
#ifndef KR260_BOOT_H
#define KR260_BOOT_H
#include <stdint.h>
#define KR260_DDR_BASE UINT64_C(0x800000000)
#define KR260_DDR_END UINT64_C(0x840000000)
#define KR260_STATUS (KR260_DDR_BASE + UINT64_C(0x4000))
#define KR260_GPIO_DATA UINT64_C(0xff0a0054)
#define KR260_GPIO_DIR UINT64_C(0xff0a0344)
#define KR260_GPIO_OEN UINT64_C(0xff0a0348)
#define KR260_GPIO_MASK_MSW UINT64_C(0xff0a002c)
#define KR260_RESET_BIT UINT32_C(0x80000000)
#define KR260_PCAP_STATUS UINT64_C(0xffca3010)
#define KR260_DDR_STATUS UINT64_C(0xfd070004)
#define KR260_HP_RDCTRL UINT64_C(0xfd380000)
#define KR260_HP_WRCTRL UINT64_C(0xfd380014)

typedef struct {
    uint32_t (*read32)(uint64_t);
    void (*write32)(uint64_t, uint32_t);
    uint64_t (*read64)(uint64_t);
    void (*write64)(uint64_t, uint64_t);
    void (*barrier)(void);
    void (*delay_ms)(unsigned);
} kr260_io;

typedef enum {
    KR260_OK = 0,
    KR260_RESET_NOT_HELD,
    KR260_PL_NOT_READY,
    KR260_DDR_NOT_READY,
    KR260_HP_WIDTH_ERROR,
    KR260_DDR_CHECK_FAILED,
    KR260_CVA6_FAILED,
    KR260_TIMEOUT,
    KR260_RELEASE_FAILED
} kr260_result;

typedef struct {
    uint64_t address, expected, observed;
} kr260_failure;

kr260_result kr260_boot(const kr260_io *io, unsigned timeout_ms, kr260_failure *failure);
#endif
