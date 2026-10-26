#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_dir="${LILAC_RUNTIME_SOURCE:-$root/source}"
revision=cf8aa92fe0055e652ff0aa8dc01d146979d20d6b
if [[ ! -e "$source_dir" ]]; then
  git clone --no-checkout https://github.com/luohoa97/cordial.git "$source_dir"
  git -C "$source_dir" checkout --detach "$revision"
fi
[[ -d "$source_dir/.git" ]] || { echo 'Source path must be a Git checkout.' >&2; exit 1; }
[[ $(git -C "$source_dir" rev-parse HEAD) == "$revision" ]] || { echo 'Checkout is not at the pinned revision; no files changed.' >&2; exit 1; }
for patch in "$root"/patches/*.patch; do
  if git -C "$source_dir" apply --reverse --check "$patch" 2>/dev/null; then
    printf 'Already applied: %s\n' "$(basename -- "$patch")"
  elif git -C "$source_dir" apply --check "$patch" 2>/dev/null; then
    # Git preserves edits outside these hunks and refuses conflicting hunks.
    git -C "$source_dir" apply "$patch"
    printf 'Applied: %s\n' "$(basename -- "$patch")"
  else
    printf 'Patch conflicts with checkout: %s. Resolve it before continuing.\n' "$(basename -- "$patch")" >&2
    exit 1
  fi
done
git -C "$source_dir" submodule update --init --recursive
printf 'Prepared LilacRuntime source at %s\n' "$source_dir"
echo 'No compiled runtime has been produced. Next run: bash runtime/build.sh'
