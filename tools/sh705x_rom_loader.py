#!/usr/bin/env python3
"""
Shared Read-Only SH705x ROM Container Loader & Nissan Metadata Parser (`tools/sh705x_rom_loader.py`)

Supports `.bin`, `.zip`, `.s19`, Intel `.hex`, and Nissan Consult `.dat`
(`0x8015` Feistel ECB and `%6` 32-byte blocks), with explicit rejection diagnostics
for UpRev Osiris, WinOLS, TCM `0x8019`, KWP2000 `0xB8 0x15 0xF1`, and media files.
"""
import re
import struct
import zipfile
from pathlib import Path
from typing import List, Tuple


def load_s19_bytes(raw: bytes) -> bytes:
    max_addr = 0x100000
    recs = []
    for line in raw.decode("ascii", errors="ignore").splitlines():
        if len(line) >= 4 and line[0] == "S" and line[1] in ("1", "2", "3"):
            alen = {"1": 4, "2": 6, "3": 8}[line[1]]
            cnt = int(line[2:4], 16)
            addr = int(line[4 : 4 + alen], 16)
            data = bytes.fromhex(line[4 + alen : 2 + cnt * 2])
            if addr + len(data) <= 0x200000:
                max_addr = max(max_addr, addr + len(data))
                recs.append((addr, data))
    buf = bytearray([0xFF] * max_addr)
    for addr, data in recs:
        buf[addr : addr + len(data)] = data
    return bytes(buf)


def load_hex_bytes(raw: bytes) -> bytes:
    buf = bytearray([0xFF] * 0x100000)
    upper = 0
    for line in raw.decode("ascii", errors="ignore").splitlines():
        if not line.startswith(":"):
            continue
        cnt = int(line[1:3], 16)
        addr = int(line[3:7], 16)
        rt = int(line[7:9], 16)
        data = bytes.fromhex(line[9 : 9 + 2 * cnt])
        if rt == 0:
            full = upper + addr
            if full + len(data) <= len(buf):
                buf[full : full + len(data)] = data
        elif rt == 4:
            upper = int.from_bytes(data, "big") << 16
        elif rt == 2:
            upper = int.from_bytes(data, "big") << 4
    return bytes(buf)


def _rol16(v: int, k: int) -> int:
    return ((v << k) | (v >> (16 - k))) & 0xFFFF


def decrypt_consult_dat_word(c: int) -> int:
    """Invert Nissan Consult .dat 2-round 16-bit Feistel ECB cipher on one 32-bit BE word."""
    ch, cl = (c >> 16) & 0xFFFF, c & 0xFFFF
    a = (cl + 0xCA1B) & 0xFFFF
    z = (a + _rol16(a, 1) + 0xFFFF) & 0xFFFF
    r0 = ch ^ (z ^ _rol16(z, 4))
    b = (r0 + 0x124D) & 0xFFFF
    f1 = (b + _rol16(b, 2) + 0xFFFF) & 0xFFFF
    l0 = cl ^ f1
    return (l0 << 16) | r0


def _check_nonflat_container(raw: bytes, label: str = "") -> None:
    """Reject known non-flat/encrypted/non-ROM containers with actionable diagnostics."""
    who = f" ({label})" if label else ""
    if raw.startswith(b"UpRev Osiris ROM File Ver "):
        ver = raw[:32].decode("ascii", errors="replace").strip()
        sections = []
        pos = 0x60
        while pos + 20 < len(raw):
            if raw[pos : pos + 10] == b"AITuneDesc":
                tag, tlen = "AITuneDesc", 10
            elif all(32 <= b < 127 for b in raw[pos : pos + 8]):
                tag, tlen = raw[pos : pos + 8].decode("ascii").strip(), 8
            else:
                break
            u0, u1, _u2 = struct.unpack_from("<III", raw, pos + tlen)
            if u1 < tlen + 16 or pos + u1 > len(raw):
                break
            sections.append(f"{tag}({u0}B)")
            pos += u1
        sec_str = ", ".join(sections) if sections else "unknown layout"
        raise ValueError(
            f"UpRev Osiris encrypted container{who}: {ver}; sections=[{sec_str}]. "
            "ROMData is encrypted and cannot be scanned directly without decryption."
        )
    if raw.startswith(b"WinOLS File") or raw[4:15] == b"WinOLS File":
        raise ValueError(
            f"WinOLS project container{who} ('WinOLS File', {len(raw):,} B) is not a flat ECU binary; "
            "export a flat .bin/.hex/.s19 image first."
        )
    if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
        w, h = struct.unpack_from(">II", raw, 16)
        raise ValueError(f"File{who} is a PNG image ({w}x{h}, {len(raw):,} B), not an ECU ROM.")
    if raw.startswith(b"%PDF-"):
        raise ValueError(f"File{who} is a PDF document ({len(raw):,} B), not an ECU ROM.")
    if raw.startswith(b"\xff\xd8\xff"):
        raise ValueError(f"File{who} is a JPEG image ({len(raw):,} B), not an ECU ROM.")


