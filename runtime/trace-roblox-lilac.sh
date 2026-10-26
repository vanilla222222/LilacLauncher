#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
mkdir -p "$root/roblox-lilac/generated"
trace_dir=$(mktemp -d "$root/roblox-lilac/generated/trace.XXXXXXXX")
log="$trace_dir/runtime-private.log"
echo 'Open Roblox, join a game, open Escape and the emote menu if available, then close the game AND runtime.'
echo 'Capturing asset activity. Only share the summary printed after the runtime closes.'
set +e
# Both switches are upstream fixed-arity tracing controls. Do not use the
# broader CORDIAL_TRACE switch, whose variadic wrappers are ABI-unsafe.
CORDIAL_TRACE_ASSETS=1 CORDIAL_TRACE_PATHS=1 bash "$root/run-roblox-lilac.sh" >"$log" 2>&1
status=$?
set -e
python3 "$root/roblox-lilac/summarize-trace.py" "$log" "$status" > "$trace_dir/summary.txt"
cat "$trace_dir/summary.txt"
printf '\nPrivate log directory (keep the full log private): %s\n' "$trace_dir"
exit "$status"
