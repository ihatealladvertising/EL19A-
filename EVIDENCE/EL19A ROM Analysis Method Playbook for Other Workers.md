# EL19A ROM Analysis: Method Playbook for Other Workers

Prepared by Claude, 2026-11-17. Basis: the EL19A work done in this conversation. I have not observed the other worker's process, only its output in the ledger, so the comparison below is a judgement and not a measurement.

## Summary

Most of the gap in trace quality comes from method and tooling, and relatively little from raw model skill. That is useful, because method and tooling can be handed to another worker.

## What the ability breaks down into (most to least transferable)

**1. A run-and-verify loop.** This matters more than anything else.

- I run code in a sandbox and never rely on reading the listing alone.
- I confirmed that all 334,126 in-ROM listing lines match the ROM bytes, so every PC I cite is real.
- I grep and script against the 27 MB listing instead of reading it.
- I reproduce numbers before trusting them. The `E678`/`E688` bytes ×2 and the `F3D6`/`F3DE` bytes ×0.3575 matched your lists, and `0x848A`/`0x848B` came out as 52.34 at ×0.78125.
- A model without code execution has to read excerpts and reason from memory, which is where most trace errors come from.

**2. A reference-resolution ladder.** A byte can be reached in many ways, and a trace only counts once each has been checked.

- Absolute literal.
- GBR-relative, using the actual GBR value at that instruction.
- Base register plus displacement.
- Base plus `r0` index.
- Pointer tables, copy helpers and block copies.
- This is how I found the readers of `FFFF85DF` (`mov.b @(r0,r12)` with `r0=0x1B`), which a literal-only or GBR-only search misses.

**3. ISA fluency.** This is the part that is really model knowledge, but it fits on one page (see the cheat sheet below).

**4. Pattern recognition.** I recognise common code shapes quickly: a compare with hysteresis (`+3` when the flag is already set), a divide-by-10 helper, or a ROM scalar copied to a RAM shadow at init. Concrete examples help any model here.

**5. Claim discipline.** I label what is confirmed and what is a hypothesis, and I state how a negative result was searched.

## Where I went wrong (worth passing on)

- My resolver kept stale registers and produced a false hit in an `INT_ATU…` routine. It also lost `r0` after `extu.b`, and its 16-instruction window dropped a base register.
- I misread `sub_25D36` at first. It is a divide-by-10 helper, not a flag helper.
- Listing labels mislead. `byte_85DF` in a `.data.l` pool is ROM `0x85DF`, not RAM, and a register labelled as a byte was accessed as a word.
- My results are unreviewed. A second worker should recheck the high-impact ones.

## Hierarchy for another worker

0. **Integrity.** Check hashes, and check that the listing bytes match the ROM.
1. **Structure.** Find function bounds, each function's GBR value, and the dispatch and pointer tables.
2. **Resolve.** Run the reference ladder on the exact target byte.
3. **Dataflow.** Trace forward from writers to readers, and verify the arithmetic (width, signedness, branch polarity).
4. **Endpoint.** Prove any hardware link by naming the register write and its configuration.
5. **Report.** State the confidence level, and the search methods behind any negative.

## ISA and ROM cheat sheet (checked in this ROM)

- A branch delay slot always executes (`bt/s`, `bra`, `rts`).
- `bt` branches when T=1, and `tst #imm` sets T when the bit is clear.
- `cmp/hs Rm,Rn` sets T when Rn ≥ Rm (unsigned).
- `mov.b` and `mov.w` sign-extend. `mov #imm` also sign-extends, so offsets above 0x7F need `extu.b`.
- A 16-bit literal like `h'8xxx` becomes `FFFF8xxx`. A 32-bit `.data.l` value below 0x100000 is a ROM pointer.
- ROM base is 0 and RAM is `FFFF xxxx`. The A/D data registers are at `FFFFF800`.
- Calibration scalars sit near `0x8000–0x9000` and are reached through a pool pointer. Some are copied to RAM at init.
- `sub_22E10` returns table\[15\] for a query of 0xF0 or more, and otherwise interpolates with `floor((B−A)·frac/16)`.
- The dispatcher `sub_2088C` runs the nine-entry table at `0x21A64`.
- The flag bytes at `860D`, `860B` and `860F` form a one-pass delay chain.

## Highest-return move

Compute the structure once and share the results, so that the worker's individual skill matters less. I would generate these files:

- a per-function GBR map,
- a literal-pool reference index,
- a reader/writer index for flag bytes,
- a list of known false aliases.

That is a one-time script. It is justified because the false positives and negatives described above come from skipping this work.

## Next step

This could be turned into a short markdown playbook plus the index files, for use by any worker on this ROM.
