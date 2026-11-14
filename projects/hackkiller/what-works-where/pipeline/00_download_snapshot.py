"""Download the fixed System Public Graph association snapshot from Harvard Dataverse (v2.1, ~422 MiB).

The file is too large for the repository (25 MB limit), so it is fetched on demand and checked
against the SHA-256 recorded when this project was built.
"""
from __future__ import annotations

import hashlib
import sys

import requests

from common import RAW_CSV

URL = "https://dataverse.harvard.edu/api/access/datafile/14061020?format=original"
SHA256 = "a9c8ba3db760efec0d08c65c17c36f0066073062d8e1ff8ea40cc71679daddf9"
SIZE = 442_463_948


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    if RAW_CSV.exists() and RAW_CSV.stat().st_size == SIZE and sha256(RAW_CSV) == SHA256:
        print("snapshot already present and verified:", RAW_CSV)
        return
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    print("downloading", URL)
    with requests.get(URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(RAW_CSV, "wb") as fh:
            for block in r.iter_content(1 << 20):
                fh.write(block)
    digest = sha256(RAW_CSV)
    if digest != SHA256:
        sys.exit(f"checksum mismatch: got {digest}, expected {SHA256}")
    print("ok:", RAW_CSV, RAW_CSV.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
