from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from osiris_keystream_probe import run_probe
from osiris_rom_inspector import (
    OsirisContainerInfo,
    extract_romdata_slice,
    inspect_osiris_file,
    is_osiris_rom,
)


def prepare_workbench_rom(
    path: Path,
    unmask_fn: Optional[Callable[[bytes, OsirisContainerInfo], bytes]] = None,
    donor_path: Optional[Path] = None,
    compare_path: Optional[Path] = None,
    run_diagnostics: bool = True,
) -> Tuple[Optional[bytes], Dict[str, Any]]:
    """
    Prepare a flat `.bin` or `.OsirisROM` file for the SH705x workbench.

    Returns `(flat_rom_or_none, report_dict)`. When `unmask_fn` is omitted on an
    `.OsirisROM` file, returns `(None, report)` with container framing and structural
    diagnostics populated so the workbench can display inspection state safely.
    """
    raw = path.read_bytes()
    if not is_osiris_rom(raw):
        return raw, {
            "container_type": "flat_bin",
            "source": path.name,
            "size": len(raw),
            "ready_for_scanner": True,
        }

    info, payload = extract_romdata_slice(raw, source_name=path.name)
    report: Dict[str, Any] = {
        "container_type": "osiris_rom",
        "source": path.name,
        "ready_for_scanner": False,
        "inspection": inspect_osiris_file(
            path,
            donor_path=donor_path,
            compare_path=compare_path,
        ),
    }
    if run_diagnostics:
        report["keystream_probe"] = run_probe(path)

    if unmask_fn is None:
        return None, report

    unmasked = unmask_fn(payload, info)
    report["ready_for_scanner"] = True
    report["unmasked_size"] = len(unmasked)
    return unmasked, report
```[cite: 10, 12, 14]

---

### 4. Practical Hardening Notes for Workbench Use
* **Text/String Dumps vs. Raw Bytes:** The sample buffers (`` and ``) appear as decoded/escaped text previews rather than raw binary `.OsirisROM` files—always run `inspect_osiris_file` and `run_probe` directly on actual `.OsirisROM` binary files on disk so byte offsets, `struct.unpack` fields, and SHA-256 hashes stay exact[cite: 10, 12, 15, 16].
* **Section Tag Parsing:** `_match_tag_at` currently recognizes `AITuneDesc`, `#mdc`, and fallback 8-byte printable ASCII tags; if additional UpRev sections appear in other ROM variants, add their exact byte tags to `KNOWN_MULTI_BYTE_TAGS` or `KNOWN_SHORT_TAGS`[cite: 10].
* **Pair-XOR & Period Tuning:** Adjust `--periods` and `--period-stride` in `osiris_rom_inspector.py` for quick sweeps on large batches, then run `probe_periodic_key_from_constant_span` with `--span-start`, `--span-end`, and `--assumed-byte` on candidate constant regions[cite: 10, 12].

<FollowUp label="Want me to extend the adapter with batch comparison and CLI reporting hooks?" query="Extend the workbench adapter with batch Osiris-vs-Osiris and donor comparison helpers plus clean CLI summary output."/>