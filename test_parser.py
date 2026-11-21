import re
import sys
import hashlib

ROM_PATH = "/home/vivian/.gemini/antigravity/scratch/EL19A-/EVIDENCE/VERSA f501.bin"
LST_PATH = "/tmp/EL19A_NEXT6_16.lst"

with open(ROM_PATH, "rb") as f:
    rom = f.read()

print(f"ROM loaded: {len(rom)} bytes")

# Let's inspect how lines look
with open(LST_PATH, "r", encoding="utf-8", errors="replace") as f:
    for i in range(100):
        line = f.readline()
        if not line:
            break
        if "CODE" in line:
            print(line.rstrip())
            break
