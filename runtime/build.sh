#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_dir="${LILAC_RUNTIME_SOURCE:-$root/source}"
for tool in cargo clang cmake pkg-config; do
  command -v "$tool" >/dev/null || { echo "Missing build tool: $tool. See runtime/README.md." >&2; exit 2; }
done
pkg-config --atleast-version=4.12 gtk4 || { echo 'GTK4 development files >=4.12 required.' >&2; exit 2; }
pkg-config --atleast-version=1.5 libadwaita-1 || { echo 'libadwaita development files >=1.5 required.' >&2; exit 2; }
pkg-config --exists libpipewire-0.3 webkitgtk-6.0 || { echo 'PipeWire and WebKitGTK 6.0 development files are required for this build.' >&2; exit 2; }
[[ -d "$source_dir/.git" ]] || { echo 'Run bash runtime/prepare.sh first.' >&2; exit 2; }
[[ $(git -C "$source_dir" rev-parse HEAD) == cf8aa92fe0055e652ff0aa8dc01d146979d20d6b ]] || { echo 'Wrong upstream revision.' >&2; exit 2; }
git -C "$source_dir" apply --reverse --check "$root/patches/0001-lilac-development-identity.patch" || { echo 'Lilac patch is not fully applied.' >&2; exit 2; }
export CC=clang CXX=clang++
# Keep this fork's output separate from other Cordial builds.
export CARGO_TARGET_DIR="$root/target"
cd "$source_dir"
cargo test --workspace --locked
cargo build --release --locked --features cordial-shell/webview
printf 'Built development binaries in %s/release. Run bash runtime/run.sh from LilacLauncher.\n' "$CARGO_TARGET_DIR"
