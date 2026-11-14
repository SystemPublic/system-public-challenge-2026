"""Losslessly restore original System CSVs; no data transformation."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/system"
TARGET = ROOT / "data/restored/system"

def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    entries = json.loads((SOURCE / "MANIFEST.json").read_text())["files"]
    for entry in entries:
        name = entry["filename"]
        archive = SOURCE / (name + ".gz")
        parts = sorted(SOURCE.glob(name + ".gz.part*"))
        if not archive.exists() and not parts:
            continue
        with tempfile.TemporaryFile() as joined:
            if parts:
                for part in parts:
                    with part.open("rb") as source:
                        shutil.copyfileobj(source, joined)
                joined.seek(0)
                compressed = gzip.GzipFile(fileobj=joined)
            else:
                compressed = gzip.open(archive, "rb")
            destination = TARGET / name
            with compressed, destination.open("wb") as output:
                shutil.copyfileobj(compressed, output)
        digest = hashlib.sha256()
        with destination.open("rb") as restored:
            for block in iter(lambda: restored.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != entry["checksums"]["sha256"]:
            raise ValueError(f"Checksum mismatch: {name}")
        print(f"Verified {name}")

if __name__ == "__main__":
    main()
