# Lilac Roblox Home theme experiment

The `runtime-lilac-theme` branch now prepares a separate asset overlay when `runtime/run.sh` starts. It looks for the newest complete Roblox build in LilacRuntime's own build store, recolours supported PNGs in Roblox's UI texture directories, and writes the results to LilacRuntime's private configuration directory. Coverage includes the observed FoundationImages and LuaApp atlases below `ExtraContent` as well as `content/textures/ui/` and `content/textures/UniversalApp/`.

Blue accents become lilac, dark neutral pixels receive a subtle violet cast, and light text is left alone. Game thumbnails arrive over the network and are not recoloured. Experience/world textures, the APK, extracted Roblox assets and signed `UniversalApp.rbxm` bytecode are not modified.

This is deliberately an **experiment**, not a claim that every Home panel is themed. Roblox draws much of its interface from compiled UI code rather than PNG files. Only texture-backed elements can change through this route. Visual verification on Mint is still required.

## Run

The existing commands are unchanged:

```bash
git switch runtime-lilac-theme
git pull
bash runtime/prepare.sh
bash runtime/build.sh
bash runtime/run.sh
```

Close existing LilacRuntime windows first. The startup log reports how many UI textures were scanned and recoloured. If Roblox was not imported when the command ran, import it and restart; the next run will generate the overlay.

For an A/B comparison:

```bash
LILAC_HOME_THEME=off bash runtime/run.sh
```

That disables only the Roblox UI asset overlay. `LILAC_THEME=off` remains the separate switch for the GTK shell palette.

## Native Home investigation

Patches 0010 and 0011 add the read-only SystemTheme vocabulary and message-shape probes from the native UI research branch. They do not publish messages, change colours or bypass Roblox integrity checks. Payload logging is bounded and redacts unknown strings and fields.

After rebuilding, close existing runtime windows and run:

```bash
LILAC_PROBE_SYSTEM_THEME=1 CORDIAL_TRACE_ASSETS=1 bash runtime/run.sh 2>&1 | grep -E '^\[lilac-(home|system-theme)\]|^\[asset\] hit \(overlay\)'
```

Open Roblox Home and, if Appearance settings are available, switch between light and dark once. The filtered output distinguishes generated textures, actual overlay lookups and native theme messages. A generated file is not evidence that Home loaded it; an overlay lookup is still not evidence that a later shader preserves its colour.

## Shared slop-label roadmap

The native slop feature is not implemented yet. Its agreed behaviour is a label shared across all Roblox profiles, hiding the labelled experience from Home, search, Discover and every other game list, plus a dedicated hidden-games menu that can restore entries. The stable experience/universe ID should be stored rather than a mutable title or one place ID.

The control and hidden-games manager must live in Roblox's native UI, not only in the Electron or GTK launcher. Implementation therefore depends on identifying a supported native UI/message surface; the texture overlay alone cannot add buttons or filter compiled lists. Persistent storage should be atomic and shared beneath LilacRuntime's configuration root.

## Overlay precedence and updates

Patch 0009 registers the generated directory as the `lilac-home-theme` asset layer. The user's own Cordial overlay has higher priority, so custom replacements still win. Disabling the theme merely stops registering the layer; no cleanup or APK restoration is needed.

The generator keys its cache to the APK's size, modification time and palette version. A new Roblox build rebuilds the dedicated generated directory and removes stale generated files. It does not delete or overwrite a user-owned overlay.

Only non-interlaced eight-bit PNGs are currently decoded, including indexed colour. Unsupported PNG variants are skipped without preventing Roblox from starting.

## Local checks

```bash
python3 -m unittest discover -s runtime -p 'lilac_home_theme_test.py' -v
bash -n runtime/run.sh runtime/prepare.sh runtime/build.sh
```

These checks cover PNG decoding, transparency, palette conversion, UI-only path selection, cache invalidation and numeric Roblox build selection. They do not replace `cargo test --workspace`, a successful release build, or a visual Home/menu comparison on Mint.
