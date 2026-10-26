#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
binary="$root/target/release/cordial-shell"
[[ -x "$binary" ]] || { echo 'No compiled LilacRuntime found. Run bash runtime/build.sh first.' >&2; exit 2; }
if [[ ! -f "$root/target/.lilac-build-patches" ]] ||
   ! (cd "$root" && sha256sum --check --status target/.lilac-build-patches); then
  echo 'The compiled runtime does not match the current patches. Run bash runtime/build.sh successfully before launching.' >&2
  exit 2
fi
# Redirect all three: upstream migrates data between cache and data on startup.
# This isolates files, not desktop keyring entries or network identity.
state_root="${LILAC_RUNTIME_STATE:-$HOME/.local/share/lilac-runtime-dev}"
mkdir -p "$state_root/data" "$state_root/cache" "$state_root/config"
export XDG_DATA_HOME="$state_root/data" XDG_CACHE_HOME="$state_root/cache" XDG_CONFIG_HOME="$state_root/config"
if [[ "${LILAC_HOME_THEME:-on}" != off ]]; then
  # Generated outside the APK and outside the user's own overlay. Patch 0009
  # adds this as a lower-priority layer, so explicit user overlays still win.
  export LILAC_HOME_OVERLAY="$state_root/config/cordial/lilac-home-overlay"
  python3 "$root/lilac_home_theme.py" \
    --data-home "$XDG_DATA_HOME" \
    --config-home "$XDG_CONFIG_HOME" \
    --apk "${CORDIAL_APK:-}"
else
  unset LILAC_HOME_OVERLAY
fi
exec "$binary" "$@"