def _load_dat_percent6(raw: bytes, pos: int) -> bytes:
    """Unpack & decrypt Nissan `%6` (0x25 0x36) 32-byte-block Consult .dat (e.g. E1BR20E.dat)."""
    sbl_blocks = 0
    rom_recs: List[Tuple[int, bytes]] = []
    max_end = 0x80000
    while pos + 7 <= len(raw) and raw[pos : pos + 2] == b"%6":
        idx = int.from_bytes(raw[pos + 2 : pos + 5], "big")
        plen = raw[pos + 5]
        frame_len = 6 + plen + 1
        if plen == 0 or pos + frame_len > len(raw):
            raise ValueError(f"Truncated Consult .dat %6 frame at 0x{pos:X}")
        blk = raw[pos : pos + frame_len]
        if (sum(blk[:-1]) & 0xFF) != blk[-1]:
            raise ValueError(f"Consult .dat %6 frame checksum mismatch at 0x{pos:X}")
        if 0x800000 <= idx < 0x820000:
            sbl_blocks += 1
        elif 0x820000 <= idx:
            if plen % 4 != 0:
                raise ValueError(f"Unaligned %6 payload length {plen} at 0x{pos:X}")
            enc = blk[6 : 6 + plen]
            dec = bytearray(plen)
            for off in range(0, plen, 4):
                w = struct.unpack_from(">I", enc, off)[0]
                struct.pack_into(">I", dec, off, decrypt_consult_dat_word(w))
            rom_off = (idx - 0x820000) * 32
            rom_recs.append((rom_off, bytes(dec)))
            if rom_off + plen > max_end:
                max_end = 0x100000 if rom_off + plen <= 0x100000 else rom_off + plen
        pos += frame_len
    if not rom_recs:
        raise ValueError(f"No ROM blocks (0x820000+) found in %6 Consult .dat (sbl_blocks={sbl_blocks})")
    buf = bytearray([0xFF] * max_end)
    for off, dec in rom_recs:
        buf[off : off + len(dec)] = dec
    return bytes(buf)


def load_dat_bytes(raw: bytes) -> bytes:
    """Unpack and decrypt a Nissan Consult .dat reprogramming container into a raw SH705x image."""
    pos_ecu = raw.find(b"\x80\x15\xfc", 0, 0x200)
    if pos_ecu != -1:
        pos = pos_ecu
        recs: List[Tuple[int, bytes]] = []
        max_end = 0x80000
        n_frames = 0
        while pos + 11 <= len(raw) and raw[pos : pos + 2] == b"\x80\x15":
            kwp_len = raw[pos + 3]
            frame_len = 4 + kwp_len + 1
            if pos + frame_len > len(raw):
                raise ValueError(f"Truncated Consult .dat frame at 0x{pos:X}")
            blk = raw[pos : pos + frame_len]
            if (sum(blk[:-1]) & 0xFF) != blk[-1]:
                raise ValueError(f"Consult .dat frame checksum mismatch at 0x{pos:X}")
            if blk[4:6] != b"\x34\x82":
                raise ValueError(f"Unexpected Consult .dat frame command {blk[4:6].hex()} at 0x{pos:X}")
            addr = int.from_bytes(blk[6:9], "big")
            plen = blk[9]
            if plen % 4 != 0 or 10 + plen > frame_len - 1:
                raise ValueError(f"Invalid Consult .dat payload length {plen} at 0x{pos:X}")
            enc = blk[10 : 10 + plen]
            dec = bytearray(plen)
            for off in range(0, plen, 4):
                w = struct.unpack_from(">I", enc, off)[0]
                struct.pack_into(">I", dec, off, decrypt_consult_dat_word(w))
            recs.append((addr, bytes(dec)))
            if addr + plen > max_end:
                max_end = 0x100000 if addr + plen <= 0x100000 else addr + plen
            pos += frame_len
            n_frames += 1
        if n_frames > 0:
            buf = bytearray([0xFF] * max_end)
            for addr, dec in recs:
                buf[addr : addr + len(dec)] = dec
            return bytes(buf)

    pos_p6 = raw.find(b"%6", 0, 0x200)
    if pos_p6 != -1:
        return _load_dat_percent6(raw, pos_p6)

    pos_tcm = raw.find(b"\x80\x19\xfc", 0, 0x200)
    if pos_tcm != -1:
        pos = pos_tcm
        n_tcm = 0
        min_a, max_a = 1 << 30, 0
        while pos + 11 <= len(raw) and raw[pos : pos + 2] == b"\x80\x19":
            fl = 4 + raw[pos + 3] + 1
            if pos + fl > len(raw):
                break
            blk = raw[pos : pos + fl]
            if (sum(blk[:-1]) & 0xFF) != blk[-1]:
                raise ValueError(f"TCM Consult .dat frame checksum mismatch at 0x{pos:X}")
            addr = int.from_bytes(blk[6:9], "big")
            min_a = min(min_a, addr)
            max_a = max(max_a, addr + blk[9])
            pos += fl
            n_tcm += 1
        hdr_ascii = "".join(chr(b) if 32 <= b < 127 else "" for b in raw[:0x25])
        raise ValueError(
            f"Nissan/Hitachi TCM Consult .dat (KWP target 0x19, header='{hdr_ascii}', "
            f"{n_tcm} checksum-verified frames 0x{min_a:X}..0x{max_a:X}) uses a distinct TCM cipher "
            "and is not an SH705x ECU binary."
        )

    pos_kwp = raw.find(b"\xb8\x15\xf1", 0, 0x200)
    if pos_kwp != -1:
        pos = pos_kwp
        n_kwp = 0
        min_a, max_a = 1 << 30, 0
        while pos + 4 <= len(raw) and raw[pos + 1 : pos + 3] == b"\x15\xf1":
            dlen = raw[pos] & 0x3F
            fl = 3 + dlen + 1
            if pos + fl > len(raw):
                break
            blk = raw[pos : pos + fl]
            if (sum(blk[:-1]) & 0xFF) != blk[-1]:
                raise ValueError(f"KWP2000 .dat checksum mismatch at 0x{pos:X}")
            addr = int.from_bytes(blk[5:8], "big")
            min_a = min(min_a, addr)
            max_a = max(max_a, addr + max(0, dlen - 5))
            pos += fl
            n_kwp += 1
        hdr_ascii = "".join(chr(b) if 32 <= b < 127 else "" for b in raw[:0x25])
        raise ValueError(
            f"Unencrypted KWP2000 partial calibration .dat (header='{hdr_ascii}', "
            f"{n_kwp} verified frames covering 0x{min_a:X}..0x{max_a:X}) is not a full SH705x ECU image."
        )

    raise ValueError("Unrecognized Consult .dat container format")


