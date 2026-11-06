#include "kr260_boot.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static struct { uint64_t a,v; } mem[32];
static unsigned count, released, writes, polls, mode;
static uint32_t gpio, dir, oen, pcap, ddr, hp;
static int corrupt, release_fail;
static uint64_t *word(uint64_t a) {
    for(unsigned i=0;i<count;i++) if(mem[i].a==a) return &mem[i].v;
    assert(count<32); mem[count].a=a; return &mem[count++].v;
}
static uint32_t r32(uint64_t a) {
    if(a==KR260_GPIO_DATA) return gpio;
    if(a==KR260_GPIO_DIR) return dir;
    if(a==KR260_GPIO_OEN) return oen;
    if(a==KR260_PCAP_STATUS) return pcap;
    if(a==KR260_DDR_STATUS) return ddr;
    if(a==KR260_HP_RDCTRL || a==KR260_HP_WRCTRL) return hp;
    assert(0); return 0;
}
static void w32(uint64_t a,uint32_t v) {
    assert(a==KR260_GPIO_MASK_MSW && v==0x7fff8000);
    assert(!released && writes==14);
    for(unsigned i=0;i<32;i+=8) assert(*word(KR260_STATUS+i)==0);
    released++;
    if(!release_fail) gpio |= KR260_RESET_BIT;
}
static uint64_t r64(uint64_t a) {
    if(released && a==KR260_STATUS) {
        polls++;
        if(polls<3) return UINT64_C(0x55aa55aa55aa55aa);
        if(mode==0) return 1;
        if(mode==1) return UINT64_MAX;
        return 0;
    }
    if(released && a>KR260_STATUS && a<KR260_STATUS+32) return a-KR260_STATUS;
    return *word(a) ^ (corrupt ? 1 : 0);
}
static void w64(uint64_t a,uint64_t v) { assert(!released); *word(a)=v; writes++; }
static void barrier(void) {}
static void delay(unsigned n) { assert(n==1); }
static kr260_io io={r32,w32,r64,w64,barrier,delay};
static kr260_failure failure;
static void init(void) {
    memset(mem,0,sizeof(mem)); count=released=writes=polls=mode=0;
    gpio=0x1234; dir=oen=KR260_RESET_BIT; pcap=8; ddr=hp=1;
    corrupt=release_fail=0;
    *word(KR260_STATUS)=1; /* stale PASS must be cleared */
}
int main(void) {
    init(); assert(kr260_boot(&io,10,&failure)==KR260_OK); assert(released==1 && gpio==0x80001234 && polls==3);
    init(); gpio |= KR260_RESET_BIT; assert(kr260_boot(&io,10,&failure)==KR260_RESET_NOT_HELD); assert(!writes && !released);
    init(); dir=0; assert(kr260_boot(&io,10,&failure)==KR260_RESET_NOT_HELD); assert(!released);
    init(); oen=0; assert(kr260_boot(&io,10,&failure)==KR260_RESET_NOT_HELD); assert(!released);
    init(); pcap=0; assert(kr260_boot(&io,10,&failure)==KR260_PL_NOT_READY); assert(!released);
    init(); ddr=0; assert(kr260_boot(&io,10,&failure)==KR260_DDR_NOT_READY); assert(!released);
    init(); hp=0; assert(kr260_boot(&io,10,&failure)==KR260_HP_WIDTH_ERROR); assert(!released);
    init(); corrupt=1; assert(kr260_boot(&io,10,&failure)==KR260_DDR_CHECK_FAILED); assert(!released && failure.address==KR260_DDR_BASE);
    init(); mode=1; assert(kr260_boot(&io,10,&failure)==KR260_CVA6_FAILED); assert(released==1 && failure.address==8 && failure.expected==16 && failure.observed==24);
    init(); mode=2; assert(kr260_boot(&io,5,&failure)==KR260_TIMEOUT); assert(released==1 && polls==5);
    init(); release_fail=1; assert(kr260_boot(&io,10,&failure)==KR260_RELEASE_FAILED); assert(released==1 && polls==0);
    puts("PASS: 11 boot sequence scenarios");
}
