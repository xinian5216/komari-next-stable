"""Fetch the user's actual plugin UI, pinned to the published ZIP checksum."""

import hashlib
import io
import os
from pathlib import Path
import urllib.request
import zipfile


URL = "https://github.com/Akizon77/komari-passkey/releases/download/v0.1.13/komari-passkey-0.1.13.zip"
SHA256 = "eee8f160caa2cd6b0d32e90ef2c0c3204c4db274fe26b121fa90f86ffccd6fd9"
DESTINATION = Path(__file__).resolve().parents[2] / "tests" / ".fixtures" / "passkey-0.1.13"


def main():
    local = os.environ.get("KOMARI_PASSKEY_ZIP")
    if local:
        payload = Path(local).read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=60) as response:
            payload = response.read(8 * 1024 * 1024 + 1)
    if hashlib.sha256(payload).hexdigest() != SHA256:
        raise SystemExit("FAIL: Passkey fixture ZIP checksum mismatch")
    DESTINATION.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for name in ("passkey-ui.js", "passkey-ui.css"):
            # Read only fixed archive entries; never extract arbitrary paths.
            (DESTINATION / name).write_bytes(archive.read("assets/" + name))
    print("OK: verified Akizon77/komari-passkey v0.1.13 UI fixture")


if __name__ == "__main__":
    main()
