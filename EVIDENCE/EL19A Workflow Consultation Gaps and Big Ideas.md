# EL19A Workflow Consultation: Gaps and Big Ideas

Prepared by Claude, 2026-11-22. Based on the repo state at HEAD `0d4042e` (1,732 commits, 408 work orders). I have not opened the PDFs or checked every work order, so unverified points are flagged.

## What we're missing

1. **We're strong on where, weak on what.** The catalogue has 179 tables: 158 are Reader-Verified, 20 are Query-Traced and only 1 is Semantic-Strong. More structural work orders won't close that. The next gain is naming what tables and variables mean.
2. **We built a symbol table and may not have joined it.** `INDEX/` already has the OBD Mode 01 map, a Consult Mode $22 PID map, a DTC crosswalk and an MMIO census. Whether these are joined to the catalogue's query variables was not checked. If not, that join names many tables at once.
3. **An unused corpus.** The repo holds the UpRev Nissan Tuning Guide, Nistune MAF notes and a knock-listener paper, and no work order cites them (no mentions found in `CONTROL`). They are likely to hold table names, units and conventions.
4. **Everything is static.** We read code but never run it.
5. **No falsifiable hypotheses.** Claims are tiered by evidence, but none are written as "if X is true, Y must hold, and here is the cheap test."

## Big ideas

- **Name tables by their query variable.** Join each table's query RAM address to the Consult and OBD name tables. A curve queried by a variable the Consult map calls coolant is a coolant curve. This is a join across files that already exist.
- **Run the ROM.** Build or reuse a minimal SH-2 interpreter, stub the peripherals, and execute single functions with chosen inputs. It would settle disputes like the row-versus-column orientation by execution, and the dashpot hysteresis would reproduce directly. Going further, a simulated ECU could vary rpm, coolant and load, then log which outputs respond. That names outputs by their response curves. It is larger and riskier, since the SH7058 peripherals need stubs.
- **Vote across two donors.** The repo holds both the V6 master A2L and a second A2L (`RFCC_2XHK19BDF1`), but the second is cited only in older work orders. Accept a name only when two independent sources agree on shape, units and range, and match by those, not by address.
- **Start from the sinks.** The MMIO census lists every hardware output. Trace backward from each actuator pin to its command variable and then to its tables. Spark, injection and the idle valve become anchored from the output side.
- **Use Mode 06 on the misfire car.** Mode 06 test results include their limits, which come from ROM constants. A P0300 gives a reason to read the misfire monitor values, which would pair ROM thresholds with named tests. Whether Torque exposes Mode 06 on this ECU is unconfirmed.
- **Experiments by information gain.** Rank the next tests by how many hypotheses each resolves. Static, emulator and live tests all go in the same list, and the live ones wait until the car is checked.

## Workflow

The FIFO lanes keep workers busy, but the backlog is structural. Add a **semantic lane** with three work orders:

1. the query-variable join;
2. a glossary extracted from the PDFs;
3. an SH-2 interpreter pilot on one function, with `sub_22CB8` as the test.

## Next step

Choose which of these to draft as a work order.
