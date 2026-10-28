"""Fetch the MATPOWER case files this study uses, and check them against pinned SHA-256 hashes.
They are not committed: MATPOWER's LICENSE says its case files are not covered by its BSD licence.
(The folder is casefiles/, not data/, because the workbench ignores every data/ folder.)
Hashes pinned 28 Oct 2026 from MATPOWER master; if MATPOWER changes a file, this script refuses it."""
import hashlib
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "https://raw.githubusercontent.com/MATPOWER/matpower/master/data/"
PIN = {"case9.m": "ee50fc7bf9f6019c0f3a3bc94d20978cc667b08f695dc725d00dbd998b358623",
       "case14.m": "2ffc4e1b734ae6c5e92dbe68b4e36010ed695a4bbcc4d065c74c4fbc39fcf3c1"}
ok = True
for name, h in PIN.items():
    p = HERE / name
    if not p.exists():
        p.write_bytes(urllib.request.urlopen(BASE + name, timeout=60).read())
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    print(name, "OK" if got == h else f"HASH MISMATCH {got}")
    ok &= got == h
sys.exit(0 if ok else 1)
