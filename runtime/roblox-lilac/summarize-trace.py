#!/usr/bin/env python3
"""Summarise expected UI texture lookups without printing raw log contents."""
from collections import Counter
from pathlib import Path
import re
import sys

FAMILIES = ('LoadingSpinner', 'BackgroundGlow', 'CircleBackground',
            'SelectedGradient', 'gr-loading-indicator', 'FPSBackground', 'GridBackground',
            'img_set_1x_1', 'img_set_1x_2', 'img_set_1x_3', 'img_set_1x_4', 'img_set_1x_5')


def summarize(text, status):
    counts = {name: Counter() for name in FAMILIES}
    asset_lines = path_lines = 0
    pack_enabled = False
    for line in text.splitlines():
        if '[lilac-assets]' in line and ('Texture pack v2 enabled' in line or 'Original texture pack enabled' in line):
            pack_enabled = True
        if '[asset]' in line:
            asset_lines += 1
        if '[paths]' in line:
            path_lines += 1
        for name in FAMILIES:
            # Exact filename-family prefix rather than arbitrary user text.
            if not re.search(re.escape(name) + r'(?:[@_.]|\b)', line):
                continue
            if '[asset] hit (overlay):' in line:
                counts[name]['overlay'] += 1
            elif '[asset] hit (apk):' in line:
                counts[name]['apk'] += 1
            elif '[asset] miss:' in line:
                counts[name]['missing'] += 1
            elif '[paths]' in line:
                counts[name]['file'] += 1
    rows = ['Lilac Roblox texture trace summary', f'Runtime exit code: {status}',
            f'Pack launch confirmed: {"yes" if pack_enabled else "no"}',
            f'Asset trace lines: {asset_lines}', f'Filesystem trace lines: {path_lines}']
    for name in FAMILIES:
        c = counts[name]
        rows.append(f'{name}: overlay={c["overlay"]}, apk={c["apk"]}, missing={c["missing"]}, file_calls={c["file"]}')
    rows.append('Zero lookups do not prove an asset is unused if startup or tracing failed. File calls do not prove a successful read or visible rendering.')
    return '\n'.join(rows) + '\n'


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Usage: summarize-trace.py LOG EXIT_CODE')
    with Path(sys.argv[1]).open(errors='replace') as log:
        print(summarize(log.read(), sys.argv[2]), end='')
