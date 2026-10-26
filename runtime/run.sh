#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
binary="$root/target/release/cordial-shell"
[[ -x "$binary" ]] || { echo 'No compiled LilacRuntime found. Run bash runtime/build.sh first.' >&2; exit 2; }
# Redirect all three: upstream migrates data between cache and data on startup.
# This isolates files, not desktop keyring entries or network identity.
state_root="${LILAC_RUNTIME_STATE:-$HOME/.local/share/lilac-runtime-dev}"
mkdir -p "$state_root/data" "$state_root/cache" "$state_root/config"
export XDG_DATA_HOME="$state_root/data" XDG_CACHE_HOME="$state_root/cache" XDG_CONFIG_HOME="$state_root/config"
exec "$binary" "$@"
