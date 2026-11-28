from pathlib import Path
from osiris_rom_inspector import extract_romdata_slice, is_osiris_rom


def load_rom_for_scanner(path: Path, unmask_fn=None) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    if not is_osiris_rom(raw):
        return raw, {"container_type": "flat_bin", "source": path.name, "unmasked": True}

    info, payload = extract_romdata_slice(raw, source_name=path.name)
    meta = {
        "container_type": "osiris_rom",
        "source": path.name,
        "version_banner": info.version_banner,
        "romdata_offset": info.romdata_offset,
        "romdata_size": info.romdata_size,
        "unmasked": False,
    }

    if unmask_fn is None:
        raise ValueError(
            f"{path.name}: UpRev ROMData is still obfuscated/encrypted; "
            "provide a verified unmask_fn before running flat calibration scanners."
        )

    flat_rom = unmask_fn(payload, info)
    meta["unmasked"] = True
    return flat_rom, meta