#!/usr/bin/env python3
"""
UpRev OsirisROM Container Parser & Payload Structural Profiler (`osiris_rom_inspector.py`)

Designed as a drop-in companion module for `tools/sh705x_rom_loader.py` and the SH705x
workbench suite. Strictly isolates container framing (`UpRev Osiris ROM File Ver ...`,
`ROMData`, trailer TLV sections) from flat ROM calibration scanners, and provides
deterministic payload diagnostics (entropy, adjacent u32_be XOR periodicity, `k % 64`
8-byte pair lattice profiling, repeating XOR period scans, donor `.bin` offset alignment,
and Osiris-vs-Osiris diffs).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


OSIRIS_MAGIC_PREFIX = b"UpRev Osiris ROM File Ver "
DEFAULT_SECTION_TABLE_OFFSET = 0x60
EXPECTED_ROMDATA_BYTES = 0x100000  # 1,048,576 bytes
KNOWN_MULTI_BYTE_TAGS = (b"AITuneDesc",)
KNOWN_SHORT_TAGS = (b"#mdc",)
DEFAULT_XOR_PERIODS = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)


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
    trailing_preview_hex: str = ""


@dataclass
class BlockProfile:
    """64 KB payload slice diagnostics."""
    offset: int
    size: int
    shannon_entropy: float
    null_bytes: int
    ff_bytes: int
    unique_u32_be: int
    unique_adj_xor: int
    period64_match_ratio: float


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
class PeriodScanEntry:
    """XOR periodicity diagnostic for a candidate period `p` (in bytes)."""
    period_bytes: int
    identical_ratio: float
    top_nonzero_xor_delta: str
    top_delta_ratio: float


@dataclass
class OsirisPayloadProfile:
    """Full structural & statistical profile of an extracted `ROMData` payload."""
    romdata_size: int
    romdata_sha256: str
    overall_entropy: float
    total_null_bytes: int
    total_ff_bytes: int
    block_profiles: List[BlockProfile]
    upper_quarter_lattice: Optional[PairLatticeProfile] = None
    xor_period_scan: List[PeriodScanEntry] = field(default_factory=list)


def _shannon_entropy(buf: bytes) -> float:
    if not buf:
        return 0.0
    freq = [0] * 256
    for b in buf:
        freq[b] += 1
    n = len(buf)
    return -sum((c / n) * math.log2(c / n) for c in freq if c)


def _period64_match_ratio(chunk: bytes) -> float:
    """
    Fraction of bytes after index 512 that match the byte 512 bytes earlier.
    Helps detect 64-pair (512-byte) repeating structure or masking patterns.
    """
    period = 512
    if len(chunk) <= period:
        return 0.0
    matches = sum(1 for i in range(period, len(chunk)) if chunk[i] == chunk[i - period])
    return round(matches / (len(chunk) - period), 6)


def _match_tag_at(raw: bytes, pos: int) -> Optional[Tuple[bytes, int]]:
    """Identify a plausible ASCII section tag at `pos` and return `(tag_bytes_raw, tag_len)`."""
    for known in KNOWN_MULTI_BYTE_TAGS:
        n = len(known)
        if pos + n <= len(raw) and raw[pos : pos + n] == known:
            return raw[pos : pos + n], n

    for short_tag in KNOWN_SHORT_TAGS:
        n = len(short_tag)
        if pos + n <= len(raw) and raw[pos : pos + n] == short_tag:
            return raw[pos : pos + n], n

    if pos + 8 <= len(raw) and all(32 <= b < 127 for b in raw[pos : pos + 8]):
        return raw[pos : pos + 8], 8

    return None


def find_repeating_xor_periods(
    payload: bytes,
    periods: Iterable[int] = DEFAULT_XOR_PERIODS,
    sample_stride: int = 1,
) -> List[PeriodScanEntry]:
    """
    Evaluate `payload[i] ^ payload[i + period]` across candidate byte periods.

    - High `identical_ratio` indicates a period where bytes repeat cleanly (e.g. a static
      mask or periodic block structure).
    - High `top_delta_ratio` with a non-zero delta indicates a constant step/drift across
      that period.
    """
    stride = max(1, sample_stride)
    n = len(payload)
    entries: List[PeriodScanEntry] = []

    for p in periods:
        if p <= 0 or p + stride > n:
            continue
        diffs: Counter[int] = Counter()
        total = 0
        for i in range(0, n - p, stride):
            total += 1
            d = payload[i] ^ payload[i + p]
            if d:
                diffs[d] += 1

        if total == 0:
            continue
        nonzero_total = sum(diffs.values())
        zero_ratio = (total - nonzero_total) / total
        if diffs:
            top_delta, top_cnt = diffs.most_common(1)[0]
            top_hex = f"0x{top_delta:02X}"
            top_ratio = top_cnt / total
        else:
            top_hex = "0x00"
            top_ratio = 0.0

        entries.append(
            PeriodScanEntry(
                period_bytes=p,
                identical_ratio=round(zero_ratio, 6),
                top_nonzero_xor_delta=top_hex,
                top_delta_ratio=round(top_ratio, 6),
            )
        )

    return entries


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

    while pos + 16 <= len(raw):
        matched = _match_tag_at(raw, pos)
        if matched is None:
            break

        tag_raw, tlen = matched
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
        raise ValueError(
            f"{source_name}: UpRev header matched, but no valid section records found at 0x{DEFAULT_SECTION_TABLE_OFFSET:X}"
        )

    trailing_len = max(0, len(raw) - pos)
    trailing_slice = raw[pos : min(len(raw), pos + 64)]

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
        trailing_unparsed_bytes=trailing_len,
        trailing_preview_hex=trailing_slice.hex(),
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


def profile_romdata_payload(
    payload: bytes,
    block_size: int = 0x10000,
    xor_periods: Iterable[int] = DEFAULT_XOR_PERIODS,
    period_stride: int = 1,
) -> OsirisPayloadProfile:
    """
    Compute structural diagnostics across the extracted `ROMData` payload, including
    64 KB entropy / byte-class / adjacent-word XOR / 512-byte periodicity metrics,
    repeating XOR period scans, and the `k % 64` 8-byte pair lattice check in `0x0C0000..0x100000`.
    """
    blocks: List[BlockProfile] = []
    total_nulls = 0
    total_ffs = 0

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

        nulls = chunk.count(0x00)
        ffs = chunk.count(0xFF)
        total_nulls += nulls
        total_ffs += ffs

        blocks.append(
            BlockProfile(
                offset=off,
                size=len(chunk),
                shannon_entropy=round(_shannon_entropy(chunk), 6),
                null_bytes=nulls,
                ff_bytes=ffs,
                unique_u32_be=uniq_w,
                unique_adj_xor=uniq_ax,
                period64_match_ratio=_period64_match_ratio(chunk),
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

    period_scan = find_repeating_xor_periods(
        payload,
        periods=xor_periods,
        sample_stride=period_stride,
    )

    return OsirisPayloadProfile(
        romdata_size=len(payload),
        romdata_sha256=hashlib.sha256(payload).hexdigest(),
        overall_entropy=round(_shannon_entropy(payload), 6),
        total_null_bytes=total_nulls,
        total_ff_bytes=total_ffs,
        block_profiles=blocks,
        upper_quarter_lattice=lattice,
        xor_period_scan=period_scan,
    )


def _summarize_diff_spans(a: bytes, b: bytes, max_spans: int = 25) -> Dict[str, object]:
    """Summarize contiguous byte-difference ranges between two equal-prefix slices."""
    n = min(len(a), len(b))
    spans: List[Dict[str, object]] = []
    start: Optional[int] = None
    count = 0

    for idx in range(n):
        if a[idx] != b[idx]:
            if start is None:
                start = idx
            count += 1
        elif start is not None:
            spans.append(
                {
                    "start": f"0x{start:06X}",
                    "end_exclusive": f"0x{idx:06X}",
                    "diff_bytes": count,
                }
            )
            start = None
            count = 0

    if start is not None:
        spans.append(
            {
                "start": f"0x{start:06X}",
                "end_exclusive": f"0x{n:06X}",
                "diff_bytes": count,
            }
        )

    return {
        "total_diff_spans": len(spans),
        "truncated_spans": len(spans) > max_spans,
        "spans": spans[:max_spans],
    }


def _find_best_donor_alignment(
    payload: bytes,
    donor_rom: bytes,
    candidate_offsets: Optional[Iterable[int]] = None,
    sample_stride: int = 16,
) -> Dict[str, object]:
    """
    Check exact offset-0 alignment and test candidate byte offsets between `payload`
    and `donor_rom` to detect shifted framing or partial slice alignment.

    Positive `donor_offset` means `payload[0..]` is compared against `donor_rom[donor_offset..]`.
    Negative `donor_offset` means `payload[-donor_offset..]` is compared against `donor_rom[0..]`.
    """
    if not payload or not donor_rom:
        return {"exact_offset_zero_match": False, "best_candidate": None, "candidates": []}

    exact_zero = len(payload) == len(donor_rom) and payload == donor_rom

    if candidate_offsets is None:
        # Default sweep: common small/block shifts around 0 plus container-header offsets
        offsets = [
            -0x100, -0x80, -0x60, -0x40, -0x20, -0x10, -0x08, -0x04,
            0x00,
            0x04, 0x08, 0x10, 0x20, 0x40, 0x60, 0x80, 0x100,
            0x010000, 0x020000, 0x040000, 0x080000, 0x0C0000,
        ]
    else:
        offsets = list(candidate_offsets)

    stride = max(1, sample_stride)
    scored: List[Dict[str, object]] = []

    for off in offsets:
        if off >= 0:
            p_start = 0
            d_start = off
        else:
            p_start = -off
            d_start = 0

        overlap = min(len(payload) - p_start, len(donor_rom) - d_start)
        if overlap < 64:
            continue

        sampled = 0
        matches = 0
        for i in range(0, overlap, stride):
            sampled += 1
            if payload[p_start + i] == donor_rom[d_start + i]:
                matches += 1

        ratio = matches / sampled if sampled else 0.0
        scored.append(
            {
                "donor_offset": f"0x{off:X}" if off >= 0 else f"-0x{abs(off):X}",
                "donor_offset_int": off,
                "overlap_bytes": overlap,
                "sampled_bytes": sampled,
                "sampled_match_ratio": round(ratio, 6),
            }
        )

    scored.sort(key=lambda item: (-float(item["sampled_match_ratio"]), abs(int(item["donor_offset_int"]))))
    return {
        "exact_offset_zero_match": exact_zero,
        "sample_stride": stride,
        "best_candidate": scored[0] if scored else None,
        "candidates": scored[:10],
    }


def compare_against_donor(
    payload: bytes,
    donor_rom: bytes,
    block_size: int = 0x10000,
    alignment_offsets: Optional[Iterable[int]] = None,
) -> Dict[str, object]:
    """
    Compare an extracted `ROMData` slice against a candidate flat stock donor ROM.
    Useful for testing candidate unmasking transforms, checking offset alignment,
    or verifying non-identity.
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
        "diff_span_summary": _summarize_diff_spans(payload, donor_rom),
        "alignment_check": _find_best_donor_alignment(
            payload,
            donor_rom,
            candidate_offsets=alignment_offsets,
        ),
    }


