/* SPDX-License-Identifier: Apache-2.0 */
#include "kr260_boot.h"

kr260_result kr260_boot(const kr260_io *io, unsigned timeout_ms, kr260_failure *failure)
{
    static const uint64_t probe[] = {
        KR260_DDR_BASE, KR260_DDR_BASE + 0x2000,
        KR260_DDR_BASE + 0x10000, KR260_DDR_BASE + 0x20000000,
        KR260_DDR_END - 8
    };
    const uint64_t pattern = UINT64_C(0x55aa55aaaa55aa55);
    failure->address = failure->expected = failure->observed = 0;
    /* Require the customized FSBL/JTAG sequence. Do not reset a running core. */
    if ((io->read32(KR260_GPIO_DATA) & KR260_RESET_BIT) != 0 ||
        (io->read32(KR260_GPIO_DIR) & KR260_RESET_BIT) == 0 ||
        (io->read32(KR260_GPIO_OEN) & KR260_RESET_BIT) == 0)
        return KR260_RESET_NOT_HELD;
    if ((io->read32(KR260_PCAP_STATUS) & 8U) == 0)
        return KR260_PL_NOT_READY;
    if ((io->read32(KR260_DDR_STATUS) & 7U) != 1U)
        return KR260_DDR_NOT_READY;
    if ((io->read32(KR260_HP_RDCTRL) & 3U) != 1U ||
        (io->read32(KR260_HP_WRCTRL) & 3U) != 1U)
        return KR260_HP_WIDTH_ERROR;

    /* Non-cacheable CPU accesses; write all probes before reading any. */
    for (unsigned pass = 0; pass != 2; ++pass) {
        uint64_t mask = pass ? ~pattern : pattern;
        for (unsigned i = 0; i < sizeof(probe)/sizeof(probe[0]); ++i)
            io->write64(probe[i], probe[i] ^ mask);
        io->barrier();
        for (unsigned i = 0; i < sizeof(probe)/sizeof(probe[0]); ++i) {
            uint64_t got = io->read64(probe[i]);
            if (got != (probe[i] ^ mask)) {
                failure->address = probe[i];
                failure->expected = probe[i] ^ mask;
                failure->observed = got;
                return KR260_DDR_CHECK_FAILED;
            }
        }
    }
    /* Clear a previous run's status BEFORE releasing CVA6. */
    for (unsigned offset = 0; offset != 32; offset += 8)
        io->write64(KR260_STATUS + offset, 0);
    io->barrier();
    io->delay_ms(1);
    /* GPIO masked write: update only bank5 bit31 (EMIO95/pl_resetn0). */
    io->write32(KR260_GPIO_MASK_MSW, UINT32_C(0x7fff8000));
    io->barrier();
    if ((io->read32(KR260_GPIO_DATA) & KR260_RESET_BIT) == 0)
        return KR260_RELEASE_FAILED;
    /* CVA6 owns DDR now. No ARM writes and no reset on timeout/failure. */
    for (unsigned elapsed = 0; elapsed < timeout_ms; ++elapsed) {
        uint64_t status = io->read64(KR260_STATUS);
        if (status == 1) return KR260_OK;
        if (status == UINT64_MAX) {
            io->barrier();
            failure->address = io->read64(KR260_STATUS + 8);
            failure->expected = io->read64(KR260_STATUS + 16);
            failure->observed = io->read64(KR260_STATUS + 24);
            return KR260_CVA6_FAILED;
        }
        /* Ignore the address-dependent pattern when status is a ROM probe. */
        io->delay_ms(1);
    }
    return KR260_TIMEOUT;
}
