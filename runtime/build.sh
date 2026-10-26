#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_dir="${LILAC_RUNTIME_SOURCE:-$root/source}"
# Prefer rustup's current stable over distribution Cargo, which can be too old
# for the pinned version-4 lockfile. No toolchain is installed automatically.
if command -v rustup >/dev/null; then
  cargo_cmd=(rustup run "${LILAC_RUST_TOOLCHAIN:-stable}" cargo)
else
  cargo_cmd=(cargo)
fi
if ! cargo_version=$("${cargo_cmd[@]}" --version 2>/dev/null); then
  echo 'Rust/Cargo unavailable. Install rustup from https://rustup.rs, then run: rustup update stable' >&2
  exit 2
fi
if [[ "$cargo_version" =~ ^cargo[[:space:]]+([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
  major=${BASH_REMATCH[1]}; minor=${BASH_REMATCH[2]}
  if (( major < 1 || (major == 1 && minor < 78) )); then
    echo "$cargo_version cannot read the pinned version-4 lockfile; Cargo >=1.78 is required." >&2
    echo 'Install rustup from https://rustup.rs if needed, then run: rustup update stable' >&2
    echo 'Keep Cargo.lock unchanged and rerun this script.' >&2
    exit 2
  fi
else
  echo "Could not recognise Cargo version: $cargo_version" >&2
  exit 2
fi
printf 'Using %s\n' "$cargo_version"
for tool in clang cmake pkg-config python3; do
  command -v "$tool" >/dev/null || { echo "Missing build tool: $tool. See runtime/README.md." >&2; exit 2; }
done
pkg-config --atleast-version=4.12 gtk4 || { echo 'GTK4 development files >=4.12 required.' >&2; exit 2; }
pkg-config --atleast-version=1.5 libadwaita-1 || { echo 'libadwaita development files >=1.5 required.' >&2; exit 2; }
pkg-config --exists libpipewire-0.3 webkitgtk-6.0 || { echo 'PipeWire and WebKitGTK 6.0 development files are required for this build.' >&2; exit 2; }
[[ -d "$source_dir/.git" ]] || { echo 'Run bash runtime/prepare.sh first.' >&2; exit 2; }
[[ $(git -C "$source_dir" rev-parse HEAD) == cf8aa92fe0055e652ff0aa8dc01d146979d20d6b ]] || { echo 'Wrong upstream revision.' >&2; exit 2; }
python3 "$root/patch-stack.py" check "$source_dir"
export CC=clang CXX=clang++
# Keep this fork's output separate from other Cordial builds.
export CARGO_TARGET_DIR="$root/target"
cd "$source_dir"
"${cargo_cmd[@]}" test --workspace --locked
"${cargo_cmd[@]}" build --release --locked --features cordial-shell/webview
printf 'Built development binaries in %s/release. Run bash runtime/run.sh from LilacLauncher.\n' "$CARGO_TARGET_DIR"