def load_any_rom(path: Path) -> bytes:
    suf = path.suffix.lower()
    if suf == ".zip":
        with zipfile.ZipFile(path) as zf:
            members = [m for m in zf.infolist() if not m.is_dir()]
            if not members:
                raise ValueError(f"Empty zip archive: {path}")
            pref = [m for m in members if m.filename.lower().endswith((".bin", ".s19", ".hex", ".dat"))]
            target = max(pref or members, key=lambda m: m.file_size)
            raw = zf.read(target.filename)
            _check_nonflat_container(raw, target.filename)
            inner_suf = Path(target.filename).suffix.lower()
            if inner_suf == ".s19":
                return load_s19_bytes(raw)
            if inner_suf == ".hex":
                return load_hex_bytes(raw)
            if inner_suf == ".dat":
                return load_dat_bytes(raw)
            return raw
    raw = path.read_bytes()
    _check_nonflat_container(raw, path.name)
    if suf == ".s19":
        return load_s19_bytes(raw)
    if suf == ".hex":
        return load_hex_bytes(raw)
    if suf == ".dat":
        return load_dat_bytes(raw)
    return raw


def parse_nissan_metadata(rom: bytes) -> dict:
    """
    Parse nissutils-style BootLoader (`LOADERxx`), Application FID (`ROMID ... DATABASE ... SH705xxx`),
    RAMF vector table count, and SH-2 IVT handler diversity.
    """
    dbs = []
    for m in re.finditer(rb"([0-9A-Z]{6,12})\x00{2,16}DATABASE\x00+(?:[A-Z0-9]\x00+)?(SH70[0-9A-Z]{2,6})", rom):
        tag, cpu = m.group(1).decode("ascii"), m.group(2).decode("ascii")
        dbs.append({"addr": m.start(), "tag": tag, "cpu": cpu, "is_loader": tag.startswith("LOADER")})

    loaders = [d for d in dbs if d["is_loader"]]
    fids = [d for d in dbs if not d["is_loader"]]
    app_fid = fids[-1] if fids else None

    ramf_count = 0
    if app_fid is not None and app_fid["addr"] + 0x94 <= len(rom):
        fa = app_fid["addr"]
        ramf_count = sum(
            1
            for off in range(fa + 0x3C, fa + 0x94, 4)
            if 0xFFFF0000 <= struct.unpack_from(">I", rom, off)[0] <= 0xFFFFFFFF
        )

    bootblock_ff = len(rom) >= 0x8200 and rom[:0x8200] == b"\xff" * 0x8200
    ivt_unique = 0
    if not bootblock_ff and len(rom) >= 0x400:
        vecs = struct.unpack_from(">256I", rom, 0)
        reset_pc = vecs[0]
        ivt_unique = len({v for v in vecs[2:] if v not in (0, 0xFFFFFFFF, reset_pc) and v < len(rom)})

    return {
        "loader": loaders[0]["tag"] if loaders else None,
        "loader_addr": loaders[0]["addr"] if loaders else None,
        "fid": app_fid["tag"] if app_fid else None,
        "fid_addr": app_fid["addr"] if app_fid else None,
        "fid_cpu": app_fid["cpu"] if app_fid else None,
        "ramf_ptrs": ramf_count,
        "bootblock_ff": bootblock_ff,
        "ivt_unique": ivt_unique,
    }
