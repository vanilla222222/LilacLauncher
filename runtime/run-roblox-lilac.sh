#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
overlay="$root/roblox-lilac/generated/overlay"
if ! python3 - "$root/roblox-lilac/generated/manifest.json" "$overlay" "$root/roblox-lilac/generate.py" <<'PY_CHECK'
import hashlib,json,sys,os
from pathlib import Path
try:
 root=Path(sys.argv[2]);manifest=json.loads(Path(sys.argv[1]).read_text())
 if manifest.get('generator_sha256')!=hashlib.sha256(Path(sys.argv[3]).read_bytes()).hexdigest():sys.exit(1)
 if manifest.get('version')!=2:sys.exit(1)
 apk=Path(manifest['source_apk'])
 if os.environ.get('LILAC_THEME_APK') and apk.resolve()!=Path(os.environ['LILAC_THEME_APK']).expanduser().resolve():sys.exit(1)
 stat=apk.stat()
 if stat.st_size!=manifest['source_apk_bytes'] or stat.st_mtime_ns!=manifest['source_apk_mtime_ns']:sys.exit(1)
 for item in manifest['textures']:
  p=root/item['path']
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:sys.exit(1)
except (OSError,ValueError,KeyError):sys.exit(1)
PY_CHECK
then
  python3 "$root/roblox-lilac/generate.py"
fi
echo '[lilac-assets] Texture pack v2 enabled; original accents and locally tinted UI atlases.'
export CORDIAL_OVERLAY="$overlay"
exec bash "$root/run.sh" "$@"
