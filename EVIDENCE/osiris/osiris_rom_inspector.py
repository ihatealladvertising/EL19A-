#!/usr/bin/env python3
"""
UpRev OsirisROM Container Parser & Payload Structural Profiler (`osiris_rom_inspector.py`)

Designed as a drop-in companion module for `tools/sh705x_rom_loader.py` and the SH705x
workbench suite. Strictly isolates container framing (`UpRev Osiris ROM File Ver ...`,
`ROMData`, trailer TLV sections) from flat ROM calibration scanners, and provides
deterministic payload diagnostics (entropy, adjacent u32_be XOR periodicity, `k % 64`
8-byte pair lattice profiling, and donor `.bin` differential checks).
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


OSIRIS_MAGIC_PREFIX = b"UpRev Osiris ROM File Ver "
DEFAULT_SECTION_TABLE_OFFSET = 0x60
EXPECTED_ROMDATA_BYTES = 0x100000  # 1,048,576 bytes


@dataclass(frozen=True)
class OsirisSection:
    """Single TLV-like tagged block inside an UpRev `.OsirisROM` container."""
    tag: str
    offset: int
    tag_bytes: int
    payload_len: int
    total_record_len: int
    flags: int
    data_offset: int
    data_sha256: str


@dataclass
class OsirisContainerInfo:
    """Parsed structural view of an UpRev `.OsirisROM` container."""
    source_name: str
    file_size: int
    file_sha256: str
    version_banner: str
    header_prefix_hex: str
    sections: List[OsirisSection] = field(default_factory=list)
    romdata_offset: Optional[int] = None
    romdata_size: Optional[int] = None
    romdata_sha256: Optional[str] = None
    is_encrypted_or_obfuscated: bool = True
    trailing_unparsed_bytes: int = 0


@dataclass
class BlockProfile:
    """64 KB payload slice diagnostics."""
    offset: int
    size: int
    shannon_entropy: float
    unique_u32_be: int
    unique_adj_xor: int


@dataclass
class PairLatticeProfile:
    """Diagnostics for 8-byte (even/odd u32_be) pair XOR periodicity in 0x0C0000..0x100000."""
    region_offset: int
    region_size: int
    total_pairs: int
    unique_pair_xors: int
    modulus_pairs: int
    pure_residue_classes: int
    deviating_pairs: int
    deviating_residues: List[int]
    top_pair_xors: List[Tuple[str, int]]


@dataclass
class OsirisPayloadProfile:
    """Full structural & statistical profile of an extracted `ROMData` payload."""
    romdata_size: int
    romdata_sha256: str
    overall_entropy: float
    block_profiles: List[BlockProfile]
    upper_quarter_lattice: Optional[PairLatticeProfile] = None


def _shannon_entropy(buf: bytes) -> float:
    if not buf:
        return 0.0
    freq = [0] * 256
    for b in buf:
        freq[b] += 1
    n = len(buf)
    return -sum((c / n) * math.log2(c / n) for c in freq if c)


def is_osiris_rom(raw: bytes) -> bool:
    """Return True if buffer starts with the UpRev Osiris container banner."""
    return raw.startswith(OSIRIS_MAGIC_PREFIX)


def parse_osiris_container(raw: bytes, source_name: str = "<memory>") -> OsirisContainerInfo:
    """
    Parse UpRev `.OsirisROM` header, `ROMData` slice bounds, and trailer tag sections.

    Raises ValueError if the buffer is not a valid UpRev Osiris container.
    """
    if not is_osiris_rom(raw):
        raise ValueError(f"{source_name}: missing UpRev Osiris magic header")

    ver_line = raw[:48].split(b"\r\n", 1)[0].split(b"\x1a", 1)[0]
    version_banner = ver_line.decode("ascii", errors="replace").strip()

    sections: List[OsirisSection] = []
    pos = DEFAULT_SECTION_TABLE_OFFSET
    romdata_offset: Optional[int] = None
    romdata_size: Optional[int] = None
    romdata_sha256: Optional[str] = None

    while pos + 20 <= len(raw):
        if raw[pos : pos + 10] == b"AITuneDesc":
            tag_raw = raw[pos : pos + 10]
            tlen = 10
        elif all(32 <= b < 127 for b in raw[pos : pos + 8]):
            tag_raw = raw[pos : pos + 8]
            tlen = 8
        else:
            break

        if pos + tlen + 12 > len(raw):
            break

        payload_len, total_rec_len, flags = struct.unpack_from("<III", raw, pos + tlen)
        data_offset = pos + tlen + 12
        end_offset = pos + total_rec_len

        if total_rec_len < tlen + 12 or end_offset > len(raw) or data_offset + payload_len > end_offset:
            break

        tag_name = tag_raw.decode("ascii").strip()
        sec_bytes = raw[data_offset : data_offset + payload_len]
        sec_hash = hashlib.sha256(sec_bytes).hexdigest()

        sections.append(
            OsirisSection(
                tag=tag_name,
                offset=pos,
                tag_bytes=tlen,
                payload_len=payload_len,
                total_record_len=total_rec_len,
                flags=flags,
                data_offset=data_offset,
                data_sha256=sec_hash,
            )
        )

        if tag_name == "ROMData":
            romdata_offset = data_offset
            romdata_size = payload_len
            romdata_sha256 = sec_hash

        pos = end_offset

    if not sections:
        raise ValueError(f"{source_name}: UpRev header matched, but no valid section records found at 0x{DEFAULT_SECTION_TABLE_OFFSET:X}")

    return OsirisContainerInfo(
        source_name=source_name,
        file_size=len(raw),
        file_sha256=hashlib.sha256(raw).hexdigest(),
        version_banner=version_banner,
        header_prefix_hex=raw[0x40:0x60].hex(),
        sections=sections,
        romdata_offset=romdata_offset,
        romdata_size=romdata_size,
        romdata_sha256=romdata_sha256,
        is_encrypted_or_obfuscated=True,
        trailing_unparsed_bytes=max(0, len(raw) - pos),
    )


def extract_romdata_slice(raw: bytes, source_name: str = "<memory>") -> Tuple[OsirisContainerInfo, bytes]:
    """
    Validate container framing and return `(container_info, raw_romdata_bytes)`.

    NOTE: The returned `raw_romdata_bytes` buffer is still obfuscated/encrypted and must NOT
    be passed directly into flat SH705x table/axis scanners without verified decryption.
    """
    info = parse_osiris_container(raw, source_name=source_name)
    if info.romdata_offset is None or info.romdata_size is None:
        raise ValueError(f"{source_name}: container lacks a valid ROMData section")
    payload = raw[info.romdata_offset : info.romdata_offset + info.romdata_size]
    return info, payload


def profile_romdata_payload(payload: bytes, block_size: int = 0x10000) -> OsirisPayloadProfile:
    """
    Compute structural diagnostics across the extracted `ROMData` payload, including
    64 KB entropy / adjacent-word XOR metrics and the `k % 64` 8-byte pair lattice check
    in `0x0C0000..0x100000`.
    """
    blocks: List[BlockProfile] = []
    for off in range(0, len(payload), block_size):
        chunk = payload[off : off + block_size]
        n_words = len(chunk) // 4
        if n_words >= 2:
            words = struct.unpack(f">{n_words}I", chunk[: n_words * 4])
            adj_xor = [words[i] ^ words[i + 1] for i in range(n_words - 1)]
            uniq_w = len(set(words))
            uniq_ax = len(set(adj_xor))
        else:
            uniq_w = 0
            uniq_ax = 0

        blocks.append(
            BlockProfile(
                offset=off,
                size=len(chunk),
                shannon_entropy=round(_shannon_entropy(chunk), 6),
                unique_u32_be=uniq_w,
                unique_adj_xor=uniq_ax,
            )
        )

    lattice: Optional[PairLatticeProfile] = None
    if len(payload) >= 0x100000:
        region_off = 0x0C0000
        region = payload[region_off:0x100000]
        w_reg = struct.unpack(f">{len(region) // 4}I", region)
        pair_xor = [w_reg[2 * k] ^ w_reg[2 * k + 1] for k in range(len(w_reg) // 2)]

        mod = 64  # 64 pairs = 512 bytes
        buckets: Dict[int, Counter] = defaultdict(Counter)
        for k, val in enumerate(pair_xor):
            buckets[k % mod][val] += 1

        pure_classes = sum(1 for r in range(mod) if len(buckets[r]) == 1)
        deviating_residues = sorted(r for r in range(mod) if len(buckets[r]) > 1)
        deviating_pairs = sum(
            1
            for k, val in enumerate(pair_xor)
            if val != buckets[k % mod].most_common(1)[0][0]
        )
        top_xors = [(f"0x{val:08X}", cnt) for val, cnt in Counter(pair_xor).most_common(8)]

        lattice = PairLatticeProfile(
            region_offset=region_off,
            region_size=len(region),
            total_pairs=len(pair_xor),
            unique_pair_xors=len(set(pair_xor)),
            modulus_pairs=mod,
            pure_residue_classes=pure_classes,
            deviating_pairs=deviating_pairs,
            deviating_residues=deviating_residues,
            top_pair_xors=top_xors,
        )

    return OsirisPayloadProfile(
        romdata_size=len(payload),
        romdata_sha256=hashlib.sha256(payload).hexdigest(),
        overall_entropy=round(_shannon_entropy(payload), 6),
        block_profiles=blocks,
        upper_quarter_lattice=lattice,
    )


def compare_against_donor(payload: bytes, donor_rom: bytes, block_size: int = 0x10000) -> Dict[str, object]:
    """
    Compare an extracted `ROMData` slice against a candidate flat stock donor ROM.
    Useful for testing candidate unmasking transforms or verifying non-identity.
    """
    cmp_len = min(len(payload), len(donor_rom))
    block_diffs = []
    for off in range(0, cmp_len, block_size):
        end = min(off + block_size, cmp_len)
        diffs = sum(1 for a, b in zip(payload[off:end], donor_rom[off:end]) if a != b)
        block_diffs.append({"offset": f"0x{off:06X}", "size": end - off, "byte_diffs": diffs})

    total_diffs = sum(b["byte_diffs"] for b in block_diffs)
    return {
        "payload_size": len(payload),
        "donor_size": len(donor_rom),
        "compared_bytes": cmp_len,
        "exact_match": (len(payload) == len(donor_rom) and total_diffs == 0),
        "total_byte_diffs": total_diffs,
        "mismatch_ratio": round(total_diffs / cmp_len, 6) if cmp_len else 1.0,
        "block_diffs": block_diffs,
    }


def inspect_osiris_file(path: Path, donor_path: Optional[Path] = None) -> Dict[str, object]:
    """High-level entry point returning a JSON-serializable inspection report."""
    raw = path.read_bytes()
    info, payload = extract_romdata_slice(raw, source_name=path.name)
    prof = profile_romdata_payload(payload)
    report: Dict[str, object] = {
        "container": asdict(info),
        "payload_profile": asdict(prof),
    }
    if donor_path is not None:
        report["donor_comparison"] = compare_against_donor(payload, donor_path.read_bytes())
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect UpRev .OsirisROM container and profile ROMData payload.")
    parser.add_argument("osiris_file", type=Path, help="Path to .OsirisROM file")
    parser.add_argument("--donor", type=Path, default=None, help="Optional flat donor .bin file to diff against")
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args()

    rep = inspect_osiris_file(args.osiris_file, donor_path=args.donor)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        c = rep["container"]
        p = rep["payload_profile"]
        print(f"File: {c['source_name']} ({c['file_size']} bytes) | Banner: {c['version_banner']}")
        print(f"ROMData: offset=0x{c['romdata_offset']:X}, size=0x{c['romdata_size']:X}, sha256={c['romdata_sha256'][:16]}...")
        print("Sections:", ", ".join(f"{s['tag']}({s['payload_len']}B @ 0x{s['offset']:X})" for s in c["sections"]))
        print(f"Overall entropy: {p['overall_entropy']} bits/byte | Unparsed trailing bytes: {c['trailing_unparsed_bytes']}")
        lat = p.get("upper_quarter_lattice")
        if lat:
            print(
                f"Upper-quarter pair lattice (0x{lat['region_offset']:06X}..0x100000): "
                f"{lat['pure_residue_classes']}/{lat['modulus_pairs']} pure (k % 64) classes, "
                f"{lat['deviating_pairs']}/{lat['total_pairs']} deviating pairs (residues={lat['deviating_residues']})"
            )
        if "donor_comparison" in rep:
            dc = rep["donor_comparison"]
            print(
                f"Donor diff ({args.donor.name}): {dc['total_byte_diffs']}/{dc['compared_bytes']} bytes differ "
                f"({dc['mismatch_ratio']*100:.2f}%)"
            )
