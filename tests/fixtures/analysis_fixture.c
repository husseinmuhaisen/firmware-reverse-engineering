#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
volatile const unsigned char aes_prefix[] = {0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76};
volatile const uint32_t md5_prefix[] = {0xd76aa478,0xe8c7b756,0x242070db,0xc1bdceee};
volatile const unsigned char sha_be[] = {0x42,0x8a,0x2f,0x98,0x71,0x37,0x44,0x91,0xb5,0xc0,0xfb,0xcf,0xe9,0xb5,0xdb,0xa5};
int auth_check(const char *input) {
    puts("password login failed");
    return strcmp(input, "fixture-only-password") == 0;
}
void call_candidates(void) {
    char first[64], second[64];
    char *value = getenv("FIXTURE_INPUT");
    if (!value || strlen(value) >= sizeof(first)) return;
    strcpy(first, value);
    strcpy(second, value);
    puts(first); puts(second);
}
void rename_candidate(void) { puts("error during init"); }
int main(int argc, char **argv) {
    rename_candidate();
    call_candidates();
    return auth_check(argc > 1 ? argv[1] : "") + aes_prefix[argc & 15] + md5_prefix[0] + sha_be[0];
}
