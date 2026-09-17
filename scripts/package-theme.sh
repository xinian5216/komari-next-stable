#!/usr/bin/env bash
# Package the built theme into the exact layout the Komari server expects:
#   <zip root>/komari-theme.json
#   <zip root>/preview.png
#   <zip root>/dist/**
#
# Run `npm ci && npm run build` first. Produces dist-release.zip (default) and
# validates it with scripts/validate-theme-package.py before returning success.
#
# Usage: bash scripts/package-theme.sh [output.zip]
set -euo pipefail

cd "$(dirname "$0")/.."

OUT="${1:-dist-release.zip}"

# 选一个真正可用的 Python（Windows 上 `python3` 可能是 Microsoft Store 的占位存根，
# 非交互执行时静默退出 49；CI/Linux 上通常就是 python3）。
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import zipfile' >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "FAIL: python3 (or python) with the zipfile module is required" >&2
  exit 1
fi

for required in komari-theme.json preview.png dist/index.html; do
  if [ ! -f "$required" ]; then
    echo "FAIL: $required is missing (run 'npm ci && npm run build' first)" >&2
    exit 1
  fi
done

rm -f "$OUT"

# Assemble deterministically: sorted relative paths, no extra directory wrapper.
"$PY" - "$OUT" <<'PY'
import os
import sys
import zipfile

out = sys.argv[1]
entries = ["komari-theme.json", "preview.png"]
for root, dirs, files in os.walk("dist"):
    dirs.sort()
    for name in sorted(files):
        entries.append(os.path.join(root, name).replace("\\", "/"))

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in entries:
        archive.write(path, path)

print(f"packaged {len(entries)} entries into {out}")
PY

"$PY" scripts/validate-theme-package.py "$OUT" --expected-short next --print-sha256
