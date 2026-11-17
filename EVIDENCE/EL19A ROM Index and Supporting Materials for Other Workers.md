# EL19A ROM: Index and Supporting Materials for Other Workers

Prepared by Claude, 2026-11-17. Basis: the EL19A work done in this conversation.

## Summary

The materials below are ranked by how much time was lost re-deriving each one during this work. A free-tier worker probably cannot run code, so everything should be precomputed, sorted by address, and split into slices small enough to paste into its context.

## 1. RAM cross-reference at byte and bit level (highest value)

- **Contents:** One record per access: RAM address, PC, enclosing function, read or write, width, the bit mask tested, set or cleared, and the access form (literal, GBR-resolved, base plus displacement, base plus `r0`).
- **Evidence:** This was rebuilt by hand for `FFFF85DF` (2 readers found), `FFFF860D` (about 35 readers of bit 3 or bit 5) and `FFFF84BA` (126 readers, no writer).
- **Also needed:** An "unresolved access sites" list, meaning accesses where the base or index could not be determined. It tells a worker where the index is blind.

## 2. Function and GBR map, with the scheduler

- **Contents:** Function bounds, the GBR value inside each function, callers and callees, and the order ISR → `sub_2088C` → task table.
- **Evidence:** Each prologue had to be read to learn its GBR, and the values differ. `sub_3BA88` uses `FFFF1E54`, `sub_46E3E` uses `0x821E` (a ROM address), and `sub_403D8` uses `FFFF1028`. A wrong GBR silently gives wrong addresses.

## 3. Calibration scalar and table index

- **Contents:** Each ROM address in the calibration area: its value, every pool reference, how it is used (compared, copied to a RAM shadow, or used as a table base), and the query expression and result destination for each lookup call.
- **Evidence:** `0x8550` has a single reader. `0x8485` is only shadow-copied to `FFFF36C1`. `0x848A` and `0x848B` pair with `E678` and `E688`. The E974 result is only tested for zero or non-zero.

## 4. Base-register dictionary

- **Contents:** The common struct bases (`FFFF1054`, `FFFF2150`, `FFFF1990`, `FFFF1CA8`, `FFFF85C4`, `FFFF3628`) with the offsets already seen and what each one holds, by address only.
- **Why:** Code such as `FFFF2150+0x52F` or `FFFF85C4+0x1B` is opaque without it.

## 5. False-alias and verified-facts register

- **Contents:**
  - Known traps: `byte_85DF` in a `.data.l` pool is ROM `0x85DF`, not RAM. A register labelled as a byte was accessed as a word. The `0x55xxx` GBR over-reach.
  - One line per verified fact: address, claim, PCs, evidence level, how a negative was searched, and who checked it.
- **Why:** It replaces prose ledger entries, and it lets the negative-claim standard be applied mechanically.

## 6. Three worked traces as few-shot examples

- **Suggested traces:** The dashpot start (`E678` → `0x848A` → flag `FFFF1DB4` → `FFFF1018`), `FFFF85DF` → `FFFF1992` → `sub_27720` → GR11A, and a delay-chain flag.
- **Why:** A weaker model improves most from seeing a complete trace, with the reasoning checks included.

## 7. Peripheral map and interrupt entries

- **Contents:** Register name, address, accessing PCs and configuration sites, plus the vector pointers.
- **Evidence:** The ATU-II channel 11 and APC lead needed exactly this.

## Format rules

- TSV, sorted by address, one slice per 256-byte RAM page or 4 KB ROM block, so a worker loads only its target.
- Every file states the ROM MD5, the listing version, and its method limits (forms covered, window sizes).
- Raw text only, no saved web pages.
- Pre-extract the relevant slices into each work-order packet.

## What to avoid

- No database or UI.
- No semantic names in the index. Keep it to facts, and keep naming as a separate, evidence-gated step.

## Caveats

- One generator script produces all of it. It must pass regression cases first: the `PKIOR_W` stale-register alias, the two `FFFF85DF` readers, and the `0x55xxx → FFFF8AF0` case.
- A static index still misses computed pointers and bulk copies, which is why item 1 carries the unresolved-sites file.

## Next step

Items 1 to 3 can be built first, since the ROM and listing are available in this conversation.
