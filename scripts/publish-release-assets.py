#!/usr/bin/env python3
"""Publish only missing theme assets; never replace or delete published bytes."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


ASSET_NAMES = ("dist-release.zip", "SHA256SUMS", "dist-release.zip.sha256")


class PublicationError(RuntimeError):
    pass


class GitHub:
    def release(self, repository, tag):
        result = subprocess.run(
            ["gh", "api", f"repos/{repository}/releases/tags/{tag}"],
            check=True, capture_output=True,
        )
        return json.loads(result.stdout)

    def download(self, repository, asset_id):
        return subprocess.run(
            ["gh", "api", "-H", "Accept: application/octet-stream",
             f"repos/{repository}/releases/assets/{asset_id}"],
            check=True, capture_output=True,
        ).stdout

    def upload(self, repository, tag, paths):
        # GitHub rejects a duplicate name. Never add a replacement/delete fallback,
        # including when another publisher wins a race after our preflight.
        subprocess.run(
            ["gh", "release", "upload", tag, *map(str, paths), "--repo", repository],
            check=True,
        )


def local_assets(directory):
    paths = {name: directory / name for name in ASSET_NAMES}
    payloads = {name: path.read_bytes() for name, path in paths.items()}
    digest = hashlib.sha256(payloads["dist-release.zip"]).hexdigest()
    if payloads["dist-release.zip.sha256"].decode("ascii").strip() != digest:
        raise PublicationError("local ZIP sidecar checksum mismatch")
    sums = payloads["SHA256SUMS"].decode("ascii").strip()
    if sums != f"{digest}  dist-release.zip":
        raise PublicationError("local SHA256SUMS does not describe the ZIP")
    return paths, payloads


def release_assets(github, repository, tag):
    release = github.release(repository, tag)
    if (
        not isinstance(release, dict)
        or release.get("tag_name") != tag
        or release.get("draft") is not False
        or release.get("prerelease") is not False
    ):
        raise PublicationError("expected an existing published stable release")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise PublicationError("release asset listing is missing or malformed")
    selected = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise PublicationError("malformed published asset")
        name = asset.get("name")
        if name not in ASSET_NAMES:
            continue
        asset_id = asset.get("id")
        if (
            name in selected or type(asset_id) is not int
            or asset_id <= 0 or asset.get("state") != "uploaded"
        ):
            raise PublicationError(f"ambiguous or incomplete published asset: {name}")
        selected[name] = asset_id
    return selected


def compare_existing(github, repository, remote, payloads):
    for name, asset_id in remote.items():
        if github.download(repository, asset_id) != payloads[name]:
            raise PublicationError(
                f"immutable release asset mismatch: {name}; publish a new version"
            )


def publish(repository, tag, directory, *, github=None, check_only=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repository):
        raise PublicationError("invalid repository")
    if not re.fullmatch(r"v\d+\.\d+\.\d+-stable\.\d+", tag):
        raise PublicationError("expected a versioned stable tag")
    github = github or GitHub()
    paths, payloads = local_assets(directory)
    remote = release_assets(github, repository, tag)
    # Check every existing asset before any upload. A missing checksum file must
    # never be generated from a different rebuilt ZIP.
    compare_existing(github, repository, remote, payloads)
    missing = [paths[name] for name in ASSET_NAMES if name not in remote]
    if check_only:
        return [path.name for path in missing]
    if missing:
        github.upload(repository, tag, missing)
    published = release_assets(github, repository, tag)
    if set(published) != set(ASSET_NAMES):
        raise PublicationError("published release is missing required theme assets")
    compare_existing(github, repository, published, payloads)
    return [path.name for path in missing]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository")
    parser.add_argument("tag")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--check-only", action="store_true", help="read-only preflight; never upload")
    args = parser.parse_args()
    try:
        missing = publish(args.repository, args.tag, args.directory, check_only=args.check_only)
    except (PublicationError, OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as error:
        # CalledProcessError does not expose subprocess output or credentials.
        parser.exit(1, f"FAIL: {error}\n")
    action = "would upload" if args.check_only else "uploaded"
    print(f"OK: {action} {', '.join(missing) if missing else 'nothing (identical assets)'}")


if __name__ == "__main__":
    main()
