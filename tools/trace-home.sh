#!/usr/bin/env bash
# Inspect an unmodified client under an existing Cordial AppImage.
set -euo pipefail
if [[ $# -ne 1 || ! -f "$1" || ! -x "$1" ]]; then
  echo 'Usage: bash tools/trace-home.sh /absolute/path/to/Cordial-x86_64.AppImage' >&2
  echo 'The AppImage must exist and have execute permission.' >&2
  exit 2
fi
runtime=$(realpath -- "$1")
if [[ -z ${DISPLAY:-} && -z ${WAYLAND_DISPLAY:-} ]]; then
  echo 'No desktop display found. Run this in a terminal on your Linux desktop.' >&2
  exit 2
fi
command -v python3 >/dev/null || { echo 'python3 is required.' >&2; exit 2; }
umask 077
trace_dir=$(mktemp -d "${TMPDIR:-/tmp}/lilac-home-trace.XXXXXXXX")
log="$trace_dir/runtime-private.log"
echo 'Open Roblox Home in Cordial, visit Discover/Search, return Home, then close Cordial.'
echo 'The private log stays on this machine. Only share the summary printed below.'
set +e
# Avoid verbose bridge/text tracing: those switches may include credentials.
env -u CORDIAL_TRACE -u CORDIAL_TRACE_BRIDGE -u CORDIAL_TRACE_TEXT_SHOW_PASSWORDS CORDIAL_TRACE_ASSETS=1 "$runtime" >"$log" 2>&1
runtime_status=$?
set -e
python3 - "$log" "$runtime_status" <<'PY'
import sys,re
from pathlib import Path
counts={'Asset trace lines':0,'UniversalApp asset trace lines':0,'Home ready notifications':0,'WebView openWindow log lines':0}
with open(sys.argv[1],errors='replace') as f:
 for line in f:
  if '[asset]' in line:
   counts['Asset trace lines']+=1
   if 'models/UniversalApp/UniversalApp.rbxm' in line:counts['UniversalApp asset trace lines']+=1
  if re.search(r'APP_READY[^\r\n]{0,100}\bHome\b',line):counts['Home ready notifications']+=1
  if '[webview]' in line and 'openWindow' in line:counts['WebView openWindow log lines']+=1
summary='Lilac Home trace summary\nCordial exit code: '+sys.argv[2]+'\n'+'\n'.join(f'{k}: {v}' for k,v in counts.items())+'\n'
summary+='These counts do not prove the Home screen is a WebView or that its scripts can be edited.\n'
Path(sys.argv[1]).with_name('summary.txt').write_text(summary)
print(summary,end='')
PY
printf '\nPrivate log and shareable summary directory: %s\n' "$trace_dir"
if [[ "$runtime_status" -ne 0 ]]; then
  echo 'Cordial exited unsuccessfully; a zero count may mean startup failed, not that a feature is absent.' >&2
fi
exit "$runtime_status"
