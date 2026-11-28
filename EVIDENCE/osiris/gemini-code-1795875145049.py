#!/usr/bin/env python3
"""
High-yield diagnostic probe for UpRev .OsirisROM payloads (`osiris_keystream_probe.py`).

Companion to `osiris_rom_inspector.py`:
- Inspects `#mdc` and trailing bytes past the last parsed TLV record.
- Extracts deviating pairs from the `0x0C0000..0x100000` (`k % 64`) XOR lattice.
- Recovers candidate periodic XOR keys over known/assumed plaintext spans (e.g. 0xFF/0x00
  runs or donor ROM windows) and scores SH705x reset-vector plausibility.
"""
from __future__ import annotations

import argparse
import json
import struct
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from osiris_rom_inspector import extract_romdata_slice


@dataclass
class LatticeDeviation:
    pair_index: int
    residue_k_mod_64: int
    romdata_offset: int
    word_even_be: str
    word_odd_be: str
    pair_xor_be: str
    expected_residue_xor_be: str


@dataclass
class KeyCandidate:
    period_bytes: int
    key_hex: str
    coverage_bytes: int
    support_ratio: float
    sh705x_sp_plausible: bool
    sh705x_pc_plausible: bool
    unmasked_ff_ratio: float
    unmasked_zero_ratio: float
    sample_head_hex: str