def compare_osiris_containers(
    info_a: OsirisContainerInfo,
    payload_a: bytes,
    info_b: OsirisContainerInfo,
    payload_b: bytes,
    block_size: int = 0x10000,
) -> Dict[str, object]:
    """Compare container metadata, section hashes, and `ROMData` payloads between two `.OsirisROM` files."""
    sec_map_a = {s.tag: s for s in info_a.sections}
    sec_map_b = {s.tag: s for s in info_b.sections}
    all_tags = list(dict.fromkeys([*(s.tag for s in info_a.sections), *(s.tag for s in info_b.sections)]))

    section_diffs = []
    for tag in all_tags:
        sa = sec_map_a.get(tag)
        sb = sec_map_b.get(tag)
        section_diffs.append(
            {
                "tag": tag,
                "in_a": sa is not None,
                "in_b": sb is not None,
                "len_a": sa.payload_len if sa else None,
                "len_b": sb.payload_len if sb else None,
                "sha256_equal": (sa is not None and sb is not None and sa.data_sha256 == sb.data_sha256),
            }
        )

    romdata_diff = compare_against_donor(payload_a, payload_b, block_size=block_size)
    return {
        "file_a": info_a.source_name,
        "file_b": info_b.source_name,
        "version_banner_equal": info_a.version_banner == info_b.version_banner,
        "section_diffs": section_diffs,
        "romdata_comparison": romdata_diff,
    }


