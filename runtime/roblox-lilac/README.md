# Roblox lilac asset experiment

This opt-in pack supplies original lilac textures through the runtime's existing asset overlay. It contains no Roblox artwork, scripts or binaries. The paths and dimensions match UI texture entries observed in the supplied Android APK.

## Run

Close Roblox and the runtime first. On the `roblox-lilac-assets` branch, with the current runtime already built, install the image-generation dependency once:

```bash
sudo apt install python3-pil
bash runtime/run-roblox-lilac.sh
```

No Rust rebuild is needed for this asset-only change. The helper generates the pack locally on first launch, checks its hashes on subsequent launches, and sets `CORDIAL_OVERLAY` for this launch. To return to the normal assets, close the runtime and start `bash runtime/run.sh`. APK files and Sober's installation are untouched. If you normally use another overlay, this launch selects this pack instead; it does not merge directories.

## What it changes when used by this Roblox build

- Loading spinner and small loading indicator textures.
- In-game menu glow textures.
- Radial emote menu background/selection textures.
- Packaged sign-in background textures.

Availability depends on the active client screen and resource path. A texture may be tinted or unused by the current app; a successful overlay lookup does not prove its appearance on screen. Roblox may fetch replacement resources that do not use these APK paths. In particular, do not sign out of an account just to test a background.

This is a partial cosmetic pack. It does **not** recolour Home's solid panels, text or buttons and does not add a slop button. Those remain part of the compiled app UI. It does not change experience geometry, avatars, gameplay assets, script code or integrity checks. Cinnamon window decorations are also outside this pack.

## Check actual use

For a short test, run:

```bash
(umask 077; CORDIAL_TRACE_ASSETS=1 bash runtime/run-roblox-lilac.sh 2> /tmp/lilac-assets-private.log)
```

Visit a game loading screen, the in-game Escape menu, and the emote menu if the game offers it. Then close the runtime. The normal terminal may already show the source's `[asset] hit (overlay)` lines; stderr alone may not contain them. Report which screens changed and attach screenshots. Keep full logs private. No client screenshots have been observed for this pack yet.

## Source

`generate.py` authors all shapes and colour gradients from scratch. Pillow generates the files locally (`python3-pil` on Mint). Generated images and their `manifest.json` live in `generated/`, which is excluded from Git. The manifest lists dimensions and hashes. Generated artwork and the generator are GPL-3.0-or-later, matching the runtime fork source. The pack is experimental and only tested offline for image format, dimensions, hashes and allowed paths.

## If no textures visibly change

The runtime does not always produce the expected end-of-run asset trace file. Use the dedicated capture instead:

```bash
bash runtime/trace-roblox-lilac.sh
```

It captures both stdout and stderr while enabling upstream asset and filesystem trace switches. Visit loading, Escape and emote screens, then close the game and runtime. It prints counts for the seven texture families, split between overlay hits, APK hits, misses and ordinary file calls. Share only that summary. The full log stays private under the Git-ignored `generated/trace.*` directory. No Rust rebuild is needed for the helper. No screen change is claimed until a client screenshot or actual lookup confirms it; file calls alone are not proof of successful loading.