def extract_lattice_deviations(payload: bytes, limit: int = 32) -> List[LatticeDeviation]:
    """Return pairs in `0x0C0000..0x100000` that deviate from their `(k % 64)` modal pair-XOR."""
    if len(payload) < 0x100000:
        return []

    base = 0x0C0000
    region = payload[base:0x100000]
    words = struct.unpack(f">{len(region) // 4}I", region)
    pair_xors = [words[2 * k] ^ words[2 * k + 1] for k in range(len(words) // 2)]

    buckets: Dict[int, Counter] = defaultdict(Counter)
    for k, px in enumerate(pair_xors):
        buckets[k % 64][px] += 1

    modal: Dict[int, int] = {r: buckets[r].most_common(1)[0][0] for r in range(64)}
    devs: List[LatticeDeviation] = []

    for k, px in enumerate(pair_xors):
        r = k % 64
        if px != modal[r]:
            w0 = words[2 * k]
            w1 = words[2 * k + 1]
            devs.append(
                LatticeDeviation(
                    pair_index=k,
                    residue_k_mod_64=r,
                    romdata_offset=base + k * 8,
                    word_even_be=f"0x{w0:08X}",
                    word_odd_be=f"0x{w1:08X}",
                    pair_xor_be=f"0x{px:08X}",
                    expected_residue_xor_be=f"0x{modal[r]:08X}",
                )
            )
            if len(devs) >= limit:
                break

    return devs


def _plausible_sh705x_vectors(buf: bytes) -> Tuple[bool, bool]:
    """
    Check basic SH705x reset vector plausibility in the first 8 bytes:
    - Initial SP typically points into internal RAM (`0xFFFFxxxx` on SH705x)
    - Initial PC typically points into ROM (`0x0000xxxx` .. `0x0010xxxx`)
    """
    if len(buf) < 8:
        return False, False
    sp, pc = struct.unpack(">II", buf[:8])
    sp_ok = (sp & 0xFFFF0000) == 0xFFFF0000 and (sp & 0x3) == 0
    pc_ok = 0x00000100 <= pc <= 0x00100000 and (pc & 0x1) == 0
    return sp_ok, pc_ok


def probe_periodic_key_from_constant_span(
    payload: bytes,
    start: int,
    end: int,
    assumed_plain_byte: int,
    periods: Tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512),
) -> List[KeyCandidate]:
    """
    Assume `payload[start:end]` is a known constant byte (e.g. `0xFF` or `0x00`),
    recover `key_byte[(i) % p] = payload[i] ^ assumed_plain_byte`, and score how
    consistently that candidate key applies across the entire `start:end` window
    and at `payload[0:8]`.
    """
    s = max(0, start)
    e = min(len(payload), end)
    if e <= s:
        return []

    span = payload[s:e]
    results: List[KeyCandidate] = []

    for p in periods:
        if p <= 0 or len(span) < p:
            continue

        votes: List[Counter] = [Counter() for _ in range(p)]
        for idx, b in enumerate(span):
            abs_pos = s + idx
            key_val = b ^ assumed_plain_byte
            votes[abs_pos % p][key_val] += 1

        key_bytes = bytearray(p)
        agree_count = 0
        for r in range(p):
            top_k, _ = votes[r].most_common(1)[0]
            key_bytes[r] = top_k

        for idx, b in enumerate(span):
            abs_pos = s + idx
            if (b ^ key_bytes[abs_pos % p]) == assumed_plain_byte:
                agree_count += 1

        ratio = agree_count / len(span)
        head_unmasked = bytes(payload[i] ^ key_bytes[i % p] for i in range(min(len(payload), 64)))
        sp_ok, pc_ok = _plausible_sh705x_vectors(head_unmasked)

        # Sample full payload with this periodic key for quick 0xFF / 0x00 density check
        sample = bytes(payload[i] ^ key_bytes[i % p] for i in range(0, len(payload), 16))
        ff_ratio = sample.count(0xFF) / len(sample)
        zero_ratio = sample.count(0x00) / len(sample)

        results.append(
            KeyCandidate(
                period_bytes=p,
                key_hex=bytes(key_bytes).hex(),
                coverage_bytes=len(span),
                support_ratio=round(ratio, 6),
                sh705x_sp_plausible=sp_ok,
                sh705x_pc_plausible=pc_ok,
                unmasked_ff_ratio=round(ff_ratio, 6),
                unmasked_zero_ratio=round(zero_ratio, 6),
                sample_head_hex=head_unmasked[:16].hex(),
            )
        )

    results.sort(key=lambda c: (-c.support_ratio, -(c.sh705x_sp_plausible and c.sh705x_pc_plausible), c.period_bytes))
    return results


def run_probe(
    osiris_path: Path,
    span_start: int = 0x0E0000,
    span_end: int = 0x100000,
    assumed_byte: int = 0xFF,
) -> Dict[str, object]:
    raw = osiris_path.read_bytes()
    info, payload = extract_romdata_slice(raw, source_name=osiris_path.name)

    last_end = max((s.offset + s.total_record_len for s in info.sections), default=0)
    post_sections_bytes = raw[last_end:]

    mdc_info = None
    for sec in info.sections:
        if sec.tag == "#mdc":
            sec_slice = raw[sec.offset : sec.offset + min(sec.total_record_len, 64)]
            mdc_info = {
                "offset": f"0x{sec.offset:X}",
                "payload_len": sec.payload_len,
                "total_record_len": sec.total_record_len,
                "flags": f"0x{sec.flags:08X}",
                "record_head_hex": sec_slice.hex(),
            }

    devs = extract_lattice_deviations(payload, limit=20)
    candidates = probe_periodic_key_from_constant_span(
        payload,
        start=span_start,
        end=span_end,
        assumed_plain_byte=assumed_byte,
    )

    return {
        "file": info.source_name,
        "romdata_sha256": info.romdata_sha256,
        "sections": [asdict(s) for s in info.sections],
        "mdc_section": mdc_info,
        "post_sections_tail_len": len(post_sections_bytes),
        "post_sections_tail_hex": post_sections_bytes[:64].hex(),
        "lattice_deviations_sample": [asdict(d) for d in devs],
        "periodic_key_candidates": [asdict(c) for c in candidates[:8]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe OsirisROM framing, #mdc tail, lattice deviations, and periodic XOR keys.")
    parser.add_argument("osiris_file", type=Path, help="Path to .OsirisROM file")
    parser.add_argument("--span-start", type=lambda x: int(x, 0), default=0x0E0000, help="Assumed constant-byte span start")
    parser.add_argument("--span-end", type=lambda x: int(x, 0), default=0x100000, help="Assumed constant-byte span end")
    parser.add_argument("--assumed-byte", type=lambda x: int(x, 0), default=0xFF, help="Assumed plaintext byte (e.g. 0xFF or 0x00)")
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args()

    rep = run_probe(
        args.osiris_file,
        span_start=args.span_start,
        span_end=args.span_end,
        assumed_byte=args.assumed_byte,
    )
    if args.json:
        print(json.dumps(rep, indent=2))
        return

    print(f"File: {rep['file']} | ROMData SHA-256: {str(rep['romdata_sha256'])[:16]}...")
    print(f"Post-section tail: {rep['post_sections_tail_len']}B | hex={rep['post_sections_tail_hex']}")
    if rep["mdc_section"]:
        print(f"#mdc: {rep['mdc_section']}")
    print(f"Lattice deviations sampled: {len(rep['lattice_deviations_sample'])}")
    for d in rep["lattice_deviations_sample"][:5]:
        print(
            f"  pair={d['pair_index']} (r={d['residue_k_mod_64']}, off=0x{d['romdata_offset']:06X}): "
            f"xor={d['pair_xor_be']} vs modal={d['expected_residue_xor_be']}"
        )
    print("Top periodic key candidates:")
    for c in rep["periodic_key_candidates"][:5]:
        print(
            f"  p={c['period_bytes']}B support={c['support_ratio']:.4f} "
            f"vectors=(SP:{c['sh705x_sp_plausible']},PC:{c['sh705x_pc_plausible']}) "
            f"ff={c['unmasked_ff_ratio']:.3f} zero={c['unmasked_zero_ratio']:.3f} head={c['sample_head_hex']}"
        )


if __name__ == "__main__":
    main()