def _parse_hex_or_int_list(raw_values: Optional[List[str]]) -> Optional[List[int]]:
    if not raw_values:
        return None
    parsed: List[int] = []
    for item in raw_values:
        for tok in item.split(","):
            tok = tok.strip()
            if tok:
                parsed.append(int(tok, 0))
    return parsed


def inspect_osiris_file(
    path: Path,
    donor_path: Optional[Path] = None,
    compare_path: Optional[Path] = None,
    dump_romdata_path: Optional[Path] = None,
    xor_periods: Iterable[int] = DEFAULT_XOR_PERIODS,
    period_stride: int = 1,
    alignment_offsets: Optional[Iterable[int]] = None,
) -> Dict[str, object]:
    """High-level entry point returning a JSON-serializable inspection report."""
    raw = path.read_bytes()
    info, payload = extract_romdata_slice(raw, source_name=path.name)
    prof = profile_romdata_payload(
        payload,
        xor_periods=xor_periods,
        period_stride=period_stride,
    )

    if dump_romdata_path is not None:
        dump_romdata_path.parent.mkdir(parents=True, exist_ok=True)
        dump_romdata_path.write_bytes(payload)

    report: Dict[str, object] = {
        "container": asdict(info),
        "payload_profile": asdict(prof),
    }
    if donor_path is not None:
        report["donor_comparison"] = compare_against_donor(
            payload,
            donor_path.read_bytes(),
            alignment_offsets=alignment_offsets,
        )
    if compare_path is not None:
        raw_b = compare_path.read_bytes()
        info_b, payload_b = extract_romdata_slice(raw_b, source_name=compare_path.name)
        report["osiris_comparison"] = compare_osiris_containers(info, payload, info_b, payload_b)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect UpRev .OsirisROM container and profile ROMData payload.")
    parser.add_argument("osiris_file", type=Path, help="Path to .OsirisROM file")
    parser.add_argument("--donor", type=Path, default=None, help="Optional flat donor .bin file to diff against")
    parser.add_argument("--compare", type=Path, default=None, help="Optional second .OsirisROM file to compare against")
    parser.add_argument(
        "--dump-romdata",
        type=Path,
        default=None,
        help="Optional output path for raw (still obfuscated/encrypted) ROMData bytes",
    )
    parser.add_argument(
        "--periods",
        nargs="*",
        default=None,
        help="Optional comma/space-separated XOR byte periods (e.g. 1,2,4,8,64,512)",
    )
    parser.add_argument(
        "--period-stride",
        type=int,
        default=1,
        help="Sample stride for XOR period scan (default: 1; use >1 for faster coarse scans)",
    )
    parser.add_argument(
        "--align-offsets",
        nargs="*",
        default=None,
        help="Optional comma/space-separated donor byte offsets to check (supports 0x hex or signed ints)",
    )
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args()

    periods = _parse_hex_or_int_list(args.periods) or list(DEFAULT_XOR_PERIODS)
    align_offsets = _parse_hex_or_int_list(args.align_offsets)

    rep = inspect_osiris_file(
        args.osiris_file,
        donor_path=args.donor,
        compare_path=args.compare,
        dump_romdata_path=args.dump_romdata,
        xor_periods=periods,
        period_stride=args.period_stride,
        alignment_offsets=align_offsets,
    )
    if args.json:
        print(json.dumps(rep, indent=2))
        return

    c = rep["container"]
    p = rep["payload_profile"]
    print(f"File: {c['source_name']} ({c['file_size']} bytes) | Banner: {c['version_banner']}")
    print(f"ROMData: offset=0x{c['romdata_offset']:X}, size=0x{c['romdata_size']:X}, sha256={c['romdata_sha256'][:16]}...")
    print("Sections:", ", ".join(f"{s['tag']}({s['payload_len']}B @ 0x{s['offset']:X})" for s in c["sections"]))
    print(
        f"Overall entropy: {p['overall_entropy']} bits/byte | nulls={p['total_null_bytes']} | 0xFF={p['total_ff_bytes']} | "
        f"Unparsed trailing bytes: {c['trailing_unparsed_bytes']}"
    )
    lat = p.get("upper_quarter_lattice")
    if lat:
        print(
            f"Upper-quarter pair lattice (0x{lat['region_offset']:06X}..0x100000): "
            f"{lat['pure_residue_classes']}/{lat['modulus_pairs']} pure (k % 64) classes, "
            f"{lat['deviating_pairs']}/{lat['total_pairs']} deviating pairs (residues={lat['deviating_residues']})"
        )
    if p.get("xor_period_scan"):
        top_periods = ", ".join(
            f"p={e['period_bytes']}B(eq={e['identical_ratio']:.3f},topΔ={e['top_nonzero_xor_delta']}:{e['top_delta_ratio']:.3f})"
            for e in p["xor_period_scan"]
        )
        print(f"XOR period scan: {top_periods}")
    if "donor_comparison" in rep:
        dc = rep["donor_comparison"]
        print(
            f"Donor diff ({args.donor.name}): {dc['total_byte_diffs']}/{dc['compared_bytes']} bytes differ "
            f"({dc['mismatch_ratio']*100:.2f}%), spans={dc['diff_span_summary']['total_diff_spans']}"
        )
        best = dc.get("alignment_check", {}).get("best_candidate")
        if best:
            print(
                f"  Best donor offset: {best['donor_offset']} (match_ratio={best['sampled_match_ratio']:.4f} "
                f"over {best['overlap_bytes']}B)"
            )
    if "osiris_comparison" in rep:
        oc = rep["osiris_comparison"]
        rd = oc["romdata_comparison"]
        print(
            f"Osiris diff vs {args.compare.name}: ROMData {rd['total_byte_diffs']}/{rd['compared_bytes']} bytes differ "
            f"({rd['mismatch_ratio']*100:.2f}%), spans={rd['diff_span_summary']['total_diff_spans']}"
        )
        for sd in oc["section_diffs"]:
            print(f"  Section {sd['tag']}: in_a={sd['in_a']} in_b={sd['in_b']} len=({sd['len_a']},{sd['len_b']}) sha_eq={sd['sha256_equal']}")


if __name__ == "__main__":
    main()