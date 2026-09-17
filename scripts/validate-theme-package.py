#!/usr/bin/env python3
"""Validate a Komari theme package (zip) against the layout the Komari server expects.

Mirrors the server-side rules in web/api/admin/theme.go:
  - komari-theme.json at the archive root; name (string or localized object) and
    short are required, short must match ^[A-Za-z0-9_-]+$ and must not be "default"
  - dist/index.html must exist
  - no symlinks, no absolute paths, no ".." traversal entries
  - limits: <= 10000 files, <= 128 MiB per file, <= 512 MiB uncompressed total,
    <= 1 MiB manifest

Usage:
    python3 scripts/validate-theme-package.py <zip> [--expected-short next] [--print-sha256]
"""

import argparse
import hashlib
import json
import re
import sys
import zipfile

MAX_FILES = 10000
MAX_FILE_SIZE = 128 << 20          # 128 MiB per entry
MAX_EXTRACTED_SIZE = 512 << 20     # 512 MiB uncompressed total
MAX_MANIFEST_SIZE = 1 << 20        # 1 MiB manifest
SHORT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def is_localized_text(value) -> bool:
    """Accept a plain string or a {lang: string} map, like the server does."""
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(isinstance(v, str) and v.strip() for v in value.values())
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path")
    parser.add_argument("--expected-short", default="next")
    parser.add_argument("--print-sha256", action="store_true")
    args = parser.parse_args()

    with zipfile.ZipFile(args.zip_path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]

        # 1) size and count limits
        if len(infos) > MAX_FILES:
            fail(f"archive has {len(infos)} entries, more than the {MAX_FILES} the server accepts")
        total = 0
        for info in infos:
            if info.is_dir():
                continue
            if info.file_size > MAX_FILE_SIZE:
                fail(f"{info.filename} is larger than the {MAX_FILE_SIZE} byte per-file limit")
            total += info.file_size
        if total > MAX_EXTRACTED_SIZE:
            fail(f"uncompressed total {total} exceeds the {MAX_EXTRACTED_SIZE} byte limit")

        # 2) symlinks, absolute paths, traversal
        for info in infos:
            mode = (info.external_attr >> 16) & 0xFFFF
            if mode and (mode & 0xA000) == 0xA000:
                fail(f"symlink entry is not allowed: {info.filename}")
            name = info.filename
            if name.startswith("/") or name.startswith("\\"):
                fail(f"absolute path entry is not allowed: {name}")
            if ".." in name.split("/"):
                fail(f"path traversal entry is not allowed: {name}")

        # 3) root layout
        for required in ("komari-theme.json", "preview.png"):
            if required not in names:
                fail(f"missing {required} at the package root")
        if not any(name.startswith("dist/") for name in names):
            fail("missing dist/ directory")
        if "dist/index.html" not in names:
            fail("missing dist/index.html")

        # 4) manifest
        raw = archive.read("komari-theme.json")
        if len(raw) > MAX_MANIFEST_SIZE:
            fail(f"komari-theme.json exceeds the {MAX_MANIFEST_SIZE} byte limit")
        try:
            manifest = json.loads(raw)
        except Exception as exc:  # noqa: BLE001 - report the parse error verbatim
            fail(f"komari-theme.json is not valid JSON: {exc}")

        if not is_localized_text(manifest.get("name")):
            fail("manifest: name is missing or empty")
        short = manifest.get("short")
        if not isinstance(short, str) or not short:
            fail("manifest: short is missing")
        if not SHORT_PATTERN.fullmatch(short):
            fail(f"manifest: short {short!r} contains characters outside [A-Za-z0-9_-]")
        if short == "default":
            fail('manifest: short must not be "default"')
        if args.expected_short and short != args.expected_short:
            fail(f"manifest: short is {short!r}, expected {args.expected_short!r}")
        for field in ("version", "author", "url"):
            value = manifest.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"manifest: {field} is missing or empty")
        configuration = manifest.get("configuration")
        if configuration is not None and not isinstance(configuration, dict):
            fail("manifest: configuration must be an object")

    print(f"OK: {args.zip_path}")
    print(
        f"  files={len(infos)} uncompressed={total / 1048576:.2f} MiB "
        f"short={short} version={manifest.get('version')}"
    )
    if args.print_sha256:
        digest = hashlib.sha256(open(args.zip_path, "rb").read()).hexdigest()
        print(f"  sha256={digest}")


if __name__ == "__main__":
    main()
