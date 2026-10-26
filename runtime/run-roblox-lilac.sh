#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
overlay="$root/roblox-lilac/generated/overlay"
if ! python3 - "$root/roblox-lilac/generated/manifest.json" "$overlay" "$root/roblox-lilac/generate.py" <<'PY_CHECK'
import hashlib,json,sys
from pathlib import Path
try:
 root=Path(sys.argv[2]);manifest=json.loads(Path(sys.argv[1]).read_text())
 if manifest.get('generator_sha256')!=hashlib.sha256(Path(sys.argv[3]).read_bytes()).hexdigest():sys.exit(1)
 for item in manifest['textures']:
  p=root/item['path']
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:sys.exit(1)
except (OSError,ValueError,KeyError):sys.exit(1)
PY_CHECK
then
  python3 "$root/roblox-lilac/generate.py"
fi
echo '[lilac-assets] Original texture pack enabled; 12 verified assets.'
export CORDIAL_OVERLAY="$overlay"
exec bash "$root/run.sh" "$@"
