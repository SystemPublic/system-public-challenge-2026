"""Download publisher-original Graph CSVs and verify the packaged SHA-256 manifest."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "system-public-graph-v1-associations.csv": 14061020,
    "system-public-graph-v1-concepts.csv": 14061021,
    "system-public-graph-v1-studies.csv": 14061022,
    "system-public-graph-v1-variables.csv": 14061023,
}


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def main():
    manifest = json.loads((ROOT / "data/raw/system/MANIFEST.json").read_text())
    entries = {entry["filename"]: entry for entry in manifest["files"]}
    target = ROOT / "data/restored/system"
    target.mkdir(parents=True, exist_ok=True)
    for filename, file_id in FILES.items():
        expected = entries[filename]
        destination = target / filename
        if destination.exists() and digest(destination) == expected["checksums"]["sha256"]:
            print("Already verified", filename)
            continue
        temporary = destination.with_suffix(".csv.part")
        url = f"https://dataverse.harvard.edu/api/access/datafile/{file_id}?format=original"
        print("Downloading", filename, flush=True)
        try:
            with urlopen(url, timeout=120) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            if temporary.stat().st_size != expected["bytes"] or digest(temporary) != expected["checksums"]["sha256"]:
                raise ValueError(f"Publisher checksum mismatch for {filename}")
            temporary.replace(destination)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        print("Verified", filename)


if __name__ == "__main__":
    main()
