/*
 * auriga_test.c
 *
 * Harmless test binary to trigger the AURIGA_driver_APT1 YARA rule.
 * It contains the wide (UTF-16LE) string literals used by the rule.
 */

#include <stdio.h>
#include <wchar.h>

int main(void)
{
    /* Strings expected by the YARA rule (wide literals) */
    const wchar_t *s1 = L"Services\\riodrv32";
    const wchar_t *s2 = L"riodrv32.sys";
    const wchar_t *s3 = L"svchost.exe";
    const wchar_t *s4 = L"wuauserv.dll";
    const wchar_t *s5 = L"arp.exe";

    /* PDB-like path which also satisfies the rule (the rule uses $pdb = "projects\\auriga" wide ascii) */
    const wchar_t *pdb = L"projects\\auriga";

    /* Print them so the compiler keeps them in the binary data section */
    wprintf(L"Marker s1: %ls\n", s1);
    wprintf(L"Marker s2: %ls\n", s2);
    wprintf(L"Marker s3: %ls\n", s3);
    wprintf(L"Marker s4: %ls\n", s4);
    wprintf(L"Marker s5: %ls\n", s5);
    wprintf(L"PDB marker: %ls\n", pdb);

    /* Keep program alive briefly */
    return 0;
}
